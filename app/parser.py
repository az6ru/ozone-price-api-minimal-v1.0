import httpx
import json
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime
from models import Product, Price, Pagination, PageResult, ProductDetails, Characteristic
from pydantic import HttpUrl
import re
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import time
import html
import logging
import os

# Constants
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en;q=0.9,uk;q=0.8,de;q=0.7,fr;q=0.6',
    'cache-control': 'max-age=0',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version': '"134.0.6998.89"',
    'sec-ch-ua-full-version-list': '"Chromium";v="134.0.6998.89", "Not:A-Brand";v="24.0.0.0", "Google Chrome";v="134.0.6998.89"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"15.0.0"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'service-worker-navigation-preload': 'true',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
}

COOKIES = {
    '__Secure-user-id': '0',
    '__Secure-ab-group': '46',
    'xcid': 'e6e37dca5a2b366b573209ccb6555974',
    '__Secure-ext_xcid': 'e6e37dca5a2b366b573209ccb6555974',
    'is_cookies_accepted': '1',
    'guest': 'true',
    '__Secure-ETC': '9ba3482ba26027dfe6ee4f74183396e6'
}

# Настройка логгера
logger = logging.getLogger(__name__)
# Меняем уровень логирования на WARNING чтобы убрать избыточные сообщения
logging.basicConfig(level=logging.WARNING)

def load_settings(settings_file: str = "settings.json") -> dict:
    """Загружает настройки из JSON файла"""
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки настроек: {e}")
        return {}

class OzonParser:
    def __init__(self, seller_id: str = "520524"):
        self.seller_id = seller_id
        self.session = httpx.Client(
            headers=HEADERS,
            cookies=COOKIES,
            follow_redirects=True
        )
        self.logger = logging.getLogger(__name__)
        # Устанавливаем уровень логирования для логгера класса
        self.logger.setLevel(logging.WARNING)
        self.settings = load_settings()
        # Копируем заголовки из настроек
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'ru,en;q=0.9,uk;q=0.8,de;q=0.7,fr;q=0.6',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-full-version': '"134.0.6998.89"',
            'sec-ch-ua-full-version-list': '"Chromium";v="134.0.6998.89", "Not:A-Brand";v="24.0.0.0", "Google Chrome";v="134.0.6998.89"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"15.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'service-worker-navigation-preload': 'true',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
        # Обновляем заголовки из настроек если есть
        if 'headers' in self.settings:
            self.headers.update(self.settings['headers'])
        # Получаем куки из настроек
        self.cookies = self.settings.get('cookies', {})
        
    def _extract_seller_id(self, url: str) -> str:
        """Извлекает ID продавца из URL"""
        try:
            # Проверяем наличие miniapp параметра
            if 'miniapp=seller_' in url:
                # Извлекаем ID из параметра miniapp
                match = re.search(r'miniapp=seller_(\d+)', url)
                if match:
                    return match.group(1)
            
            # Если miniapp не найден, пробуем извлечь из пути URL
            # Удаляем GET параметры
            url = url.split('?')[0]
            # Удаляем trailing слэш если есть
            url = url.rstrip('/')
            # Разбиваем URL на части
            parts = url.split('/')
            # Ищем часть с seller
            for i, part in enumerate(parts):
                if 'seller' in part:
                    # Проверяем следующую часть после seller
                    if i + 1 < len(parts):
                        # Извлекаем ID из следующей части
                        next_part = parts[i + 1]
                        # Ищем числовой ID в конце строки
                        if match := re.search(r'-(\d+)(?:/|$)', next_part):
                            return match.group(1)
                        elif next_part.isdigit():
                            return next_part
            
            print("Не удалось извлечь ID продавца из URL")
            return ""
            
        except Exception as e:
            print(f"Ошибка при извлечении ID продавца: {e}")
            return ""

    def _extract_pagination_info(self, data: dict) -> Pagination:
        """Extract pagination information from API response."""
        try:
            # Получаем shared данные
            shared_str = data.get('shared', '{}')
            shared_data = json.loads(shared_str)
            
            # Извлекаем информацию о пагинации из catalog
            catalog = shared_data.get('catalog', {})
            total_found = catalog.get('totalFound', 0)
            total_pages = catalog.get('totalPages', 0)
            
            return Pagination(
                current_page=1,  # По умолчанию 1, так как не предоставляется в ответе
                total_pages=total_pages,
                items_per_page=12,  # Стандартное количество товаров на странице
                total_items=total_found
            )
        except Exception as e:
            print(f"Ошибка извлечения пагинации: {e}")
            return None

    def _extract_categories(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Извлекает информацию о категориях из filtersDesktop виджета"""
        categories = {}
        try:
            # Ищем виджет с фильтрами
            widget_states = data.get('widgetStates', {})
            filters_widget_key = next((key for key in widget_states.keys() 
                                    if 'filtersDesktop' in key), None)
            
            if not filters_widget_key:
                print("filtersDesktop widget not found")
                return {}
            
            # Парсим данные виджета
            filters_data = json.loads(widget_states[filters_widget_key])
            
            # Ищем секцию с фильтром категорий
            for section in filters_data.get('sections', []):
                for filter_data in section.get('filters', []):
                    if filter_data.get('type') == 'categoryFilter':
                        category_filter = filter_data.get('categoryFilter', {})
                        # Извлекаем категории
                        for category in category_filter.get('categories', []):
                            title = category.get('title', '')
                            url_value = category.get('urlValue', '')
                            level = category.get('level', 0)
                            
                            # Берем только категории нулевого уровня (основные)
                            if level == 0 and title:
                                categories[title] = {
                                    'url': url_value,
                                    'level': level
                                }
                        break  # Прерываем поиск после нахождения фильтра категорий
            
            if not categories:
                print("No categories found in filters")
                # Создаем дефолтную категорию
                categories["Все товары"] = {
                    'url': 'default',
                    'level': 0
                }
            
            return categories
        
        except Exception as e:
            print(f"Ошибка извлечения категорий: {e}")
            import traceback
            traceback.print_exc()
            return {"Все товары": {'url': 'default', 'level': 0}}

    def _extract_price_info(self, price_data: dict) -> Price:
        """Extract price information from product data."""
        try:
            if not price_data:
                return Price(original=0, final=0)

            # Получаем цены из priceV2
            prices = price_data.get('price', [])
            if not prices:
                return Price(original=0, final=0)

            # Функция для очистки цены
            def clean_price(price_text: str) -> float:
                return float(re.sub(r'[^\d.]', '', price_text.replace(',', '.')))

            # Получаем финальную цену
            final_price = clean_price(prices[0]['text']) if prices else 0

            # Получаем оригинальную цену
            original_price = clean_price(prices[1]['text']) if len(prices) > 1 else final_price

            # Вычисляем скидку
            discount = original_price - final_price if original_price > final_price else None

            return Price(
                original=original_price,
                final=final_price,
                discount=discount
            )
        except Exception as e:
            print(f"Ошибка извлечения цен: {e}")
            return Price(original=0, final=0)

    def _extract_product_info(self, item: dict) -> Product:
        """Extract product information from widget."""
        name = item.get('title', '')
        category = None
        
        # Try to get category from labelList
        label_list = item.get('labelList', [])
        if label_list:
            for label in label_list:
                if 'text' in label and 'category' in label.get('textColor', '').lower():
                    category = label['text']
                    break
        
        # If category not found in labelList, try to find in actions
        if not category and 'action' in item:
            action = item.get('action', {})
            if isinstance(action, dict) and 'link' in action:
                link = action['link']
                # Look for category in URL
                if '/category/' in link:
                    category_parts = link.split('/category/')
                    if len(category_parts) > 1:
                        category = category_parts[1].split('/')[0].replace('-', ' ').title()

        # Extract price info
        price_info = self._extract_price_info(item)
        
        # Create Price object
        price = Price(
            original=price_info.original,
            discount=price_info.discount,
            final=price_info.final
        )
        
        return Product(
            name=name,
            category=category,
            price=price,
            seller_id=self.seller_id,
            quantity=item.get('quantity', 0),
            rating=item.get('rating', 0),
            reviews=item.get('reviewCount', 0),
            images=item.get('images', [])
        )

    def _extract_products(self, data: Dict[str, Any], seller_id: str) -> List[Product]:
        """Извлекает список товаров из ответа API"""
        products = []
        try:
            # Получаем категории
            categories = self._extract_categories(data)
            
            # Ищем виджет с результатами поиска
            widget_states = data.get('widgetStates', {})
            widget_key = next((key for key in widget_states.keys() 
                            if 'searchResultsV2' in key), None)
                            
            if not widget_key:
                logger.error("searchResultsV2 widget not found")
                return []
                
            widget_data_raw = widget_states[widget_key]
            
            try:
                widget_data = json.loads(widget_data_raw)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse widget data: {e}")
                return []
            
            items = widget_data.get('items', [])
            
            # Обрабатываем каждый товар
            for item in items:
                try:
                    # Получаем основные данные товара из mainState
                    main_state = item.get('mainState', [])
                    title = None
                    price_data = None
                    rating = None
                    reviews = None
                    
                    for state in main_state:
                        if state.get('type') == 'atom' and state.get('id') == 'name':
                            title = state.get('atom', {}).get('textAtom', {}).get('text', '')
                        elif state.get('type') == 'atom' and state.get('id') == 'atom':
                            price_data = state.get('atom', {}).get('priceV2', {})
                        elif state.get('atom', {}).get('type') == 'labelList':
                            label_list = state.get('atom', {}).get('labelList', {}).get('items', [])
                            for label in label_list:
                                if label.get('icon', {}).get('image') == 'ic_s_star_filled_compact':
                                    rating = float(label.get('title', '0').strip())
                                elif label.get('icon', {}).get('image') == 'ic_s_dialog_filled_compact':
                                    reviews_text = label.get('title', '0')
                                    reviews = int(''.join(filter(str.isdigit, reviews_text)))
                    
                    # Получаем категорию из action и сопоставляем с извлеченными категориями
                    action = item.get('action', {})
                    category = None
                    if isinstance(action, dict) and 'link' in action:
                        link = action['link']
                        # Ищем соответствующую категорию по URL
                        for cat_name, cat_data in categories.items():
                            if cat_data['url'] in link:
                                category = cat_name
                                break
                    
                    # Если категория не найдена, используем "Все товары"
                    if not category:
                        category = "Все товары"
                    
                    # Получаем количество товара из multiButton
                    multi_button = item.get('multiButton', {})
                    ozon_button = multi_button.get('ozonButton', {})
                    button_data = ozon_button.get('addToCartButtonWithQuantity', {})
                    quantity = button_data.get('maxItems', 0)
                    
                    # Получаем изображения
                    tile_image = item.get('tileImage', {})
                    images = [img.get('image', {}).get('link') for img in tile_image.get('items', [])]
                    
                    # Получаем цены
                    price = self._extract_price_info(price_data)
                    
                    # Получаем skuId
                    sku_id = item.get('skuId', '')
                    
                    # Создаем объект Product
                    if title:  # Создаем продукт только если есть название
                        product = Product(
                            name=html.unescape(title),
                            category=category,
                            price=price,
                            seller_id=seller_id,
                            quantity=quantity,
                            rating=rating or 0.0,
                            reviews=reviews or 0,
                            images=images,
                            sku_id=sku_id
                        )
                        products.append(product)
                except Exception as e:
                    logger.error(f"Error processing item: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка извлечения списка товаров: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return products

    async def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Выполняет запрос к API"""
        try:
            # Создаем директорию для сохранения ответов
            api_responses_dir = Path("api_responses")
            api_responses_dir.mkdir(exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            # Используем синхронный клиент для лучшей совместимости
            with httpx.Client(
                cookies=self.cookies,
                headers=self.headers,
                follow_redirects=True,
                timeout=30.0
            ) as client:
                response = client.get(url, params=params)
                
                if response.status_code == 200:
                    if "application/json" in response.headers.get("Content-Type", "") or response.text.strip().startswith('{'):
                        try:
                            json_data = response.json()
                            
                            # Сохраняем JSON ответ
                            json_file = api_responses_dir / f"response_{timestamp}.json"
                            with open(json_file, "w", encoding="utf-8") as f:
                                json.dump(json_data, f, ensure_ascii=False, indent=2)
                            
                            return json_data
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка при разборе JSON: {e}")
                            # Сохраняем сырой ответ
                            raw_file = api_responses_dir / f"raw_response_{timestamp}.txt"
                            with open(raw_file, "w", encoding="utf-8") as f:
                                f.write(response.text)
                    else:
                        # Сохраняем HTML ответ
                        html_file = api_responses_dir / f"html_response_{timestamp}.html"
                        with open(html_file, "w", encoding="utf-8") as f:
                            f.write(response.text)
                else:
                    # Сохраняем ответ с ошибкой
                    error_file = api_responses_dir / f"error_{status_code}_{timestamp}.txt"
                    with open(error_file, "w", encoding="utf-8") as f:
                        f.write(response.text)
                
                return None
                
        except Exception as e:
            logger.error(f"Ошибка запроса: {e}")
            return None

    async def get_page(self, url_or_seller_id: str, page: int = 1) -> Optional[PageResult]:
        """Получает данные одной страницы"""
        # Проверяем, является ли входной параметр ID продавца
        if url_or_seller_id.isdigit():
            seller_id = url_or_seller_id
        else:
            seller_id = self._extract_seller_id(url_or_seller_id)
            
        if not seller_id:
            print("Не удалось получить ID продавца")
            return None

        # Используем прямой формат API URL
        api_url = "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"
        params = {
            "url": f"/seller/magazin-{seller_id}/products/",
            "layout_container": "categorySearchMegapagination",
            "layout_page_index": page,
            "page": page
        }

        data = await self._make_request(api_url, params)
        if not data:
            return None

        # Извлекаем информацию о пагинации
        pagination = self._extract_pagination_info(data)
        if not pagination:
            return None

        # Извлекаем список товаров
        products = self._extract_products(data, seller_id)

        return PageResult(
            pagination=pagination,
            products=products,
            metadata={
                "seller_id": seller_id,
                "parsed_at": datetime.now().isoformat(),
                "url": f"https://www.ozon.ru/seller/magazin-{seller_id}/products/"
            }
        )

    def save_page_result(self, result: PageResult, output_dir: str = "results") -> str:
        """Сохраняет результаты парсинга страницы в JSON файл"""
        try:
            # Создаем директорию если её нет
            os.makedirs(output_dir, exist_ok=True)
            
            # Формируем имя файла
            filename = f"{output_dir}/seller_{result.metadata['seller_id']}_page_{result.pagination.current_page}.json"
            
            # Преобразуем результат в словарь
            result_dict = result.model_dump(exclude_none=False)  # Включаем None значения
            
            # Сохраняем результат
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)
            
            return filename
        except Exception as e:
            print(f"Ошибка сохранения результатов: {e}")
            return ""

    async def get_all_pages(self, url_or_seller_id: str) -> List[PageResult]:
        """Получает все страницы с товарами продавца"""
        # Получаем первую страницу для определения общего количества страниц
        first_page = await self.get_page(url_or_seller_id, page=1)
        if not first_page:
            return []

        total_pages = first_page.pagination.total_pages
        results = [first_page]
        
        # Получаем остальные страницы
        for page in range(2, total_pages + 1):
            print(f"\rЗагрузка страницы {page} из {total_pages}...", end="")
            result = await self.get_page(url_or_seller_id, page=page)
            if result:
                results.append(result)
            # Добавляем небольшую задержку между запросами
            await asyncio.sleep(1)
        
        print("\nЗагрузка завершена!")
        return results

    def save_all_results(self, results: List[PageResult], output_dir: str = "results") -> str:
        """Сохраняет результаты парсинга всех страниц в один JSON файл"""
        try:
            # Создаем директорию если её нет
            os.makedirs(output_dir, exist_ok=True)
            
            # Собираем все товары в один список
            all_products = []
            total_items = 0
            seller_id = None
            
            for result in results:
                all_products.extend([product.model_dump() for product in result.products])
                total_items += len(result.products)
                if not seller_id:
                    seller_id = result.metadata['seller_id']
            
            # Формируем итоговый результат
            final_result = {
                "metadata": {
                    "seller_id": seller_id,
                    "parsed_at": datetime.now().isoformat(),
                    "total_pages": len(results),
                    "total_items": total_items
                },
                "products": all_products
            }
            
            # Формируем имя файла
            filename = f"{output_dir}/seller_{seller_id}_all_products.json"
            
            # Сохраняем результат
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, ensure_ascii=False, indent=2, default=str)
            
            return filename
        except Exception as e:
            print(f"Ошибка сохранения результатов: {e}")
            return ""

    def _extract_product_details(self, data: Dict[str, Any], product_id: str) -> Optional[ProductDetails]:
        """Извлекает детальную информацию о продукте из ответа API"""
        try:
            # Получаем schema.org разметку
            schema_data = None
            seo_data = data.get('seo', {})
            if isinstance(seo_data, str):
                try:
                    seo_data = json.loads(seo_data)
                except json.JSONDecodeError:
                    seo_data = {}
            
            for script in seo_data.get('script', []):
                if script.get('type') == 'application/ld+json':
                    try:
                        schema_data = json.loads(script.get('innerHTML', '{}'))
                        break
                    except json.JSONDecodeError:
                        continue

            # Получаем виджеты
            widget_states = data.get('widgetStates', {})
            
            # Ищем нужные виджеты по точным ключам
            gallery_widget = None
            price_widget = None
            reviews_widget = None
            seller_widget = None
            breadcrumbs_widget = None
            characteristics_widget = None
            short_characteristics_widget = None
            description_widget = None  # Добавляем переменную для виджета описания
            
            # Получаем виджет с ценой по точному ключу
            price_widget_key = 'webPrice-3121879-default-1'
            price_widget_data = widget_states.get(price_widget_key)
            
            if price_widget_data:
                try:
                    price_widget = json.loads(price_widget_data) if isinstance(price_widget_data, str) else price_widget_data
                except (json.JSONDecodeError, TypeError) as e:
                    self.logger.error(f"Ошибка парсинга виджета цены: {e}")
                    price_widget = None

            # Ищем остальные виджеты
            for key, value in widget_states.items():
                try:
                    if 'webGallery' in key:
                        gallery_widget = json.loads(value) if isinstance(value, str) else value
                    elif 'webReviewProductScore' in key:
                        reviews_widget = json.loads(value) if isinstance(value, str) else value
                    elif 'webStickyProducts' in key:
                        seller_widget = json.loads(value) if isinstance(value, str) else value
                    elif 'breadCrumbs' in key:
                        breadcrumbs_widget = json.loads(value) if isinstance(value, str) else value
                    elif 'webCharacteristics' in key:
                        characteristics_widget = json.loads(value) if isinstance(value, str) else value
                    elif 'webShortCharacteristics' in key:
                        short_characteristics_widget = json.loads(value) if isinstance(value, str) else value
                    elif 'webDescription' in key:
                        description_widget = json.loads(value) if isinstance(value, str) else value
                except (json.JSONDecodeError, TypeError) as e:
                    self.logger.error(f"Ошибка парсинга виджета {key}: {e}")
                    continue

            # Получаем базовую информацию из layoutTrackingInfo
            try:
                layout_info = json.loads(data.get('layoutTrackingInfo', '{}')) if isinstance(data.get('layoutTrackingInfo'), str) else data.get('layoutTrackingInfo', {})
            except json.JSONDecodeError:
                layout_info = {}
            
            category_name = layout_info.get('categoryName')
            
            # Извлекаем название и бренд
            name = ''
            description = ''
            brand = None

            # Получаем бренд из иерархии категорий
            hierarchy = layout_info.get('hierarchy', '')
            if hierarchy:
                brand = hierarchy.split('/')[-1]

            # Получаем название из webAspects
            aspects_widget_key = 'webAspects-3529295-default-1'
            aspects_data = widget_states.get(aspects_widget_key)
            
            product_name = ''
            
            if aspects_data:
                try:
                    aspects = json.loads(aspects_data) if isinstance(aspects_data, str) else aspects_data
                    
                    if aspects.get('aspects'):
                        variants = aspects['aspects'][0].get('variants', [])
                        for variant in variants:
                            if variant.get('active'):
                                product_name = variant.get('data', {}).get('title', '')
                                break
                
                except (json.JSONDecodeError, TypeError) as e:
                    self.logger.error(f"Ошибка парсинга webAspects: {e}")

            # Очищаем название от HTML-сущностей и лишних пробелов
            if product_name:
                product_name = html.unescape(product_name.strip())
                product_name = ' '.join(product_name.split())

            # Извлекаем цены
            price = Price(original=0.0, final=0.0, discount=None, card_price=None)
            
            # Пробуем получить цены из price_widget
            if price_widget:
                try:
                    def clean_price(price_str: str) -> float:
                        if not price_str:
                            return 0.0
                        cleaned = re.sub(r'[^\d.,]', '', str(price_str)).replace(',', '.').strip()
                        if cleaned.count('.') > 1:
                            parts = cleaned.split('.')
                            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
                        try:
                            return float(cleaned)
                        except ValueError as e:
                            self.logger.error(f"Ошибка конвертации цены {cleaned}: {e}")
                            return 0.0

                    if isinstance(price_widget, dict):
                        current_price = price_widget.get('price', '0')
                        price.final = clean_price(current_price)

                        original_price = price_widget.get('originalPrice', current_price)
                        price.original = clean_price(original_price)
                        
                        card_price = price_widget.get('cardPrice', '0')
                        price.card_price = clean_price(card_price)

                        if price.original == 0 and price.final > 0:
                            price.original = price.final

                        show_original_price = price_widget.get('showOriginalPrice', False)
                        if show_original_price and price.original > price.final:
                            price.discount = price.original - price.final
                            price.discount_percent = int(round((price.discount / price.original) * 100))

                except Exception as e:
                    self.logger.error(f"Ошибка при извлечении цен из price_widget: {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())

            # Извлекаем информацию о продавце
            seller_data = seller_widget.get('seller', {}) if seller_widget else {}
            seller = {
                'id': seller_data.get('link', '').split('/')[-2] if seller_data.get('link') else None,
                'name': seller_data.get('name'),
                'logo': seller_data.get('logoImageUrl'),
                'link': seller_data.get('link')
            }
            
            # Извлекаем изображения
            images = []
            if gallery_widget:
                cover_image = gallery_widget.get('coverImage')
                if cover_image:
                    images.append(cover_image)
                gallery_images = [img.get('src') for img in gallery_widget.get('images', [])]
                images.extend(gallery_images)
            
            # Если изображения не найдены в галерее, пробуем взять из schema.org
            if not images and schema_data:
                schema_images = schema_data.get('image')
                if isinstance(schema_images, str):
                    images.append(schema_images)
                elif isinstance(schema_images, list):
                    images.extend(schema_images)
            
            # Извлекаем рейтинг и отзывы
            rating = 0.0
            reviews_count = 0
            if reviews_widget:
                rating = float(reviews_widget.get('totalScore', 0))
                reviews_count = int(reviews_widget.get('reviewsCount', 0))
            elif schema_data and 'aggregateRating' in schema_data:
                agg_rating = schema_data['aggregateRating']
                if isinstance(agg_rating, dict):
                    rating = float(agg_rating.get('ratingValue', 0))
                    reviews_count = int(agg_rating.get('reviewCount', 0))
            
            # Извлекаем характеристики
            characteristics = []
            
            # Сначала пробуем извлечь из webShortCharacteristics
            if short_characteristics_widget:
                try:
                    # Проверяем новый формат характеристик
                    if isinstance(short_characteristics_widget, dict) and 'characteristics' in short_characteristics_widget:
                        for char in short_characteristics_widget['characteristics']:
                            # Получаем название характеристики
                            title_rs = char.get('title', {}).get('textRs', [])
                            name = ''
                            for text_block in title_rs:
                                if text_block.get('type') == 'text':
                                    name = text_block.get('content', '')
                                    break
                            
                            # Получаем значения характеристики
                            values = []
                            for value_obj in char.get('values', []):
                                if 'text' in value_obj:
                                    values.append(value_obj['text'])
                            
                            # Объединяем все значения в одну строку
                            value = ', '.join(str(v) for v in values if v)
                            
                            if name and value:
                                characteristics.append(Characteristic(name=name, value=value))
                    # Старый формат характеристик
                    else:
                        for char in short_characteristics_widget.get('characteristics', []):
                            name = char.get('name', '')
                            values = []
                            
                            # Собираем значения из разных возможных форматов
                            if 'value' in char:
                                values.append(str(char['value']))
                            elif 'values' in char:
                                if isinstance(char['values'], list):
                                    values.extend(str(v) for v in char['values'])
                                else:
                                    values.append(str(char['values']))
                            elif 'text' in char:
                                values.append(str(char['text']))
                            
                            # Если есть единицы измерения, добавляем их
                            if char.get('unit'):
                                values = [f"{v} {char['unit']}" for v in values]
                            
                            # Объединяем все значения в одну строку
                            value = ', '.join(str(v) for v in values if v)
                            
                            if name and value:
                                characteristics.append(Characteristic(name=name, value=value))
                except Exception as e:
                    self.logger.error(f"Ошибка при извлечении коротких характеристик: {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())
            
            # Если характеристики не найдены, пробуем извлечь из webCharacteristics
            if not characteristics and characteristics_widget:
                try:
                    for group in characteristics_widget.get('characteristics', []):
                        for char in group.get('short', []):
                            name = char.get('name', '')
                            value = char.get('value', '')
                            if name and value:
                                characteristics.append(Characteristic(name=name, value=str(value)))
                except Exception as e:
                    self.logger.error(f"Ошибка при извлечении полных характеристик: {e}")
            
            # Если характеристики все еще не найдены, пробуем извлечь из schema.org
            if not characteristics and schema_data:
                try:
                    for prop_name, prop_value in schema_data.items():
                        if prop_name.startswith('additional') and isinstance(prop_value, (str, int, float)):
                            characteristics.append(Characteristic(
                                name=prop_name.replace('additional', '').strip(),
                                value=str(prop_value)
                            ))
                except Exception as e:
                    self.logger.error(f"Ошибка при извлечении характеристик из schema.org: {e}")

            # Извлекаем описание товара
            description = ''
            # Ищем виджет с описанием
            widget_states = data.get('widgetStates', {})
            description_widget_key = next(
                (key for key in widget_states.keys() if 'webDescription' in key),
                None
            )
            
            if description_widget_key:
                try:
                    description_widget_data = widget_states[description_widget_key]
                    if isinstance(description_widget_data, str):
                        description_widget = json.loads(description_widget_data)
                    else:
                        description_widget = description_widget_data

                    if isinstance(description_widget, dict):
                        # Проверяем наличие richAnnotationJson
                        rich_annotation = description_widget.get('richAnnotationJson', {})
                        if rich_annotation:
                            text_blocks = []
                            
                            def extract_text_from_blocks(blocks):
                                for block in blocks:
                                    # Извлекаем текст из title
                                    if 'title' in block:
                                        title_content = block['title'].get('content', [])
                                        if isinstance(title_content, list):
                                            text_blocks.extend(title_content)
                                    
                                    # Извлекаем текст из text.content
                                    if 'text' in block:
                                        text_data = block['text']
                                        if isinstance(text_data, dict) and 'content' in text_data:
                                            content = text_data['content']
                                            if isinstance(content, list):
                                                text_blocks.extend(content)
                                        elif isinstance(text_data, list):
                                            text_blocks.extend(text_data)
                            
                            # Обрабатываем основной контент
                            for content_block in rich_annotation.get('content', []):
                                # Проверяем наличие blocks
                                if 'blocks' in content_block:
                                    extract_text_from_blocks(content_block['blocks'])
                                # Проверяем text и title напрямую
                                if 'text' in content_block:
                                    text_data = content_block['text']
                                    if isinstance(text_data, dict) and 'content' in text_data:
                                        text_blocks.extend(text_data['content'])
                                if 'title' in content_block:
                                    title_data = content_block['title']
                                    if isinstance(title_data, dict) and 'content' in title_data:
                                        text_blocks.extend(title_data['content'])
                            
                            # Фильтруем и объединяем текстовые блоки
                            text_blocks = [block for block in text_blocks if block and isinstance(block, str)]
                            description = '\n'.join(text_blocks)
                        
                        # Проверяем наличие HTML-формата описания
                        elif 'richAnnotation' in description_widget:
                            html_description = description_widget.get('richAnnotation', '')
                            if html_description:
                                # Заменяем HTML-теги на переносы строк
                                description = html_description.replace('<br>', '\n')
                                # Удаляем возможные оставшиеся HTML-теги
                                description = re.sub(r'<[^>]+>', '', description)
                        
                        # Если richAnnotationJson не найден, пробуем старый формат
                        else:
                            content = description_widget.get('content', [])
                            text_blocks = []
                            
                            def extract_text_from_content(content_items):
                                for item in content_items:
                                    if isinstance(item, dict):
                                        if 'text' in item:
                                            text_blocks.append(item['text'])
                                        if 'content' in item and isinstance(item['content'], list):
                                            extract_text_from_content(item['content'])
                                        if 'textRs' in item:
                                            for text_item in item['textRs']:
                                                if text_item.get('type') == 'text':
                                                    text_blocks.append(text_item.get('content', ''))
                            
                            extract_text_from_content(content)
                            description = '\n'.join(text_blocks)
                        
                        # Очищаем описание
                        description = html.unescape(description.strip())
                        description = ' '.join(description.split())

                except Exception as e:
                    self.logger.error(f"Ошибка при извлечении описания из виджета: {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())

            if not description:
                self.logger.warning("Описание товара не найдено")

            # Создаем и возвращаем объект ProductDetails
            product_details = ProductDetails(
                id=product_id,
                name=product_name,
                brand=brand,
                category=category_name,
                price=price,
                seller=seller,
                characteristics=characteristics,
                description=description,
                images=images,
                rating=rating,
                reviews_count=reviews_count,
                quantity=0,
                sku_id=product_id,
                parsed_at=datetime.now(),
                url=f"https://www.ozon.ru/product/{product_id}/"
            )
            
            self.logger.info(f"Создан объект ProductDetails с названием: {product_details.name}")
            return product_details

        except Exception as e:
            self.logger.error(f"Ошибка при извлечении деталей продукта: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    async def get_product(self, product_id: str) -> Optional[ProductDetails]:
        """Получает детальную информацию о конкретном продукте по его ID"""
        try:
            # Получаем основные данные
            data = await self._make_request(
                "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2",
                {"url": f"/product/{product_id}"}
            )
            
            if not data:
                self.logger.error(f"Не удалось получить данные о продукте {product_id}")
                return None
            
            # Получаем дополнительные данные с описанием
            description_data = await self._make_request(
                "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2",
                {
                    "url": f"/product/{product_id}",
                    "layout_container": "pdpPage2column",
                    "layout_page_index": 2
                }
            )
            
            # Объединяем данные
            if description_data:
                # Добавляем виджеты из description_data в основные данные
                main_widget_states = data.get('widgetStates', {})
                desc_widget_states = description_data.get('widgetStates', {})
                
                # Находим ключ виджета с описанием
                description_widget_key = next(
                    (key for key in desc_widget_states.keys() if 'webDescription' in key),
                    None
                )
                
                if description_widget_key:
                    main_widget_states[description_widget_key] = desc_widget_states[description_widget_key]
                    data['widgetStates'] = main_widget_states
            
            # Извлекаем детальную информацию
            product_details = self._extract_product_details(data, product_id)
            if not product_details:
                self.logger.error(f"Не удалось извлечь информацию о продукте {product_id}")
                return None
            
            return product_details
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации о продукте {product_id}: {e}")
            return None

async def main():
    """Пример использования парсера"""
    print("\nВыберите режим работы:")
    print("1. Парсинг магазина продавца")
    print("2. Парсинг отдельного товара")
    
    mode = input("\nВведите номер режима (1 или 2): ").strip()
    
    try:
        # Создаем парсер
        parser = OzonParser()
        
        if mode == "1":
            print("\nВведите ID продавца или полную ссылку на магазин.")
            print("Примеры:")
            print("1. ID продавца: 1179237")
            print("2. Ссылка: https://www.ozon.ru/seller/magazin-name-1179237/products/")
            print("Добавьте флаг -all для загрузки всех страниц")
            
            user_input = input("\nВведите ID или ссылку: ").strip()
            
            # Проверяем наличие флага -all
            collect_all = False
            if user_input.endswith("-all"):
                collect_all = True
                user_input = user_input.replace("-all", "").strip()
            
            print("\nЗагрузка данных...")
            
            if collect_all:
                # Получаем все страницы
                results = await parser.get_all_pages(user_input)
                if results:
                    # Сохраняем все результаты в один файл
                    filename = parser.save_all_results(results)
                    total_items = sum(len(result.products) for result in results)
                    print(f"\nИнформация о продавце:")
                    print(f"ID продавца: {results[0].metadata['seller_id']}")
                    print(f"Всего товаров: {total_items}")
                    print(f"Всего страниц: {len(results)}")
                    print(f"\nРезультаты сохранены в файл: {filename}")
            else:
                # Получаем только первую страницу
                result = await parser.get_page(user_input, page=1)
                if result:
                    # Сохраняем результат
                    filename = parser.save_page_result(result)
                    print(f"\nИнформация о продавце:")
                    print(f"ID продавца: {result.metadata['seller_id']}")
                    print(f"Всего товаров: {result.pagination.total_items}")
                    print(f"Всего страниц: {result.pagination.total_pages}")
                    print(f"Товаров на странице: {len(result.products)}")
                    print(f"\nРезультаты сохранены в файл: {filename}")
        
        elif mode == "2":
            print("\nВведите ID товара или полную ссылку на товар.")
            print("Примеры:")
            print("1. ID товара: 1849590918")
            print("2. Ссылка: https://www.ozon.ru/product/1849590918")
            
            user_input = input("\nВведите ID или ссылку: ").strip()
            
            # Извлекаем ID товара из ссылки если нужно
            if "ozon.ru" in user_input:
                product_id = user_input.split("/")[-1].split("?")[0]
            else:
                product_id = user_input
            
            print("\nЗагрузка данных о товаре...")
            
            # Получаем информацию о товаре
            product = await parser.get_product(product_id)
            if product:
                # Сохраняем результат
                output_dir = "results"
                os.makedirs(output_dir, exist_ok=True)
                filename = f"{output_dir}/product_{product_id}.json"
                
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(product.model_dump(), f, ensure_ascii=False, indent=2, default=str)
                
                print(f"\nИнформация о товаре:")
                print(f"Название: {product.name}")
                print(f"Бренд: {product.brand}")
                print(f"Категория: {product.category}")
                print(f"Цена: {product.price.final} ₽")
                if product.price.discount:
                    print(f"Скидка: {product.price.discount} ₽")
                print(f"Продавец: {product.seller['name']}")
                print(f"Рейтинг: {product.rating}")
                print(f"Количество отзывов: {product.reviews_count}")
                print(f"\nРезультаты сохранены в файл: {filename}")
        
        else:
            print("\nНеверный режим работы. Пожалуйста, выберите 1 или 2.")
            
    except Exception as e:
        print(f"\nПроизошла ошибка при обработке запроса: {e}")

if __name__ == "__main__":
    asyncio.run(main())
