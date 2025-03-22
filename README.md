# Ozon Price API

Минимальная версия API для получения цен с Ozon. API позволяет отслеживать цены товаров и получать информацию о продавцах.

## Возможности

- Получение информации о товарах продавца
- Получение цен и скидок на товары
- Постраничная навигация по каталогу продавца
- Опциональное сохранение ответов API
- Управление настройками через API endpoints
- Авторизация через токены

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/YOUR_USERNAME/ozone-price-api-minimal.git
cd ozone-price-api-minimal
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv .venv
source .venv/bin/activate  # для Linux/Mac
# или
.venv\Scripts\activate  # для Windows
pip install -r app/requirements.txt
```

3. Создайте базу данных:
```bash
python app/init_db.py
```

4. Запустите приложение:
```bash
python app/main.py
```

По умолчанию API будет доступен по адресу: http://localhost:8000

## API Endpoints

### Настройки

- `GET /v1/settings` - Получение текущих настроек
- `POST /v1/settings` - Обновление настроек
- `POST /v1/settings/generate` - Генерация настроек из файла settings.json

### Товары

- `GET /v1/seller/products/page` - Получение страницы товаров продавца
- `GET /v1/product/{product_id}` - Получение информации о конкретном товаре

## Авторизация

Все запросы к API должны содержать токен авторизации в заголовке:
```
Authorization: Bearer YOUR_TOKEN
```

## Настройка

Основные настройки хранятся в базе данных и могут быть изменены через API endpoints. 
Начальные настройки можно загрузить из файла `settings.json`.

### Параметры настроек:

- `save_api_responses` - Сохранение ответов API (boolean)
- `headers` - Заголовки для запросов к Ozon (object)
- `cookies` - Cookies для запросов к Ozon (object)

## Разработка

### Структура проекта:
```
ozone-price-api-minimal/
├── .gitignore
├── README.md
├── settings.json
└── app/
    ├── Dockerfile
    ├── alembic.ini
    ├── database.py
    ├── init_db.py
    ├── main.py
    ├── models.py
    ├── parser.py
    ├── requirements.txt
    └── migrations/
        ├── env.py
        └── script.py.mako
```

### База данных

Проект использует SQLite для хранения данных. Файл базы данных: `api.db`

## Лицензия

MIT 