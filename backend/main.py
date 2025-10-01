import os
from typing import Optional, List
import datetime

from beanie import PydanticObjectId, init_beanie
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import BeanieUserDatabase
from motor.motor_asyncio import AsyncIOMotorClient
import google.generativeai as genai
from pydantic import BaseModel, Field

from models import User, UserCreate, UserRead, UserUpdate

load_dotenv()
app = FastAPI()

origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("MONGO_URI")
SECRET = os.getenv("SECRET")

client = AsyncIOMotorClient(DATABASE_URL)
db = client["wisepal_db"]
conversation_collection = db.get_collection("conversations") 

@app.on_event("startup")
async def on_startup():
    await init_beanie(database=db, document_models=[User])

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    genai.configure(api_key=api_key)
    ai_model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Error during AI model initialization: {e}")
    ai_model = None

class UserManager(BaseUserManager[User, PydanticObjectId]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[dict] = None):
        print(f"User {user.id} has registered.")

    def parse_id(self, id: str) -> PydanticObjectId:
        return PydanticObjectId(id)

async def get_user_db():
    yield BeanieUserDatabase(User)

async def get_user_manager(user_db: BeanieUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, PydanticObjectId](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)

class ChatRequest(BaseModel):
    message: str

class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the WisePal API"}

@app.post("/chat")
async def chat(request: ChatRequest, user: User = Depends(current_active_user)):
    if not ai_model:
        raise HTTPException(status_code=500, detail="AI model is not available")
    try:
        user_message_content = request.message
        response = ai_model.generate_content(user_message_content)
        ai_reply_content = response.text

        user_message = Message(role="user", content=user_message_content)
        ai_message = Message(role="assistant", content=ai_reply_content)

        new_conversation = {
            "messages": [user_message.dict(), ai_message.dict()],
            "created_at": datetime.datetime.utcnow(),
            "user_id": user.id 
        }
        await conversation_collection.insert_one(new_conversation)
        return {"response": ai_reply_content}
    except Exception as e:
        print(f"An error occurred during chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat.")

@app.get("/conversations")
async def get_conversations(user: User = Depends(current_active_user)):
    """
    A PROTECTED endpoint to fetch all conversations for the logged-in user.
    """
    user_conversations = []
    cursor = conversation_collection.find({"user_id": user.id}).sort("created_at", 1)
    
    async for conversation in cursor:
        conversation["_id"] = str(conversation["_id"])
        conversation["user_id"] = str(conversation["user_id"])
        user_conversations.append(conversation)
        
    return user_conversations
