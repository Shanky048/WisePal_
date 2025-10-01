from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column # <-- IMPORT THESE
from sqlalchemy import Integer # <-- IMPORT THIS

class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "user"

    # --- THIS IS THE FIX ---
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # -----------------------