# API Документация: Ozon Seller API

## Общая информация
API предоставляет доступ к данным о товарах и продавцах на платформе Ozon. API построено на основе парсера и позволяет получать информацию о товарах продавца и детальную информацию о конкретных товарах.

**Базовый URL:** `https://api.example.com/v1`

## Аутентификация
Для доступа к API используется API ключ, который необходимо передавать в заголовке запроса:
```
X-API-Key: your_api_key_here
```

## Эндпоинты

### 1. Получение списка товаров продавца

#### Запрос
```http
GET /sellers/{seller_id}/products
```

#### Параметры пути
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|-----------|
| seller_id | string | Да | ID продавца на Ozon |

#### Параметры запроса
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|-----------|
| page | integer | 1 | Номер страницы |
| page_size | integer | 12 | Количество товаров на странице (макс. 100) |

#### Пример ответа
```json
{
  "pagination": {
    "current_page": 1,
    "total_pages": 10,
    "items_per_page": 12,
    "total_items": 120
  },
  "products": [
    {
      "name": "Название товара",
      "category": "Категория",
      "price": {
        "original": 8900.0,
        "final": 5433.0,
        "discount": 3467.0,
        "card_price": 5100.0,
        "discount_percent": 39
      },
      "seller_id": "1179237",
      "quantity": 10,
      "rating": 4.8,
      "reviews": 150,
      "images": [
        "https://cdn1.ozone.ru/s3/multimedia-1/image.jpg"
      ],
      "sku_id": "123456789"
    }
  ],
  "metadata": {
    "seller_id": "1179237",
    "parsed_at": "2024-03-23T15:30:00Z",
    "url": "https://www.ozon.ru/seller/magazin-1179237/products/"
  }
}
```

### 2. Получение информации о товаре

#### Запрос
```http
GET /products/{product_id}
```

#### Параметры пути
| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|-----------|
| product_id | string | Да | ID товара на Ozon |

#### Параметры запроса
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|-----------|
| include_description | boolean | false | Включить полное описание товара |

#### Пример ответа
```json
{
  "name": "Название товара",
  "brand": "Бренд",
  "category": "Категория",
  "price": {
    "original": 8900.0,
    "final": 5433.0,
    "discount": 3467.0,
    "card_price": 5100.0,
    "discount_percent": 39
  },
  "seller": {
    "id": "1179237",
    "name": "Магазин продавца",
    "logo": "https://cdn1.ozone.ru/s3/seller-logo/image.jpg",
    "link": "/seller/1179237/"
  },
  "characteristics": [
    {
      "name": "Объем",
      "value": "100 мл"
    }
  ],
  "description": "Подробное описание товара...",
  "quantity": 10,
  "rating": 4.8,
  "reviews_count": 150,
  "images": [
    "https://cdn1.ozone.ru/s3/multimedia-1/image.jpg"
  ],
  "sku_id": "123456789",
  "parsed_at": "2024-03-23T15:30:00Z",
  "url": "https://www.ozon.ru/product/123456789/"
}
```

## Коды ответов

| Код | Описание |
|-----|-----------|
| 200 | Успешный запрос |
| 400 | Неверный запрос |
| 401 | Не авторизован |
| 403 | Доступ запрещен |
| 404 | Ресурс не найден |
| 429 | Слишком много запросов |
| 500 | Внутренняя ошибка сервера |

## Ограничения
1. Максимальное количество товаров на странице: 100
2. Ограничение на количество запросов: 100 запросов в минуту
3. Кеширование результатов: 5 минут

## Модели данных

### Price (Цена)
```typescript
{
  original: number;       // Оригинальная цена
  final: number;         // Финальная цена
  discount?: number;     // Размер скидки
  card_price?: number;   // Цена по карте
  discount_percent?: number; // Процент скидки
}
```

### Characteristic (Характеристика)
```typescript
{
  name: string;    // Название характеристики
  value: string;   // Значение характеристики
}
```

### Seller (Продавец)
```typescript
{
  id: string;      // ID продавца
  name: string;    // Название магазина
  logo?: string;   // URL логотипа
  link: string;    // Ссылка на магазин
}
```

### Pagination (Пагинация)
```typescript
{
  current_page: number;    // Текущая страница
  total_pages: number;     // Всего страниц
  items_per_page: number;  // Элементов на странице
  total_items: number;     // Всего элементов
}
```

## Обработка ошибок

API возвращает ошибки в следующем формате:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Описание ошибки",
    "details": {
      "field": "Дополнительная информация об ошибке"
    }
  }
}
```

### Типовые коды ошибок

| Код ошибки | Описание |
|------------|----------|
| INVALID_SELLER_ID | Неверный ID продавца |
| INVALID_PRODUCT_ID | Неверный ID товара |
| RATE_LIMIT_EXCEEDED | Превышен лимит запросов |
| SELLER_NOT_FOUND | Продавец не найден |
| PRODUCT_NOT_FOUND | Товар не найден |
| PARSING_ERROR | Ошибка парсинга данных |
| INTERNAL_ERROR | Внутренняя ошибка сервера |

## Примеры использования

### cURL

1. Получение списка товаров продавца:
```bash
curl -X GET "https://api.example.com/v1/sellers/1179237/products?page=1&page_size=12" \
     -H "X-API-Key: your_api_key_here"
```

2. Получение информации о товаре:
```bash
curl -X GET "https://api.example.com/v1/products/123456789?include_description=true" \
     -H "X-API-Key: your_api_key_here"
```

### Python

```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "https://api.example.com/v1"

# Получение списка товаров продавца
def get_seller_products(seller_id: str, page: int = 1, page_size: int = 12):
    response = requests.get(
        f"{BASE_URL}/sellers/{seller_id}/products",
        params={"page": page, "page_size": page_size},
        headers={"X-API-Key": API_KEY}
    )
    return response.json()

# Получение информации о товаре
def get_product_details(product_id: str, include_description: bool = False):
    response = requests.get(
        f"{BASE_URL}/products/{product_id}",
        params={"include_description": include_description},
        headers={"X-API-Key": API_KEY}
    )
    return response.json()
``` 