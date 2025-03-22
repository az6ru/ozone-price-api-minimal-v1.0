from fastapi import FastAPI, HTTPException, Query, Depends, Request, status, Security, Path, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
from parser import OzonParser
from models import PageResult, Product, Token, Settings
from database import get_db, Base, engine
import logging
import json
import os

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer()

app = FastAPI(
    title="Ozon Price API",
    description="""
    API для получения информации о товарах и ценах с Ozon.
    
    ## Авторизация
    
    Для использования API необходим токен доступа. Все запросы должны содержать заголовок:
    ```
    Authorization: Bearer YOUR_TOKEN
    ```
    
    ### Получение токена:
    1. Зарегистрируйтесь в системе через веб-интерфейс
    2. Создайте новый токен в разделе профиля
    3. Используйте полученный токен для запросов к API
    
    ### Важно:
    - Токены имеют срок действия 30 дней
    - После истечения срока токен нужно обновить
    - Неактивные токены автоматически деактивируются
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def verify_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> Optional[int]:
    """Проверка токена в заголовке запроса"""
    try:
        token = credentials.credentials
        db_token = db.query(Token).filter(
            Token.access_token == token,
            Token.is_active == True
        ).first()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Проверяем срок действия токена
        if db_token.expires_at and db_token.expires_at < datetime.utcnow():
            db_token.is_active = False
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Срок действия токена истек",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return db_token.user_id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка проверки токена",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get(
    "/v1/seller/products/page",
    response_model=PageResult,
    tags=["Products"],
    summary="Получение страницы товаров продавца",
    description="""
    Возвращает информацию о товарах продавца с указанной страницы.
    
    Каждая страница содержит до 100 товаров.
    
    Для больших каталогов рекомендуется использовать постраничное получение данных.
    """,
    responses={
        200: {
            "description": "Успешное получение данных",
            "content": {
                "application/json": {
                    "example": {
                        "pagination": {
                            "current_page": 1,
                            "total_pages": 5,
                            "items_per_page": 100,
                            "total_items": 423
                        },
                        "products": [
                            {
                                "name": "Название товара",
                                "price": {
                                    "original": 1000.0,
                                    "final": 800.0,
                                    "discount": 200.0
                                }
                            }
                        ]
                    }
                }
            }
        },
        401: {"description": "Ошибка авторизации"},
        404: {"description": "Продавец не найден"}
    }
)
async def get_products_page(
    seller_id: str = Query(..., description="ID продавца на Ozon"),
    page: int = Query(1, description="Номер страницы", ge=1),
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
) -> PageResult:
    try:
        parser = OzonParser(db)
        result = await parser.get_page(seller_id, page)
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Продавец не найден или страница недоступна"
            )
        return result
    except Exception as e:
        logger.error(f"Error getting products page: {e}")
        raise HTTPException(
            status_code=404,
            detail="Продавец не найден или страница недоступна"
        )

@app.get(
    "/v1/product/{product_id}",
    tags=["Products"],
    summary="Получение информации о товаре",
    description="Возвращает подробную информацию о конкретном товаре по его ID.",
    responses={
        200: {
            "description": "Успешное получение данных",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Название товара",
                        "price": {
                            "original": 1000.0,
                            "final": 800.0,
                            "discount": 200.0
                        },
                        "rating": 4.5,
                        "reviews": 100
                    }
                }
            }
        },
        401: {
            "description": "Ошибка авторизации",
            "content": {
                "application/json": {
                    "example": {"detail": "Недействительный токен"}
                }
            }
        },
        404: {
            "description": "Товар не найден",
            "content": {
                "application/json": {
                    "example": {"detail": "Товар не найден"}
                }
            }
        }
    }
)
async def get_product(
    product_id: int = Path(..., description="ID товара на Ozon"),
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        parser = OzonParser(db)
        product = await parser.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail="Товар не найден"
            )
        return product
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        raise HTTPException(
            status_code=404,
            detail="Товар не найден"
        )

@app.get(
    "/health",
    tags=["System"],
    summary="Проверка работоспособности",
    description="Проверяет доступность API и возвращает текущее время сервера.",
    responses={
        200: {
            "description": "API работает",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-03-25T12:00:00.000Z"
                    }
                }
            }
        }
    }
)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get(
    "/v1/settings",
    tags=["Settings"],
    summary="Получение текущих настроек",
    description="Возвращает текущие настройки API, включая параметры сохранения ответов API.",
    responses={
        200: {
            "description": "Успешное получение настроек",
            "content": {
                "application/json": {
                    "example": {
                        "save_api_responses": True,
                        "headers": {},
                        "cookies": {},
                        "created_at": "2024-03-22T12:00:00.000Z",
                        "updated_at": "2024-03-22T12:00:00.000Z"
                    }
                }
            }
        },
        401: {"description": "Ошибка авторизации"}
    }
)
async def get_settings(
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings(
            save_api_responses=False,
            headers={},
            cookies={}
        )
        db.add(settings)
        db.commit()
    
    return settings.to_dict()

@app.post(
    "/v1/settings",
    tags=["Settings"],
    summary="Обновление настроек",
    description="Обновляет настройки API, включая параметры сохранения ответов API.",
    responses={
        200: {
            "description": "Настройки успешно обновлены",
            "content": {
                "application/json": {
                    "example": {
                        "save_api_responses": True,
                        "headers": {},
                        "cookies": {},
                        "created_at": "2024-03-22T12:00:00.000Z",
                        "updated_at": "2024-03-22T12:00:00.000Z"
                    }
                }
            }
        },
        401: {"description": "Ошибка авторизации"}
    }
)
async def update_settings(
    settings_data: Dict[str, Any] = Body(...),
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
    
    if "save_api_responses" in settings_data:
        settings.save_api_responses = settings_data["save_api_responses"]
    if "headers" in settings_data:
        settings.headers = settings_data["headers"]
    if "cookies" in settings_data:
        settings.cookies = settings_data["cookies"]
    
    db.commit()
    return settings.to_dict()

@app.post(
    "/v1/settings/generate",
    tags=["Settings"],
    summary="Генерация настроек из файла",
    description="Генерирует настройки на основе существующего файла settings.json.",
    responses={
        200: {
            "description": "Настройки успешно сгенерированы",
            "content": {
                "application/json": {
                    "example": {
                        "save_api_responses": True,
                        "headers": {},
                        "cookies": {},
                        "created_at": "2024-03-22T12:00:00.000Z",
                        "updated_at": "2024-03-22T12:00:00.000Z"
                    }
                }
            }
        },
        401: {"description": "Ошибка авторизации"},
        404: {"description": "Файл settings.json не найден"}
    }
)
async def generate_settings(
    user_id: int = Depends(verify_token),
    db: Session = Depends(get_db)
):
    try:
        with open("settings.json", "r") as f:
            settings_data = json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Файл settings.json не найден"
        )
    
    settings = db.query(Settings).first()
    if not settings:
        settings = Settings()
        db.add(settings)
    
    settings.headers = settings_data.get("headers", {})
    settings.cookies = settings_data.get("cookies", {})
    settings.save_api_responses = True  # По умолчанию включаем сохранение ответов
    
    db.commit()
    return settings.to_dict()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 