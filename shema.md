# Схема извлечения данных из API Ozon

## Секция layoutTrackingInfo

- Ссылка на товар `currentPageUrl`
- Название категории `categoryName`
- Иерархия категорий `hierarchy` (используется для извлечения бренда - последний элемент)

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

## Секция widgetStates

### webGallery-3311626-default-1 (Изображения)

- Основное изображение: `coverImage`
- Дополнительные изображения: `images[].src`

```json
{
  "coverImage": "https://cdn1.ozone.ru/s3/multimedia-1-f/7343854647.jpg",
  "images": [
    {
      "src": "https://cdn1.ozone.ru/s3/multimedia-1-f/7343854647.jpg",
      "alt": "Название товара #1"
    }
  ]
}
```

### webReviewProductScore-3132021-default-1 (Отзывы)

- Рейтинг: `totalScore`
- Количество отзывов: `reviewsCount`

```json
{
  "totalScore": 5,
  "reviewsCount": 3
}
```

### webStickyProducts-726428-default-1 (Информация о продавце)

- Название продавца: `seller.name`
- Ссылка на продавца: `seller.link`
- Логотип продавца: `seller.logoImageUrl`

```json
{
  "seller": {
    "logoImageUrl": "https://cdn1.../image.jpg",
    "name": "магазин Александра Леонова",
    "link": "/seller/1179237/"
  }
}
```

### webPrice-3121879-default-1 (Цены)

- Цена по карте: `cardPrice`
- Текущая цена: `price`
- Оригинальная цена: `originalPrice`
- Флаг показа оригинальной цены: `showOriginalPrice`

```json
{
  "cardPrice": "5 100 ₽",
  "price": "5 433 ₽",
  "originalPrice": "8 900 ₽",
  "showOriginalPrice": true
}
```

### webDescription-*-pdpPage2column-2 (Описание)

Для получения описания требуется дополнительный запрос с параметрами:
- `layout_container`: "pdpPage2column"
- `layout_page_index`: 2

Описание может быть представлено в двух форматах:

1. Формат JSON (richAnnotationJson):
```json
{
  "richAnnotationJson": {
    "content": [
      {
        "blocks": [
          {
            "title": {
              "content": ["Заголовок блока"]
            },
            "text": {
              "content": ["Текст описания"]
            }
          }
        ]
      }
    ]
  }
}
```

Извлекаются:
- Заголовки из `blocks[].title.content[]`
- Текст описания из `blocks[].text.content[]`
- Дополнительные блоки текста из вложенных `content[]`

2. Формат HTML (richAnnotation):
```json
{
  "richAnnotation": "Ручной миксер.<br><br> 2 венчика для взбивания.<br> 2 крюка для замешивания теста.",
  "richAnnotationType": "HTML"
}
```

Извлекаются:
- Текст из поля `richAnnotation`
- HTML-теги `<br>` конвертируются в переносы строк
- Удаляются лишние пробелы и переносы строк

### webShortCharacteristics-*-default-1 (Характеристики)

Характеристики извлекаются из структуры:
```json
{
  "characteristics": [
    {
      "title": {
        "textRs": [
          {
            "type": "text",
            "content": "Название характеристики"
          }
        ]
      },
      "values": [
        {
          "text": "Значение характеристики"
        }
      ]
    }
  ]
}
```

## Порядок извлечения данных

1. Основной запрос для получения:
   - Основной информации о товаре
   - Цен
   - Характеристик
   - Изображений
   - Информации о продавце
   - Рейтинга и отзывов

2. Дополнительный запрос для получения:
   - Полного описания товара

3. Объединение данных в единую структуру ProductDetails
