from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tokens = relationship("Token", back_populates="user")

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    user = relationship("User", back_populates="tokens")

class Price(BaseModel):
    original: float
    final: float
    discount: Optional[float] = None

class Product(BaseModel):
    id: str
    name: str
    url: str
    price: Price
    rating: Optional[float] = None
    reviews_count: Optional[int] = None

class Pagination(BaseModel):
    current_page: int
    total_pages: int
    items_per_page: int
    total_items: int

class PageResult(BaseModel):
    pagination: Pagination
    products: List[Product]
    metadata: Optional[Dict[str, Any]] = None

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    save_api_responses = Column(Boolean, default=False)
    headers = Column(JSON)
    cookies = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "save_api_responses": self.save_api_responses,
            "headers": self.headers,
            "cookies": self.cookies,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 