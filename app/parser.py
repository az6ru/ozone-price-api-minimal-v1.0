import httpx
import json
from typing import Optional, Dict, Any, List
import asyncio
from datetime import datetime
from models import Product, Price, PageResult, Pagination
import re
import logging
from pathlib import Path
import time
import html
import os
import aiohttp
from sqlalchemy.orm import Session
from models import Settings

# Настройка логгера
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

def load_settings(settings_file: str = "settings.json") -> dict:
    """Загружает настройки из JSON файла"""
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки настроек: {e}")
        return {}

class OzonParser:
    def __init__(self, db: Session):
        self.db = db
        self._load_settings()

    def _load_settings(self):
        settings = self.db.query(Settings).first()
        if not settings:
            settings = Settings(
                save_api_responses=False,
                headers={},
                cookies={}
            )
            self.db.add(settings)
            self.db.commit()
        
        self.save_api_responses = settings.save_api_responses
        self.headers = settings.headers
        self.cookies = settings.cookies

    def _save_api_response(self, url: str, response_data: dict):
        if not self.save_api_responses:
            return
            
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"api_responses/{timestamp}_{hash(url)}.json"
        
        os.makedirs("api_responses", exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(response_data, f, ensure_ascii=False, indent=2)

    def _extract_pagination_info(self, data: dict) -> Pagination:
        """Extract pagination information from API response."""
        try:
            shared_str = data.get('shared', '{}')
            shared_data = json.loads(shared_str)
            
            catalog = shared_data.get('catalog', {})
            total_found = catalog.get('totalFound', 0)
            total_pages = catalog.get('totalPages', 0)
            
            return Pagination(
                current_page=1,
                total_pages=total_pages,
                items_per_page=12,
                total_items=total_found
            )
        except Exception as e:
            logger.error(f"Ошибка извлечения пагинации: {e}")
            return None

    def _extract_price_info(self, price_data: dict) -> Price:
        """Extract price information from product data."""
        try:
            if not price_data:
                return Price(original=0, final=0)

            prices = price_data.get('price', [])
            if not prices:
                return Price(original=0, final=0)

            def clean_price(price_text: str) -> float:
                return float(re.sub(r'[^\d.]', '', price_text.replace(',', '.')))

            final_price = clean_price(prices[0]['text']) if prices else 0
            original_price = clean_price(prices[1]['text']) if len(prices) > 1 else final_price
            discount = original_price - final_price if original_price > final_price else None

            return Price(
                original=original_price,
                final=final_price,
                discount=discount
            )
        except Exception as e:
            logger.error(f"Ошибка извлечения цен: {e}")
            return Price(original=0, final=0)

    def _extract_products(self, data: Dict[str, Any], seller_id: str) -> List[Product]:
        """Извлекает список товаров из ответа API"""
        products = []
        try:
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
            
            for item in items:
                try:
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
                    
                    multi_button = item.get('multiButton', {})
                    ozon_button = multi_button.get('ozonButton', {})
                    button_data = ozon_button.get('addToCartButtonWithQuantity', {})
                    quantity = button_data.get('maxItems', 0)
                    
                    tile_image = item.get('tileImage', {})
                    images = [img.get('image', {}).get('link') for img in tile_image.get('items', [])]
                    
                    price = self._extract_price_info(price_data)
                    
                    sku_id = item.get('skuId', '')
                    
                    if title:
                        product = Product(
                            id=sku_id,
                            name=html.unescape(title),
                            url=f"https://www.ozon.ru/product/{sku_id}/",
                            price=price,
                            rating=rating or 0.0,
                            reviews_count=reviews or 0
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
            api_responses_dir = Path("api_responses")
            api_responses_dir.mkdir(exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            
            async with httpx.AsyncClient(
                cookies=self.cookies,
                headers=self.headers,
                follow_redirects=True,
                timeout=30.0
            ) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    if "application/json" in response.headers.get("Content-Type", "") or response.text.strip().startswith('{'):
                        try:
                            json_data = response.json()
                            
                            json_file = api_responses_dir / f"response_{timestamp}.json"
                            with open(json_file, "w", encoding="utf-8") as f:
                                json.dump(json_data, f, ensure_ascii=False, indent=2)
                            
                            return json_data
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка при разборе JSON: {e}")
                            raw_file = api_responses_dir / f"raw_response_{timestamp}.txt"
                            with open(raw_file, "w", encoding="utf-8") as f:
                                f.write(response.text)
                    else:
                        html_file = api_responses_dir / f"html_response_{timestamp}.html"
                        with open(html_file, "w", encoding="utf-8") as f:
                            f.write(response.text)
                else:
                    error_file = api_responses_dir / f"error_{response.status_code}_{timestamp}.txt"
                    with open(error_file, "w", encoding="utf-8") as f:
                        f.write(response.text)
                
                return None
                
        except Exception as e:
            logger.error(f"Ошибка запроса: {e}")
            return None

    async def get_page(self, seller_id: str, page: int = 1) -> Optional[PageResult]:
        """Получает данные одной страницы"""
        url = f"https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"
        params = {
            "url": f"/seller/{seller_id}/products/",
            "layout_container": "categorySearchMegapagination",
            "layout_page_index": page,
            "page": page
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers, cookies=self.cookies) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                
                # Сохраняем ответ API если включено
                self._save_api_response(url, data)
                
                pagination = self._extract_pagination_info(data)
                if not pagination:
                    return None

                products = self._extract_products(data, seller_id)

                return PageResult(
                    pagination=pagination,
                    products=products
                )

    async def get_product(self, product_id: int) -> Optional[Product]:
        """Получение информации о конкретном товаре"""
        api_url = f"https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"
        params = {
            "url": f"/product/{product_id}/"
        }
        
        data = await self._make_request(api_url, params)
        if not data:
            return None
            
        try:
            widget_states = data.get('widgetStates', {})
            product_key = next((key for key in widget_states.keys() 
                              if 'webProductHeading' in key), None)
                              
            if not product_key:
                return None
                
            product_data = json.loads(widget_states[product_key])
            
            name = product_data.get('title', '')
            price_data = product_data.get('price', {})
            rating = product_data.get('rating', {}).get('value', 0)
            reviews_count = product_data.get('rating', {}).get('count', 0)
            
            price = self._extract_price_info(price_data)
            
            return Product(
                id=product_id,
                name=name,
                url=f"https://www.ozon.ru/product/{product_id}/",
                price=price,
                rating=rating,
                reviews_count=reviews_count
            )
            
        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None 

    async def get_products_page(self, seller_id: str, page: int = 1) -> Dict[str, Any]:
        url = f"https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url=/seller/{seller_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, cookies=self.cookies) as response:
                response_data = await response.json()
                
                # Сохраняем ответ API если включено
                self._save_api_response(url, response_data)
                
                # Остальной код обработки... 