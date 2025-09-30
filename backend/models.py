from beanie import Document, PydanticObjectId
from fastapi_users.db import BeanieBaseUser, BeanieUserDatabase
from pydantic import Field

class User(BeanieBaseUser, Document):
    pass

from fastapi_users import schemas

class UserRead(schemas.BaseUser[PydanticObjectId]):
    pass

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass