# Структура ответа API Ozon для товара

## Общая информация

API endpoint: `https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url=/product/{product_id}`

Ответ API содержит несколько основных секций с данными о товаре. Основная информация находится в `widgetStates`, где каждый виджет имеет свой уникальный идентификатор.

## Основные секции данных

### 1. layoutTrackingInfo
Содержит базовую информацию о товаре и его категории:
```json
{
    "layoutId": 11852,
    "layoutVersion": 1127,
    "pageType": "pdp",
    "ruleId": 2149,
    "categoryId": 6562,
    "categoryName": "Кремы",
    "currentPageUrl": "https://www.ozon.ru/product/bio-matritsa-garyaeva-kik-3-krem-s-maklyuroy-i-kedrovoy-zhivitsey-1849590918/",
    "deviceType": "desktop",
    "hierarchy": "Красота и здоровье/Уход за лицом/Увлажнение и питание/Кремы/Александр Леонов",
    "platform": "site",
    "templateType": "desktop",
    "sku": 1849590918,
    "marketplaceId": 1,
    "requestId": "218902f24fb79d41d6786768f09aef91"
}
```

### 2. Виджеты (widgetStates)

#### webGallery-3311626-default-1
Содержит информацию об изображениях товара:
```json
{
    "sku": "1849590918",
    "coverImage": "https://cdn1.ozone.ru/s3/multimedia-1-f/7343854647.jpg",
    "images": [
        {
            "src": "https://cdn1.ozone.ru/s3/multimedia-1-f/7343854647.jpg",
            "alt": "Био Матрица Гаряева КИК-3 Крем с маклюрой и кедровой живицей  #1"
        }
    ]
}
```

#### webReviewProductScore-3132021-default-1
Информация о рейтинге и отзывах:
```json
{
    "score": null,
    "reviewsCount": 3,
    "itemId": 1849590918,
    "totalScore": 5,
    "isHidden": false,
    "url": "/product/bio-matritsa-garyaeva-kik-3-krem-s-maklyuroy-i-kedrovoy-zhivitsey-1849590918/reviews/"
}
```

#### webStickyProducts-726428-default-1
Информация о продавце:
```json
{
    "sku": "1849590918",
    "name": "Био Матрица Гаряева КИК-3 Крем с маклюрой и кедровой живицей",
    "coverImageUrl": "https://cdn1.ozone.ru/s3/multimedia-1-f/c50/7343854647.jpg",
    "seller": {
        "logoImageUrl": "https://cdn1.ozonusercontent.com/s3/marketing-api/banners/M4/Rk/M4RkQpYOcQB2y0PyTU5qimJWKM0xBumN.jpg",
        "name": "магазин Александра Леонова",
        "link": "/seller/1179237/",
        "subtitle": "Перейти в магазин"
    }
}
```

#### breadCrumbs-3385917-default-1
Навигационная цепочка категорий:
```json
{
    "breadcrumbs": [
        {
            "text": "Красота и здоровье",
            "link": "/category/krasota-i-zdorove-6500/",
            "crumbType": "CRUMB_TYPE_NORMAL"
        }
    ],
    "connectSymbol": ">",
    "isFull": true
}
```

#### webPrice-3121879-default-1
Информация о ценах и скидках:
```json
{
    "isAvailable": true,
    "cardPrice": "5 100 ₽",        // Цена по карте Ozon
    "price": "5 433 ₽",           // Текущая цена
    "originalPrice": "8 900 ₽",    // Оригинальная цена
    "showOriginalPrice": true,     // Показывать ли оригинальную цену
    "link": "/modal/withoutOzonAccount",
    "lexemes": {
        "currency": "Валюта",
        "includeVatTextMobile": "Цена с НДС",
        "withOzonCard": "c Ozon Картой",
        "withoutOzonCard": "без Ozon Карты",
        "withoutVatText": "без НДС"
    }
}
```

