from database import Base, engine, get_db
from models import User, Token
from datetime import datetime, timedelta
import secrets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Инициализация базы данных и создание администратора"""
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("Таблицы базы данных созданы")

        # Создаем сессию
        db = next(get_db())

        # Проверяем, существует ли уже администратор
        admin = db.query(User).filter(User.is_admin == True).first()
        if not admin:
            # Создаем администратора
            admin = User(
                username="admin",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKXcQ3kqGJH8gWi",  # пароль: admin
                is_active=True,
                is_admin=True,
                created_at=datetime.utcnow()
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            logger.info("Администратор создан")

            # Создаем токен для администратора
            token = Token(
                access_token=secrets.token_urlsafe(32),
                user_id=admin.id,
                is_active=True,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.add(token)
            db.commit()
            logger.info(f"Токен администратора создан: {token.access_token}")
        else:
            logger.info("Администратор уже существует")

    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise

if __name__ == "__main__":
    init_db() 