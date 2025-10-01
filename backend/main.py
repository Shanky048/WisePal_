# In backend/main.py

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from pydantic import BaseModel

# Import new SQLAlchemy components
from fastapi_users import FastAPIUsers, schemas  # <--- 1. ADD `schemas` HERE
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from sqlalchemy import create_engine
from db import get_user_db, engine
from models import User, Base

# --- Application Setup ---
load_dotenv()
app = FastAPI()

# --- CORS Configuration ---
origins = [
    "http://localhost:3000",
    "https://wise-pal-shanky048.vercel.app"  
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

# --- AI Model Configuration ---
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KxEY not found in .env file")
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

fastapi_users = FastAPIUsers[User, int](
    get_user_db,
    [auth_backend],
)

current_active_user = fastapi_users.current_user(active=True)

# --- Pydantic Models for API ---
# --- 2. THIS IS THE FIX ---
class UserRead(schemas.BaseUser[int]):
    pass

class UserCreate(schemas.BaseUserCreate):
    pass
# -------------------------

class ChatRequest(BaseModel):
    message: str

# --- API Routers ---
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])


# --- Table Creation and Main Endpoints ---
@app.on_event("startup")
async def on_startup():
    # This will create the database tables for our models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
        
        # We will add saving chat history to SQL in the next step.
        
        return {"response": ai_reply_content}
    except Exception as e:
        print(f"An error occurred during chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {e}")