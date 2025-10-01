import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from pydantic import BaseModel

# Import new SQLAlchemy components
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from sqlalchemy import create_engine
from db import get_user_db
from models import User, Base

# --- Application Setup ---
load_dotenv()
app = FastAPI()

# --- CORS Configuration ---
origins = [
    "http://localhost:3000",
    "https://wise-pal-shanky048.vercel.app" # Make sure this is your Vercel URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database and User Model Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET = os.getenv("SECRET")

# This is a synchronous operation that creates the 'user' table if it doesn't exist
# It's okay to do this once on startup
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)


# --- AI Model Configuration ---
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    genai.configure(api_key=api_key)
    ai_model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    print(f"Error during AI model initialization: {e}")
    ai_model = None

# --- Authentication Logic ---
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# We now use an integer for the user ID with SQLAlchemy
fastapi_users = FastAPIUsers[User, int](
    get_user_db,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)

# --- Pydantic Models for API ---
class UserRead(fastapi_users.schemas.BaseUser[int]):
    pass

class UserCreate(fastapi_users.schemas.BaseUserCreate):
    pass

class ChatRequest(BaseModel):
    message: str

# --- API Routers ---
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])

# --- Main Application Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the WisePal API with PostgreSQL!"}

@app.post("/chat")
async def chat(request: ChatRequest, user: User = Depends(current_active_user)):
    if not ai_model:
        raise HTTPException(status_code=500, detail="AI model is not available")
    
    try:
        user_message_content = request.message
        response = ai_model.generate_content(user_message_content)
        ai_reply_content = response.text
        
        # NOTE: We will add saving chat history to SQL in the next step.
        # For now, let's just make sure the chat works.
        
        return {"response": ai_reply_content}
    except Exception as e:
        print(f"An error occurred during chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {e}")