#### webShortCharacteristics-3385952-default-1
Краткие характеристики товара:
```json
{
    "limit": 5,
    "showLongCharacteristics": true,
    "thresholdLength": 60,
    "paramsLinkTarget": "self",
    "isFreshColorsEnabled": true,
    "offsetScrol": 144,
    "linkToDescription": "section-description",
    "linkToDescriptionButtonText": "Перейти к описанию",
    "linkToCharacteristics": "section-characteristics",
    "linkToCharacteristicsButtonText": "Перейти к характеристикам"
}
```

## Таблица извлекаемых данных

| Поле | Источник (точный ID виджета) | Путь в JSON | Пример значения |
|------|----------|-------------|-----------------|
| ID товара | layoutTrackingInfo | sku | 1849590918 |
| Название | webStickyProducts-726428-default-1 | name | "Био Матрица Гаряева КИК-3 Крем..." |
| Категория | layoutTrackingInfo | categoryName | "Кремы" |
| Иерархия категорий | layoutTrackingInfo | hierarchy | "Красота и здоровье/Уход за лицом..." |
| Текущая цена | webPrice-3121879-default-1 | price | "5 433 ₽" |
| Оригинальная цена | webPrice-3121879-default-1 | originalPrice | "8 900 ₽" |
| Цена по карте | webPrice-3121879-default-1 | cardPrice | "5 100 ₽" |
| Скидка в рублях | Вычисляемое | originalPrice - price | 3467 ₽ |
| Скидка в процентах | Вычисляемое | (originalPrice - price) / originalPrice * 100 | 39% |
| Показывать скидку | webPrice-3121879-default-1 | showOriginalPrice | true |
| Рейтинг | webReviewProductScore-3132021-default-1 | totalScore | 5 |
| Количество отзывов | webReviewProductScore-3132021-default-1 | reviewsCount | 3 |
| Продавец | webStickyProducts-726428-default-1 | seller.name | "магазин Александра Леонова" |
| ID продавца | webStickyProducts-726428-default-1 | seller.link | "/seller/1179237/" |
| Основное изображение | webGallery-3311626-default-1 | coverImage | "https://cdn1.ozone.ru/..." |
| Галерея изображений | webGallery-3311626-default-1 | images[].src | ["https://cdn1.ozone.ru/...", ...] |
| Доступность | webPrice-3121879-default-1 | isAvailable | true |
| Характеристики | webShortCharacteristics-3385952-default-1 | characteristics | [...] |

## Особенности извлечения данных

1. **Точные ID виджетов**: 
   - Каждый виджет имеет уникальный идентификатор в формате `{название}-{id}-default-1`
   - Необходимо использовать точные ключи для каждого виджета
   - ID виджетов фиксированные и не меняются между запросами

2. **Форматирование цен**: 
   - Цены приходят в формате строки с пробелами и символом валюты ("5 433 ₽")
   - Необходимо удалить символ валюты и пробелы
   - Заменить запятые на точки для десятичных чисел
   - Преобразовать в числовой формат

3. **Вычисление скидок**:
   - Проверить флаг `showOriginalPrice` перед вычислением
   - Абсолютная скидка = originalPrice - price
   - Процентная скидка = (originalPrice - price) / originalPrice * 100
   - Округлить процентную скидку до целого числа

4. **Вложенность данных**: 
   - Данные находятся в строго определенных виджетах
   - Каждый виджет отвечает за свой блок информации
   - Необходимо использовать точные пути для извлечения данных

5. **Опциональные поля**: 
   - Некоторые поля могут отсутствовать даже в правильном виджете
   - Необходимо предусмотреть значения по умолчанию
   - Проверять наличие полей перед извлечением

## Рекомендации по парсингу

1. Всегда использовать точные ключи виджетов
2. Реализовать безопасное извлечение данных с проверкой наличия полей
3. Очищать и форматировать извлеченные данные (цены, ID и т.д.)
4. Сохранять сырой ответ API для отладки
5. Логировать ошибки при извлечении данных
6. Проверять флаг showOriginalPrice перед вычислением скидок
7. Корректно форматировать цены и скидки для отображения
8. Использовать альтернативные источники данных (например, schema.org) при отсутствии основных
9. Реализовать обработку ошибок и отсутствующих данных
10. Добавить систему логирования для отслеживания процесса парсинга 