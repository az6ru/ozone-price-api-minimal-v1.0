from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Table, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Price(BaseModel):
    """Модель для представления цены"""
    original: float = 0.0  # Оригинальная цена
    discount: Optional[float] = None  # Скидка
    discount_percent: Optional[int] = None  # Скидка в процентах
    final: Optional[float] = None    # Текущая цена
    card_price: Optional[float] = None  # Цена по карте Ozon

class Product(BaseModel):
    name: str = Field(..., description="Наименование товара")
    category: Optional[str] = Field(None, description="Категория товара")
    price: Price = Field(..., description="Цены товара")
    seller_id: str = Field(..., description="ID продавца")
    quantity: Optional[int] = Field(None, description="Количество товара")
    rating: Optional[float] = Field(None, description="Рейтинг товара")
    reviews: Optional[int] = Field(None, description="Количество отзывов")
    images: List[str] = Field(default_factory=list, description="Список URL изображений")
    sku_id: str

class Pagination(BaseModel):
    current_page: int = Field(..., description="Текущая страница")
    total_pages: int = Field(..., description="Всего страниц")
    items_per_page: int = Field(..., description="Товаров на странице")
    total_items: int = Field(..., description="Всего товаров")

class PageResult(BaseModel):
    pagination: Pagination
    products: List[Product]
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительные метаданные"
    )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Отношения
    tokens = relationship("Token", back_populates="user")
    api_requests = relationship("ApiRequest", back_populates="user")

class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Внешний ключ
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="tokens")

class ApiRequest(Base):
    __tablename__ = "api_requests"

    id = Column(Integer, primary_key=True, index=True)
    method = Column(String)
    url = Column(String)
    status_code = Column(Integer)
    response_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Внешний ключ
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="api_requests")

class Characteristic(BaseModel):
    name: str
    value: str

class ProductDetails(BaseModel):
    """Расширенная модель продукта с детальной информацией"""
    id: str
    name: str
    brand: Optional[str]
    category: Optional[str]
    price: Price
    seller: Dict[str, Any]
    characteristics: List[Characteristic] = []
    description: Optional[str]
    images: List[str] = []
    rating: float = 0.0
    reviews_count: int = 0
    quantity: int = 0
    sku_id: Optional[str] = None
    parsed_at: datetime
    url: str 