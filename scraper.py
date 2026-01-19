"""
AKILLI ÜRÜN SCRAPING MODÜLÜ - YENİ MİMARİ v2.0
================================================================
✅ Mobil link normalizasyonu (m.trendyol.com → www.trendyol.com)
✅ Evrensel görsel yönetimi (Arçelik WebP, Hepsiburada format)
✅ Gelişmiş generic scraper (JS değişken madenciliği)
✅ Akıllı kategori tespiti (genişletilmiş kelime havuzu)
✅ User-Agent rotasyonu ve retry mekanizması
"""

import re
import json
import time
import logging
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Cloudflare bypass için cloudscraper
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
    logger.info("✅ cloudscraper yüklü")
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    logger.warning("⚠️ cloudscraper yüklü değil: pip install cloudscraper")

# ============================================
# CACHE SİSTEMİ (5 dakika TTL)
# ============================================
SCRAPE_CACHE = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

# ============================================
# RATE LIMITING
# ============================================
LAST_REQUEST_TIME = {}
MIN_REQUEST_INTERVAL = 1.5  # API çağrıları arası minimum 1.5 saniye

# ============================================
# USER-AGENT ROTASYONU (Masaüstü + Mobil)
# ============================================
USER_AGENTS = [
    # Masaüstü - Chrome/Windows
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Upgrade-Insecure-Requests': '1',
    },
    # Masaüstü - Firefox/Windows
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Upgrade-Insecure-Requests': '1',
    },
    # Mobil - iPhone Safari
    {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    },
    # Mobil - Android Chrome
    {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    }
]

# ============================================
# GENİŞLETİLMİŞ REGEX PATTERNS
# ============================================
REGEX_PATTERNS = {
    # Boyut kalıpları
    'boyut_wxhxd': r'(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)\s*(?:cm|mm|m)?',
    'genislik': r'(?:genişlik|en|width)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:cm|mm|m)?',
    'yukseklik': r'(?:yükseklik|boy|height)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:cm|mm|m)?',
    'derinlik': r'(?:derinlik|depth)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:cm|mm|m)?',

    # Kapasite
    'kapasite_litre': r'(\d+(?:[.,]\d+)?)\s*(?:litre|lt|l)\b',
    'kapasite_kg': r'(\d+(?:[.,]\d+)?)\s*(?:kg|kilo)',

    # Enerji sınıfı
    'enerji_sinifi': r'(?:enerji\s*sınıfı|energy\s*class)[:\s]*([A-Ga-g](?:\+{1,3})?)',
    'enerji_sinifi_alt': r'\b([A-G](?:\+{1,3})?)\s*(?:enerji|energy)',

    # Ekran
    'ekran_inc': r"(\d+(?:[.,]\d+)?)\s*(?:inç|inch|''|\"|\"|in\b)",
    'ekran_cm': r'(\d+)\s*(?:ekran|cm\s*ekran)',

    # Güç/Watt
    'watt': r'(\d+(?:[.,]\d+)?)\s*(?:watt|w)\b',

    # Devir (Çamaşır makinesi)
    'devir': r'(\d+)\s*(?:devir|rpm|d/dk)',

    # Su tüketimi
    'su_tuketimi': r'(?:su\s*tüketimi)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:lt|litre|l)',

    # Gürültü
    'gurultu_db': r'(\d+(?:[.,]\d+)?)\s*(?:db|dba|desibel)',

    # İşlemci
    'islemci': r'(?:intel|amd|apple|qualcomm|core|ryzen|m\d+)[^\n,]{0,50}',

    # RAM
    'ram': r'(\d+)\s*(?:gb|tb)\s*(?:ram|bellek|memory)',

    # Depolama
    'depolama': r'(\d+)\s*(?:gb|tb)\s*(?:ssd|hdd|emmc|storage|depolama)',

    # Çözünürlük
    'cozunurluk': r'(\d{3,4})\s*[xX×]\s*(\d{3,4})',
    'cozunurluk_alt': r'(4K|8K|FHD|Full\s*HD|UHD|QHD|2K)',

    # Malzeme/Kumaş
    'malzeme': r'(?:malzeme|materyal|material|kumaş|fabric)[:\s]*([A-Za-zğüşıöçĞÜŞİÖÇ\s,]+)',
    'kumas_tipi': r'\b(pamuk|saten|ranforce|penye|floş|pike|şardonlu|jakarlı|kadife|keten|ipek|süet|deri|mikrofiber)\b',

    # Mobilya tipleri (3+3+1, 2+3 formatları dahil)
    'mobilya_tipi': r"(\d+['']lü|\d+\+\d+\+\d+|\d+-\d+-\d+|\d+\+\d+|\d+-\d+|köşe\s*takımı|berjer|chester|kanepe|zigon)",
}

# ============================================
# SİTE HANDLER ROUTER - v3.0
# ============================================
SITE_HANDLERS = {
    # Marketplace - API Öncelikli
    'trendyol.com': 'api_trendyol',
    'hepsiburada.com': 'jsonld',  # JSON-LD schema kullan
    'n11.com': 'datalayer',
    'ciceksepeti.com': 'datalayer',

    # Beyaz Eşya - JSON-LD Çalışıyor
    'arcelik.com.tr': 'jsonld',
    'beko.com.tr': 'jsonld',
    'vestel.com.tr': 'jsonld',
    'bosch-home.com.tr': 'jsonld',
    'siemens-home.bsh-group.com': 'jsonld',
    'samsung.com': 'jsonld_datalayer',
    'altus.com.tr': 'jsonld',
    'lg.com': 'jsonld_datalayer',
    'philips.com.tr': 'jsonld',
    'grundig.com': 'jsonld',
    'whirlpool.com.tr': 'jsonld',
    'electrolux.com.tr': 'jsonld',
    'indesit.com.tr': 'jsonld',
    'hotpoint.com.tr': 'jsonld',
    'profilo.com': 'jsonld',

    # Mobilya - Akinon Platform
    'enzahome.com.tr': 'akinon',
    'alfemo.com.tr': 'akinon',
    'istikbal.com.tr': 'akinon',
    'bellona.com.tr': 'akinon',
    'dogtas.com': 'akinon',
    'mondi.com.tr': 'akinon',

    # Mobilya - Shopify
    'normod.com': 'shopify',
    'vivense.com': 'shopify',
    'koltuktakimi.com': 'shopify',
    'mobilya31.com': 'shopify',

    # Mobilya - Diğer
    'ikea.com.tr': 'ikea',
    'bellona.com.tr': 'jsonld',
    'istikbal.com.tr': 'jsonld',
    'dogtas.com': 'meta_html',
    'mondi.com.tr': 'meta_html',
    'yildizmobilya.com.tr': 'jsonld',
    'kilim.com': 'meta_html',
    'weltew.com': 'meta_html',
    'tepe-home.com': 'meta_html',

    # Ev Tekstili
    'englishhome.com': 'woocommerce',
    'madamecoco.com': 'woocommerce',
    'yatas.com.tr': 'jsonld',
    'tac.com.tr': 'woocommerce',
    'chakra.com.tr': 'woocommerce',
    'ozdilek.com.tr': 'meta_html',
    'linens.com.tr': 'woocommerce',
    'enlev.com.tr': 'meta_html',
    'englishhome.com.tr': 'woocommerce',

    # Dekorasyon
    'zarahome.com': 'nextjs',
    'karaca.com': 'datalayer',
    'hm.com': 'nextjs',
    'koleksiyon.com.tr': 'meta_html',
    'pasabahce.com': 'jsonld',
    'bernardo.com.tr': 'jsonld',
    'kutahyaporselen.com': 'jsonld',

    # DIY
    'koctas.com.tr': 'jsonld_datalayer',
    'bauhaus.com.tr': 'meta_html',
    'adeo.com.tr': 'meta_html',
    'praktiker.com.tr': 'meta_html',

    # Elektronik
    'vatanbilgisayar.com': 'datalayer',
    'teknosa.com': 'datalayer',
    'mediamarkt.com.tr': 'datalayer',
    'gold.com.tr': 'meta_html',
    'aygaz.com.tr': 'jsonld',
}

def get_site_handler(domain):
    """Domain'den uygun handler'ı bul"""
    domain_lower = domain.lower()
    for site_domain, handler in SITE_HANDLERS.items():
        if site_domain in domain_lower:
            return handler
    return 'generic'

def normalize_price(price_str):
    """Fiyat string'ini float'a çevir"""
    if isinstance(price_str, (int, float)):
        return float(price_str)
    if not price_str:
        return 0

    price_clean = str(price_str).replace('TL', '').replace('₺', '').strip()

    # Nokta ve virgül normalizasyonu
    if ',' in price_clean and '.' in price_clean:
        if price_clean.rindex(',') > price_clean.rindex('.'):
            price_clean = price_clean.replace('.', '').replace(',', '.')
        else:
            price_clean = price_clean.replace(',', '')
    elif ',' in price_clean:
        price_clean = price_clean.replace(',', '.')
    elif '.' in price_clean:
        parts = price_clean.split('.')
        if len(parts) == 2 and len(parts[1]) == 3:
            price_clean = price_clean.replace('.', '')

    price_clean = price_clean.replace(' ', '')
    try:
        return float(price_clean)
    except:
        return 0

# ============================================
# CACHE YÖNETİMİ
# ============================================
def get_from_cache(url):
    """Cache'den veri çek"""
    if url in SCRAPE_CACHE:
        cached_data, timestamp = SCRAPE_CACHE[url]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
            print(f"✅ Cache hit: {url}")
            return cached_data
        else:
            # Expired cache
            del SCRAPE_CACHE[url]
    return None

def save_to_cache(url, data):
    """Cache'e kaydet"""
    SCRAPE_CACHE[url] = (data, datetime.now())

def clear_expired_cache():
    """Süresi dolmuş cache'leri temizle"""
    now = datetime.now()
    expired_keys = [
        url for url, (data, timestamp) in SCRAPE_CACHE.items()
        if now - timestamp >= timedelta(seconds=CACHE_TTL_SECONDS)
    ]
    for key in expired_keys:
        del SCRAPE_CACHE[key]

# ============================================
# RATE LIMITING
# ============================================
def wait_for_rate_limit(domain):
    """Rate limit kontrolü - API çağrıları arası bekleme"""
    if domain in LAST_REQUEST_TIME:
        elapsed = time.time() - LAST_REQUEST_TIME[domain]
        if elapsed < MIN_REQUEST_INTERVAL:
            wait_time = MIN_REQUEST_INTERVAL - elapsed
            print(f"⏱️  Rate limit: {wait_time:.1f}s bekliyor ({domain})")
            time.sleep(wait_time)

    LAST_REQUEST_TIME[domain] = time.time()

# ============================================
# TRENDYOL PUBLIC API PARSER
# ============================================
def scrape_api_trendyol(url, session):
    """Trendyol Public API"""
    try:
        # Product ID extraction
        match = re.search(r'-p-(\d+)', url)
        if not match:
            print(f"⚠️ Trendyol: Product ID bulunamadı (URL pattern: -p-XXXXX)")
            return None

        product_id = match.group(1)
        api_url = f'https://public.trendyol.com/discovery-web-productgw-service/api/productDetail/{product_id}'

        # Rate limiting for API
        wait_for_rate_limit('trendyol.com')

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.trendyol.com/',
        }

        response = session.get(api_url, headers=headers, timeout=10, proxies={})

        if response.status_code != 200:
            print(f"⚠️ Trendyol API: HTTP {response.status_code}")
            return None

        data = response.json()

        if 'result' not in data:
            print(f"⚠️ Trendyol API: 'result' field bulunamadı")
            return None

        product = data.get('result', {})
        price = product.get('price', {}).get('sellingPrice', 0)
        images = product.get('images', [])
        image_url = images[0] if images else ''

        if image_url and not image_url.startswith('http'):
            image_url = 'https://cdn.dsmcdn.com' + image_url

        result = {
            'title': product.get('name', ''),
            'price': float(price) if price else 0,
            'image_url': image_url,
            'brand': product.get('brand', {}).get('name', ''),
            'description': product.get('description', ''),
        }

        # Veri kalitesi kontrolü
        if not result['title']:
            print(f"⚠️ Trendyol API: Başlık boş")
        if not result['price']:
            print(f"⚠️ Trendyol API: Fiyat bulunamadı")

        return result

    except requests.exceptions.Timeout:
        print(f"⚠️ Trendyol API: Timeout (10 saniye)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Trendyol API: Network error - {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ Trendyol API: JSON parse error - {str(e)}")
        return None
    except Exception as e:
        print(f"⚠️ Trendyol API: Unexpected error - {str(e)}")
        return None

# ============================================
# IKEA PARSER
# ============================================
def scrape_ikea(url, soup, use_cloudscraper=True):
    """IKEA özel parser - Timeout ve bot koruması için optimize"""
    try:
        result = {'title': '', 'price': 0, 'brand': 'IKEA', 'image_url': ''}

        # Eğer soup None ise veya içerik boşsa, yeniden fetch et
        if soup is None or not soup.find('body'):
            logger.info("🔄 IKEA: Cloudscraper ile yeniden deneniyor...")
            if CLOUDSCRAPER_AVAILABLE and use_cloudscraper:
                scraper = cloudscraper.create_scraper(
                    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True},
                    delay=5
                )
                try:
                    response = scraper.get(url, timeout=45)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                except Exception as e:
                    logger.error(f"⚠️ IKEA cloudscraper hatası: {e}")
                    return None
            else:
                logger.warning("⚠️ IKEA: Cloudscraper kullanılamıyor")
                return None

        # JSON-LD önce dene (IKEA bunu kullanıyor)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = next((item for item in data if item.get('@type') == 'Product'), {})
                if data.get('@type') == 'Product':
                    result['title'] = data.get('name', '')
                    offers = data.get('offers', {})
                    if isinstance(offers, list):
                        offers = offers[0]
                    if offers:
                        result['price'] = float(offers.get('price', 0))
                    img = data.get('image', '')
                    result['image_url'] = img[0] if isinstance(img, list) else img

                    if result['title'] and result['price'] > 0:
                        return result
            except:
                continue

        # Meta tags
        og_title = soup.find('meta', property='og:title')
        if og_title and not result['title']:
            result['title'] = og_title.get('content', '').split('|')[0].strip()

        og_image = soup.find('meta', property='og:image')
        if og_image and not result['image_url']:
            result['image_url'] = og_image.get('content', '')

        # Fiyat için product:price:amount meta tag
        price_meta = soup.find('meta', property='product:price:amount')
        if price_meta and not result['price']:
            try:
                result['price'] = float(price_meta.get('content', '0').replace(',', '.'))
            except:
                pass

        # HTML selectors
        if not result['price']:
            price_selectors = [
                '.pip-temp-price__integer', '.pip-price',
                '[data-price]', '.product-pip__price',
                '.range-revamp-pip-price-package__main-price'
            ]
            for sel in price_selectors:
                el = soup.select_one(sel)
                if el:
                    price_text = el.get_text(strip=True)
                    price_clean = re.sub(r'[^\d]', '', price_text)
                    if price_clean:
                        try:
                            result['price'] = float(price_clean)
                            if result['price'] > 0:
                                break
                        except:
                            continue

        # Hiçbir yöntem çalışmadıysa meta_html_fallback dene
        if not (result['title'] and result['price'] > 0):
            logger.info("🔄 IKEA: meta_html_fallback deneniyor...")
            fallback_result = scrape_meta_html_fallback(soup, url)
            if fallback_result:
                return fallback_result

        return result if (result['title'] and result['price'] > 0) else None

    except Exception as e:
        logger.error(f"⚠️ IKEA parser hatası: {e}")
        return None

# ============================================
# HEPSİBURADA JSON-LD PARSER
# ============================================
def scrape_hepsiburada(url, use_cloudscraper=True):
    """Scrape Hepsiburada using JSON-LD schema"""
    try:
        logger.info(f"Trying Hepsiburada JSON-LD parser for {url}")
        response, error = fetch_with_retry(url, timeout=20, use_cloudscraper=use_cloudscraper)

        if not response or response.status_code != 200:
            logger.error(f"Failed to fetch Hepsiburada: {url} (status: {response.status_code if response else 'None'})")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # JSON-LD script tag'lerini bul
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)

                # @graph içinde Product ara
                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Product':
                            offers = item.get('offers', {})
                            image_data = item.get('image', [])
                            images = image_data if isinstance(image_data, list) else [image_data] if image_data else []

                            brand_data = item.get('brand', {})
                            brand = brand_data.get('name') if isinstance(brand_data, dict) else str(brand_data)

                            rating_data = item.get('aggregateRating', {})

                            logger.info(f"✅ Hepsiburada JSON-LD başarılı: {item.get('name', '')[:50]}")
                            return {
                                'title': item.get('name'),
                                'price': float(offers.get('price', 0)),
                                'brand': brand or '',
                                'image_url': images[0] if images else '',
                                'description': item.get('description', ''),
                                'sku': item.get('sku', ''),
                                'category': item.get('category', ''),
                                'rating': rating_data.get('ratingValue') if rating_data else None,
                                'review_count': rating_data.get('ratingCount') if rating_data else None,
                            }

                # Direkt Product objesi
                elif isinstance(data, dict) and data.get('@type') == 'Product':
                    offers = data.get('offers', {})
                    image_data = data.get('image', [])
                    images = image_data if isinstance(image_data, list) else [image_data] if image_data else []

                    brand_data = data.get('brand', {})
                    brand = brand_data.get('name') if isinstance(brand_data, dict) else str(brand_data)

                    rating_data = data.get('aggregateRating', {})

                    logger.info(f"✅ Hepsiburada JSON-LD başarılı: {data.get('name', '')[:50]}")
                    return {
                        'title': data.get('name'),
                        'price': float(offers.get('price', 0)),
                        'brand': brand or '',
                        'image_url': images[0] if images else '',
                        'description': data.get('description', ''),
                        'sku': data.get('sku', ''),
                        'category': data.get('category', ''),
                        'rating': rating_data.get('ratingValue') if rating_data else None,
                        'review_count': rating_data.get('ratingCount') if rating_data else None,
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"JSON-LD parse error: {e}")
                continue
            except Exception as e:
                logger.warning(f"JSON-LD processing error: {e}")
                continue

        logger.error("No Product found in JSON-LD")
        return None

    except Exception as e:
        logger.error(f"Hepsiburada scrape failed: {e}")
        return None

# ============================================
# AKINON PLATFORM PARSER (Enza Home, İstikbal, Bellona, Doğtaş, Mondi, Alfemo)
# ============================================
def scrape_enza_akinon(url, use_cloudscraper=False):
    """Scrape Enza Home and other Akinon platform sites using hidden dataLayer"""
    try:
        logger.info(f"Trying Akinon platform parser for {url}")
        response, error = fetch_with_retry(url, timeout=20, use_cloudscraper=use_cloudscraper)

        if not response or response.status_code != 200:
            logger.error(f"Failed to fetch Akinon site: {url} (status: {response.status_code if response else 'None'})")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Hidden div içindeki JSON'ı bul
        datalayer_div = soup.find('div', class_='js-datalayer-group-item')
        if datalayer_div and datalayer_div.string:
            try:
                data = json.loads(datalayer_div.string.strip())
                product = data.get('product', {})

                if product:
                    # Görsel URL'lerini bul
                    images = []
                    img_tags = soup.find_all('img', class_='product-image')
                    for img in img_tags:
                        src = img.get('src') or img.get('data-src')
                        if src and src.startswith('http'):
                            images.append(src)

                    # Ürün başlığını bul - tam başlık HTML'de
                    title_elem = soup.find('h1', class_='product-name') or soup.find('div', class_='combine-product-info-title')
                    if title_elem:
                        title_link = title_elem.find('a')
                        title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
                    else:
                        title = product.get('name')

                    # Açıklama - HTML tag'lerini temizle
                    description = product.get('attributes', {}).get('integration_item_short_desc', '')
                    if description:
                        description = BeautifulSoup(description, 'html.parser').get_text(strip=True)

                    # Marka bilgisini attributes'tan al
                    brand = product.get('attributes', {}).get('integration_marka', '')
                    if not brand:
                        # Domain'e göre default marka
                        if 'enzahome' in url:
                            brand = 'Yatas Enza'
                        elif 'istikbal' in url:
                            brand = 'İstikbal'
                        elif 'bellona' in url:
                            brand = 'Bellona'
                        elif 'dogtas' in url:
                            brand = 'Doğtaş'
                        elif 'mondi' in url:
                            brand = 'Mondi'
                        elif 'alfemo' in url:
                            brand = 'Alfemo'

                    logger.info(f"✅ Akinon başarılı: {title[:50] if title else 'N/A'}")
                    return {
                        'title': title,
                        'price': float(product.get('price', 0)),
                        'brand': brand,
                        'image_url': images[0] if images else '',
                        'description': description,
                        'sku': product.get('sku', ''),
                        'category': product.get('attributes', {}).get('integration_kategori_adi', ''),
                        'in_stock': int(product.get('stock', 0)) > 0,
                        'retail_price': product.get('retail_price'),
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"Akinon dataLayer parse error: {e}")
            except Exception as e:
                logger.warning(f"Akinon data processing error: {e}")

        logger.error("No dataLayer found in Akinon page")
        return None

    except Exception as e:
        logger.error(f"Akinon scrape failed: {e}")
        return None

# ============================================
# META HTML FALLBACK
# ============================================
def scrape_meta_html_fallback(soup, url):
    """
    Meta tags ve HTML selectors kullanan fallback parser
    Tüm site-specific parser'lar başarısız olduğunda kullanılır
    """
    try:
        logger.info(f"Trying meta_html_fallback for {url}")
        result = {'title': '', 'price': 0, 'brand': '', 'image_url': ''}

        # Title - OG tags
        og_title = soup.find('meta', property='og:title')
        if og_title:
            result['title'] = og_title.get('content', '').split('|')[0].split('-')[0].strip()

        # Price - OG tags ve common selectors
        og_price = soup.find('meta', property='og:price:amount') or soup.find('meta', property='product:price:amount')
        if og_price:
            try:
                result['price'] = float(og_price.get('content', '0').replace(',', '.'))
            except:
                pass

        # Price selectors (fallback)
        if not result['price']:
            price_selectors = [
                '.product-price', '.price', '.current-price', '.sale-price',
                '[data-price]', '.pdp-price', 'span[itemprop="price"]',
                '.product-detail-price', '.product__price', '.ProductPrice'
            ]
            for sel in price_selectors:
                el = soup.select_one(sel)
                if el:
                    price_text = el.get('content', '') or el.get_text(strip=True)
                    price_clean = re.sub(r'[^\d,.]', '', price_text)
                    price_clean = price_clean.replace('.', '').replace(',', '.')
                    try:
                        result['price'] = float(price_clean)
                        if result['price'] > 0:
                            break
                    except:
                        continue

        # Brand - OG tags
        og_brand = soup.find('meta', property='og:brand') or soup.find('meta', property='product:brand')
        if og_brand:
            result['brand'] = og_brand.get('content', '')

        # Image - OG tags
        og_image = soup.find('meta', property='og:image')
        if og_image:
            result['image_url'] = og_image.get('content', '')

        logger.info(f"Meta/HTML fallback result: title={result['title'][:30] if result['title'] else 'N/A'}, price={result['price']}")
        return result if (result['title'] or result['price'] > 0) else None

    except Exception as e:
        logger.error(f"Meta/HTML fallback error: {e}")
        return None

# ============================================
# KARACA DATALAYER PARSER
# ============================================
def scrape_datalayer_karaca(url, soup, html_text, use_cloudscraper=True):
    """Karaca özel parser - Çoklu yöntem"""
    try:
        logger.info(f"Trying Karaca dataLayer parser for {url}")
        result = {'title': '', 'price': 0, 'brand': 'Karaca', 'image_url': ''}

        # Yöntem 1: dataLayer - birden fazla regex pattern dene
        dataLayer_patterns = [
            r'dataLayer\.push\((.*?)\);',  # dataLayer.push(...)
            r'var\s+dataLayer\s*=\s*(\[.*?\]);',  # var dataLayer = [...]
            r'window\.dataLayer\s*=\s*(\[.*?\]);',  # window.dataLayer = [...]
            r'dataLayer\.push\(\s*({[\s\S]*?"ecommerce"[\s\S]*?})\s*\);',  # Detaylı ecommerce pattern
        ]

        for pattern in dataLayer_patterns:
            matches = re.finditer(pattern, html_text, re.DOTALL)
            for match in matches:
                try:
                    json_str = match.group(1)
                    # Trailing comma fix
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*]', ']', json_str)

                    data = json.loads(json_str)

                    # data bir array olabilir, kontrol et
                    if isinstance(data, list):
                        data = data[0] if data else {}

                    if 'ecommerce' in data:
                        ecommerce = data['ecommerce']

                        # detail.products format (GA Universal)
                        if 'detail' in ecommerce:
                            products = ecommerce['detail'].get('products', [])
                            if products:
                                product = products[0]
                                result['title'] = product.get('name', '')
                                result['price'] = float(product.get('price', 0))
                                result['brand'] = product.get('brand', 'Karaca')

                        # items format (GA4)
                        if 'items' in ecommerce:
                            items = ecommerce['items']
                            if items:
                                item = items[0]
                                result['title'] = item.get('item_name', '') or item.get('name', '')
                                result['price'] = float(item.get('price', 0))
                                result['brand'] = item.get('item_brand', 'Karaca')

                        if result['title'] and result['price'] > 0:
                            logger.info(f"Karaca dataLayer başarılı: {result['title'][:30]}")
                            break
                except Exception as e:
                    logger.debug(f"Karaca dataLayer pattern hatası: {e}")
                    continue

            if result['title'] and result['price'] > 0:
                break

        # Yöntem 2: __NEXT_DATA__ (Karaca Next.js kullanıyor olabilir)
        if not result['title'] or not result['price']:
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data and next_data.string:
                try:
                    data = json.loads(next_data.string)
                    page_props = data.get('props', {}).get('pageProps', {})

                    # Çeşitli key'leri dene
                    product = (page_props.get('product') or
                              page_props.get('productDetail') or
                              page_props.get('initialProduct') or
                              {})

                    if product:
                        result['title'] = product.get('name', '') or product.get('title', '')
                        result['price'] = float(product.get('price', 0) or product.get('salePrice', 0) or product.get('discountedPrice', 0))
                        result['image_url'] = product.get('image', '') or product.get('mainImage', '') or product.get('imageUrl', '')
                except:
                    pass

        # Yöntem 3: JSON-LD
        if not result['title'] or not result['price']:
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        data = next((item for item in data if item.get('@type') == 'Product'), {})
                    if data.get('@type') == 'Product':
                        result['title'] = data.get('name', '') or result['title']
                        offers = data.get('offers', {})
                        if isinstance(offers, list):
                            offers = offers[0]
                        if offers and not result['price']:
                            result['price'] = float(offers.get('price', 0))
                        if not result['image_url']:
                            img = data.get('image', '')
                            result['image_url'] = img[0] if isinstance(img, list) else img
                except:
                    continue

        # Yöntem 4: Meta tags + HTML (son çare)
        if not result['title']:
            og_title = soup.find('meta', property='og:title')
            if og_title:
                result['title'] = og_title.get('content', '').split('|')[0].split('-')[0].strip()

        if not result['price']:
            price_selectors = [
                '.product-price', '.price', '.current-price',
                '[data-price]', '.sale-price', '.pdp-price',
                'span[itemprop="price"]', '.product-detail-price'
            ]
            for sel in price_selectors:
                el = soup.select_one(sel)
                if el:
                    price_text = el.get('content', '') or el.get_text(strip=True)
                    price_clean = re.sub(r'[^\d,.]', '', price_text)
                    price_clean = price_clean.replace('.', '').replace(',', '.')
                    try:
                        result['price'] = float(price_clean)
                        if result['price'] > 0:
                            break
                    except:
                        continue

        if not result['image_url']:
            og_image = soup.find('meta', property='og:image')
            if og_image:
                result['image_url'] = og_image.get('content', '')

        logger.info(f"Karaca result: title={result['title'][:30] if result['title'] else 'N/A'}, price={result['price']}")

        # Hiçbir yöntem çalışmadıysa scrape_meta_html_fallback dene
        if not result['title'] and not result['price']:
            logger.warning("Karaca: Tüm yöntemler başarısız, meta_html_fallback deneniyor")
            fallback_result = scrape_meta_html_fallback(soup, url)
            if fallback_result:
                return fallback_result

        return result if (result['title'] or result['price'] > 0) else None

    except Exception as e:
        logger.error(f"Karaca parser error: {e}")
        return None

# ============================================
# WOOCOMMERCE PARSER (English Home, Madame Coco, IKEA vb.)
# ============================================
def parse_woocommerce_product(url, soup, use_cloudscraper=False):
    """
    WooCommerce kullanan siteler için özel parser
    1. HTML'den data-product-id çek
    2. Veya HTML içinden schema/meta parse et
    """
    try:
        logger.info(f"Trying WooCommerce parser for {url}")
        # WooCommerce genelde HTML'de zengin veri saklar
        # Product ID'yi bul
        product_div = soup.find('div', class_='product') or soup.find('div', attrs={'data-product-id': True})

        if product_div:
            # Title
            title = ''
            title_el = soup.select_one('.product_title, h1.product-title, .product-name')
            if title_el:
                title = title_el.get_text(strip=True)

            # Price
            price = 0
            price_selectors = [
                '.woocommerce-Price-amount', '.price ins .amount', '.price .amount',
                '.product-price .amount', 'span[itemprop="price"]', '.product_price .amount'
            ]
            for selector in price_selectors:
                price_el = soup.select_one(selector)
                if price_el:
                    price_text = price_el.get_text(strip=True)
                    price_clean = re.sub(r'[^\d,.]', '', price_text)
                    price_clean = price_clean.replace('.', '').replace(',', '.')
                    try:
                        price = float(price_clean)
                        if price > 0:
                            break
                    except:
                        continue

            # Image
            image_url = ''
            img_selectors = [
                '.woocommerce-product-gallery__image img',
                '.product-image img',
                'img.wp-post-image',
                '.product-gallery img'
            ]
            for selector in img_selectors:
                img = soup.select_one(selector)
                if img:
                    src = img.get('data-src') or img.get('data-large-image') or img.get('src')
                    if src and 'placeholder' not in src.lower():
                        image_url = src
                        break

            # Brand
            brand = ''
            brand_el = soup.select_one('.product-brand, .brand, [itemprop="brand"]')
            if brand_el:
                brand = brand_el.get_text(strip=True) or brand_el.get('content', '')

            if title or price > 0:
                return {
                    'title': title,
                    'price': price,
                    'image_url': image_url,
                    'brand': brand,
                    'description': '',
                }

        # WooCommerce başarısız olursa meta_html_fallback dene
        logger.info("🔄 WooCommerce başarısız, meta_html_fallback deneniyor...")
        fallback_result = scrape_meta_html_fallback(soup, url)
        if fallback_result:
            return fallback_result

        return None
    except Exception as e:
        logger.error(f"⚠️ WooCommerce parser hatası: {e}")
        # Exception durumunda da meta_html_fallback dene
        try:
            fallback_result = scrape_meta_html_fallback(soup, url)
            if fallback_result:
                return fallback_result
        except:
            pass
        return None

# ============================================
# SHOPIFY PARSER (Normod, Vivense vb.)
# ============================================
def scrape_shopify(url):
    """Scrape Shopify-based sites (Normod, Vivense)"""
    try:
        logger.info(f"Trying Shopify parser for {url}")
        parts = url.rstrip('/').split('/products/')
        if len(parts) < 2:
            logger.error(f"Invalid Shopify URL format: {url}")
            return None

        handle = parts[1].split('?')[0].split('#')[0].rstrip('/')
        base_url = parts[0]
        json_url = f"{base_url}/products/{handle}.json"

        logger.info(f"Trying Shopify JSON endpoint: {json_url}")
        response, error = fetch_with_retry(json_url, timeout=20, use_cloudscraper=False)

        # Eğer response yok veya 404 dönerse, bu site Shopify değil
        if not response:
            logger.warning(f"Failed to fetch Shopify JSON: {json_url} - {error}")
            return None

        if response.status_code == 404:
            logger.warning(f"Not a Shopify site or product not found: {url}")
            return None

        if response.status_code == 200:
            return parse_shopify_product(response.json())

    except Exception as e:
        logger.error(f"Shopify scrape failed for {url}: {e}")
    return None


def parse_shopify_product(data):
    """Parse Shopify product JSON"""
    try:
        logger.info(f"Parsing Shopify product data")
        # Shopify yanıtı direkt product objesi veya {"product": {...}} olabilir
        if isinstance(data, dict):
            product = data.get('product', data)

            if not product or not isinstance(product, dict):
                logger.warning("No valid product data in Shopify response")
                return None

            # İlk variant'ı al
            variants = product.get('variants', [])
            first_variant = variants[0] if variants else {}

            # Fiyat - string veya number olabilir
            price_val = first_variant.get('price', 0)
            try:
                price = float(price_val) if price_val else 0
            except:
                price = 0

            # Images listesi oluştur
            images = []
            for img in product.get('images', []):
                if isinstance(img, dict):
                    src = img.get('src')
                    if src:
                        images.append(src)
                elif isinstance(img, str):
                    images.append(img)

            # Description HTML'den temizle
            description = product.get('body_html', '')
            if description:
                description = BeautifulSoup(description, 'html.parser').get_text(strip=True)[:500]

            logger.info(f"✅ Shopify parse başarılı: {product.get('title', '')[:50]}")
            return {
                'title': product.get('title'),
                'price': price,
                'brand': product.get('vendor'),
                'image_url': images[0] if images else '',
                'description': description,
                'in_stock': first_variant.get('available', False),
                'sku': first_variant.get('sku'),
            }
    except Exception as e:
        logger.error(f"Shopify parse error: {e}")
    return None

# ============================================
# NEXT.JS PARSER (Karaca, Zara Home vb.)
# ============================================
def parse_nextjs_product(url, soup, use_cloudscraper=False):
    """
    Next.js kullanan siteler için özel parser
    __NEXT_DATA__ script'inden veri çıkarır
    """
    import os
    DEBUG = os.environ.get('SCRAPER_DEBUG', 'false').lower() == 'true'

    # Extract domain from URL
    from urllib.parse import urlparse
    domain = urlparse(url).netloc

    try:
        logger.info(f"Trying Next.js parser for {url}")
        # __NEXT_DATA__ script'ini bul
        next_data_script = soup.find('script', id='__NEXT_DATA__')
        if not next_data_script or not next_data_script.string:
            if DEBUG:
                print("⚠️ __NEXT_DATA__ script tag bulunamadı!")
            return None

        data = json.loads(next_data_script.string)

        if DEBUG:
            print(f"✅ __NEXT_DATA__ bulundu! Keys: {list(data.keys())}")

        # Karaca için
        if 'karaca' in domain:
            try:
                page_props = data.get('props', {}).get('pageProps', {})
                if DEBUG:
                    print(f"   pageProps keys: {list(page_props.keys())}")

                product = page_props.get('product', {})
                if DEBUG:
                    if product:
                        print(f"   product keys: {list(product.keys())}")
                        print(f"   name: {product.get('name', 'N/A')}")
                        print(f"   price: {product.get('price', 'N/A')}")
                    else:
                        print(f"   ⚠️ product key bulunamadı!")
                        print(f"   Alternatif aramalar:")
                        # Alternatif yolları dene
                        for key in page_props.keys():
                            if 'product' in key.lower():
                                print(f"      Bulundu: {key} -> {type(page_props[key])}")

                if product:
                    return {
                        'title': product.get('name', '') or product.get('title', ''),
                        'price': float(product.get('price', 0) or product.get('salePrice', 0)),
                        'image_url': product.get('image', '') or product.get('mainImage', ''),
                        'brand': product.get('brand', '') or 'Karaca',
                        'description': product.get('description', ''),
                    }
            except Exception as e:
                if DEBUG:
                    print(f"   ❌ Karaca parse hatası: {e}")
                pass

        # Zara Home için
        if 'zarahome' in domain or 'zara' in domain:
            try:
                page_props = data.get('props', {}).get('pageProps', {})
                product = page_props.get('product', {}) or page_props.get('productData', {})

                if product:
                    # Zara'nın veri yapısı
                    detail = product.get('detail', {})
                    colors = detail.get('colors', [{}])[0] if detail.get('colors') else {}

                    return {
                        'title': detail.get('displayName', '') or product.get('name', ''),
                        'price': float(colors.get('price', 0) / 100) if colors.get('price') else 0,  # Cent to TL
                        'image_url': colors.get('image', {}).get('url', '') if colors.get('image') else '',
                        'brand': 'Zara Home',
                        'description': detail.get('description', ''),
                    }
            except:
                pass

        # Hiçbir Next.js yöntemi çalışmadıysa meta_html_fallback dene
        logger.info("🔄 Next.js başarısız, meta_html_fallback deneniyor...")
        fallback_result = scrape_meta_html_fallback(soup, url)
        if fallback_result:
            return fallback_result

        return None
    except Exception as e:
        logger.error(f"⚠️ Next.js parser hatası: {e}")
        # Exception durumunda da meta_html_fallback dene
        try:
            fallback_result = scrape_meta_html_fallback(soup, url)
            if fallback_result:
                return fallback_result
        except:
            pass
        return None

# ============================================
# 1. MOBİL LİNK NORMALİZASYONU
# ============================================
def normalize_mobile_url(url):
    """
    Mobil subdomain'leri masaüstü versiyonuna çevirir
    m.trendyol.com → www.trendyol.com
    mobile.donanimhaber.com → www.donanimhaber.com
    touch.example.com → www.example.com
    """
    parsed = urlparse(url)
    domain_parts = parsed.netloc.split('.')

    # Mobil subdomain'leri tespit et ve değiştir
    if len(domain_parts) >= 3:
        subdomain = domain_parts[0].lower()
        if subdomain in ['m', 'mobile', 'touch', 'wap']:
            domain_parts[0] = 'www'
            new_domain = '.'.join(domain_parts)
            new_url = f"{parsed.scheme}://{new_domain}{parsed.path}"
            if parsed.query:
                new_url += f"?{parsed.query}"
            return new_url, True  # URL değişti

    return url, False  # URL değişmedi

# ============================================
# 2. EVRENSEL GÖRSEL YÖNETİMİ
# ============================================
def extract_image(soup, url, domain):
    """
    ÖNCELIK SIRASI:
    1. application/ld+json içindeki image
    2. og:image, twitter:image
    3. link[rel="image_src"]
    4. HTML içinde data-src, data-original, srcset (en yüksek çözünürlük)
    5. Son çare: src

    ÖNEMLİ: Arçelik/Beko için WebP zorlaması
    """
    image_url = ''

    # 1. JSON-LD'den image
    try:
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = next((item for item in data if item.get('@type') == 'Product'), {})
                if '@graph' in data:
                    data = next((item for item in data['@graph'] if item.get('@type') == 'Product'), {})

                if data.get('@type') in ['Product', 'product', 'IndividualProduct']:
                    img = data.get('image', '')
                    if isinstance(img, list) and len(img) > 0:
                        image_url = img[0] if isinstance(img[0], str) else img[0].get('url', '')
                    elif isinstance(img, str):
                        image_url = img
                    elif isinstance(img, dict):
                        image_url = img.get('url', '')

                    if image_url:
                        break
            except:
                continue
    except:
        pass

    # 2. Meta tags (og:image, twitter:image)
    if not image_url:
        meta_img = soup.find('meta', property='og:image')
        if meta_img:
            image_url = meta_img.get('content', '')

    if not image_url:
        twitter_img = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_img:
            image_url = twitter_img.get('content', '')

    # 3. link[rel="image_src"]
    if not image_url:
        link_img = soup.find('link', rel='image_src')
        if link_img:
            image_url = link_img.get('href', '')

    # 4. HTML elementlerinden (data-src, srcset, src)
    if not image_url:
        img_selectors = [
            # Generic
            '.product-image img', '.gallery-image img', '[itemprop="image"]',
            '.product-gallery img', '.pdp-gallery img', '.main-image img',
            '.product-detail-image img', 'img.product-image', '.slick-slide img',
            '.carousel-item img', '.product-img img', '[data-testid*="image"] img',
            # Magento 2
            '.gallery-placeholder img', '.fotorama__img', '.product-image-photo',
            # PrestaShop
            '#bigpic', '.product-cover img', '.js-qv-product-cover img',
            # OpenCart
            '.product-image img', '#image', '.thumbnails img',
            # WooCommerce
            '.woocommerce-product-gallery__image img', '.wp-post-image',
            # Shopware
            '.gallery-slider-item img', '.image-slider img',
            # Fallback
            'img[alt*="product"]', 'img[alt*="ürün"]', '.product img'
        ]

        for selector in img_selectors:
            img = soup.select_one(selector)
            if img:
                # Öncelik: data-src > data-original > srcset (en büyük) > src
                src = img.get('data-src') or img.get('data-original')

                # srcset varsa en yüksek çözünürlüklüyü al
                if not src and img.get('srcset'):
                    srcset = img.get('srcset')
                    # srcset format: "url1 1x, url2 2x, url3 3x"
                    urls = [s.strip().split()[0] for s in srcset.split(',')]
                    if urls:
                        src = urls[-1]  # En yüksek çözünürlüklü (genellikle son)

                if not src:
                    src = img.get('src')

                if src and 'placeholder' not in src.lower() and 'data:image' not in src:
                    image_url = src
                    break

    # Protokol düzeltmeleri
    if image_url:
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            parsed = urlparse(url)
            image_url = f"{parsed.scheme}://{parsed.netloc}{image_url}"
        elif image_url.startswith('www.'):
            image_url = 'https://' + image_url

    # ============ ÖNEMLİ: SİTE-ÖZEL GÖRSEL NORMALİZASYONU ============

    # ARÇELIK/BEKO: .webp zorlaması ve 2000x2000 format
    if image_url and ('arcelik.com' in domain or 'beko.com' in domain):
        if 'media/resize' in image_url or 'media/' in image_url:
            # 1. /media/ → /media/resize/
            if '/resize/' not in image_url:
                image_url = image_url.replace('/media/', '/media/resize/')

            # 2. Eğer /1000Wx1000H/ veya /2000Wx2000H/ gibi format varsa → /2000Wx2000H/image.webp
            if re.search(r'/\d+Wx\d+H/', image_url):
                image_url = re.sub(r'/\d+Wx\d+H/image\.(png|jpg|jpeg|webp)', '/2000Wx2000H/image.webp', image_url)
            else:
                # 3. Format yoksa dosya adından sonra ekle
                # Örnek: .../7131960100_MDM2_LOW_1.png → .../7131960100_MDM2_LOW_1.png/2000Wx2000H/image.webp
                match = re.search(r'\.(png|jpg|jpeg|webp)(\?.*)?$', image_url, re.IGNORECASE)
                if match:
                    ext_pos = match.start() + len(match.group(1)) + 1
                    image_url = image_url[:ext_pos] + '/2000Wx2000H/image.webp'
                    # Query string temizle
                    if '?' in image_url:
                        image_url = image_url.split('?')[0]

    # HEPSIBURADA: /format:webp ekle
    elif image_url and 'hepsiburada.com' in domain:
        if 'productimages' in image_url and '/format:webp' not in image_url:
            # URL sonuna /format:webp ekle
            if '?' in image_url:
                image_url = image_url.split('?')[0]
            image_url = image_url.rstrip('/') + '/format:webp'

    return image_url

# ============================================
# 3. GELİŞMİŞ GENERIC SCRAPER (JS Madenciliği)
# ============================================
def extract_hidden_json_data(soup, html_text):
    """
    HTML içindeki gizli JS değişkenlerinden JSON verisi çıkar
    Örnek: window.__PRELOADED_STATE__ = {...}
    Örnek: var product = {...}
    Örnek: dataLayer.push({...}) - Karaca, MediaMarkt vb.
    """
    result = {
        'title': '',
        'price': 0,
        'brand': '',
        'specs': {}
    }

    # Pattern 0: window.dataLayer (Google Tag Manager)
    # Karaca, MediaMarkt gibi siteler bunu kullanır
    dataLayer_pattern = r'dataLayer\.push\(\s*({[\s\S]*?})\s*\);'
    dataLayer_matches = re.finditer(dataLayer_pattern, html_text)

    for match in dataLayer_matches:
        try:
            json_str = match.group(1)
            data = json.loads(json_str)

            # Ecommerce verisi
            if 'ecommerce' in data:
                ecommerce = data['ecommerce']

                # Detail view (GA Universal format)
                if 'detail' in ecommerce and 'products' in ecommerce['detail']:
                    products = ecommerce['detail']['products']
                    if products and len(products) > 0:
                        product = products[0]
                        if not result['title']:
                            result['title'] = product.get('name', '')
                        if not result['price']:
                            try:
                                result['price'] = float(product.get('price', 0))
                            except:
                                pass
                        if not result['brand']:
                            result['brand'] = product.get('brand', '')

                # Items (GA4 format)
                if 'items' in ecommerce and len(ecommerce['items']) > 0:
                    item = ecommerce['items'][0]

                    # Title extraction (item_name or name)
                    if not result['title']:
                        result['title'] = item.get('item_name', '') or item.get('name', '')

                    # Price extraction with multiple formats
                    if not result['price']:
                        price_val = item.get('price', 0) or item.get('item_price', 0)
                        try:
                            price_float = float(price_val)
                            # Bazı siteler fiyatı cent cinsinden gönderir (örn: 269900 = 2699.00 TL)
                            # Eğer fiyat 10000'den büyükse ve ondalık kısmı yoksa, cent olabilir
                            if price_float > 10000 and price_float == int(price_float):
                                # Muhtemelen cent cinsinden, 100'e böl
                                result['price'] = price_float / 100
                            else:
                                result['price'] = price_float
                        except:
                            pass

                    # Brand extraction
                    if not result['brand']:
                        result['brand'] = item.get('item_brand', '') or item.get('brand', '')

                    # Image URL extraction (GA4 genellikle image gönderir)
                    if not result['image_url']:
                        img = item.get('item_image', '') or item.get('image_url', '') or item.get('image', '')
                        if img and img.startswith('http'):
                            result['image_url'] = img

                    # SKU/GTIN extraction
                    if not result.get('sku'):
                        result['sku'] = item.get('item_id', '') or item.get('sku', '')

                    # Category extraction
                    if not result.get('category'):
                        cat = (item.get('item_category', '') or
                               item.get('item_category1', '') or
                               item.get('category', ''))
                        if cat:
                            result['category'] = cat

            # Eğer bulunduysa döndür
            if result['title'] or result['price']:
                return result

        except:
            continue

    # Pattern 1: Klaviyo tracking (Shopify sites - Normod, Vivense, vb.)
    # _learnq.push(['track', 'Viewed Product', {...}])
    klaviyo_pattern = r'var\s+item\s*=\s*({[\s\S]*?});[\s\S]*?_learnq\.push'
    klaviyo_match = re.search(klaviyo_pattern, html_text)
    if klaviyo_match:
        try:
            json_str = klaviyo_match.group(1)
            data = json.loads(json_str)

            if not result['title'] and 'Name' in data:
                result['title'] = data.get('Name', '')

            if not result['price'] and ('Price' in data or 'Value' in data):
                # Price: "101.360TL" veya Value: "101,360"
                price_str = data.get('Price', '') or data.get('Value', '')
                price_str = price_str.replace('TL', '').replace('.', '').replace(',', '.')
                try:
                    result['price'] = float(price_str)
                except:
                    pass

            if not result['brand'] and 'Brand' in data:
                result['brand'] = data.get('Brand', '')

            # Eğer bulunduysa döndür
            if result['title'] or result['price']:
                return result
        except:
            pass

    # Pattern 2: window.__PRELOADED_STATE__ veya __NEXT_DATA__
    patterns = [
        r'window\.__PRELOADED_STATE__\s*=\s*({.+?});',
        r'window\.__NEXT_DATA__\s*=\s*({.+?});',
        r'var\s+product\s*=\s*({.+?});',
        r'const\s+product\s*=\s*({.+?});',
        r'window\.productData\s*=\s*({.+?});',
    ]

    for pattern in patterns:
        match = re.search(pattern, html_text, re.DOTALL)
        if match:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)

                # Recursive olarak product bilgisini ara
                def find_product_data(obj, depth=0):
                    if depth > 5:  # Sonsuz loop önleme
                        return

                    if isinstance(obj, dict):
                        # Fiyat
                        for key in ['price', 'sellingPrice', 'salePrice', 'currentPrice']:
                            if key in obj and not result['price']:
                                try:
                                    result['price'] = float(obj[key])
                                except:
                                    pass

                        # Başlık
                        for key in ['name', 'title', 'productName']:
                            if key in obj and not result['title']:
                                result['title'] = str(obj[key])[:300]

                        # Marka
                        for key in ['brand', 'brandName', 'manufacturer']:
                            if key in obj and not result['brand']:
                                if isinstance(obj[key], dict):
                                    result['brand'] = obj[key].get('name', '')
                                else:
                                    result['brand'] = str(obj[key])

                        # Alt seviyeye in
                        for value in obj.values():
                            find_product_data(value, depth + 1)

                    elif isinstance(obj, list):
                        for item in obj:
                            find_product_data(item, depth + 1)

                find_product_data(data)

                if result['title'] or result['price']:
                    break  # Bulundu
            except:
                continue

    return result

def extract_html_elements(soup, url, html_text):
    """HTML elementlerinden + gizli JS verilerinden ürün bilgilerini çıkar"""
    result = {
        'title': '',
        'price': 0,
        'image_url': '',
        'brand': '',
        'specs': {}
    }

    domain = urlparse(url).netloc.lower()

    # ============ GİZLİ JS VERİLERİ (YENİ) ============
    hidden_data = extract_hidden_json_data(soup, html_text)
    result['title'] = hidden_data.get('title', '')
    result['price'] = hidden_data.get('price', 0)
    result['brand'] = hidden_data.get('brand', '')

    # ============ TITLE (GENİŞLETİLMİŞ) ============
    if not result['title']:
        title_selectors = [
            # Generic E-commerce
            'h1.product-name', 'h1.product-title', 'h1#productName',
            'h1[itemprop="name"]', '.product-name h1', '.pr-new-br h1',
            'h1.product_name', '.product-title h1', 'h1.pdp-title',
            'h1.product-detail-name', '[data-testid="product-name"]',
            '.product__title', '.prod-name', '.item-title',
            # WooCommerce
            '.product_title', 'h1.entry-title', '.summary h1',
            # Magento 2
            '.page-title-wrapper h1', '.product-info-main .page-title',
            '.product.attribute.overview', '.page-title', '.product-name',
            # PrestaShop
            'h1[itemprop="name"]', '.product-title', '#product-name',
            '.h1', '.product-name',
            # OpenCart
            '.product-title h1', '#content h1', '.product-info h1',
            # Shopware
            '.product-detail-name', '.product-name',
            # Custom & Fallback
            '.product-info h1', '.product-header h1', '.prod-title',
            'h1'
        ]

        for selector in title_selectors:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                result['title'] = el.get_text(strip=True)[:300]
                break

    # ============ PRICE (GENİŞLETİLMİŞ) ============
    if not result['price']:
        price_selectors = [
            # Generic E-commerce
            '.product-price', '.prc-dsc', '.price', '[data-test-id="price"]',
            '[data-testid="price"]', '[data-testid="product-price"]',
            '.product_price', '[itemprop="price"]', '.current-price',
            '.sale-price', '.pdp-price', '.price-value', '.product-detail-price',
            '.new-price', '.discount-price', '.sales-price', '.selling-price',
            '.price-current', '.product-price-value',
            # Magento 2
            '.price-box .price', '.special-price .price', '.final-price .price',
            '.price-wrapper .price', '.product-info-price .price',
            # PrestaShop
            '.product-price', '.current-price', 'span[itemprop="price"]',
            '.product-prices .price', '#our_price_display',
            # OpenCart
            '.product-price', '#price-special', '.price-new',
            '.price-tag', 'h2.price',
            # WooCommerce
            '.woocommerce-Price-amount', '.price ins .amount',
            'p.price', '.summary .price',
            # Shopware
            '.product-detail-price', '.price--default',
            # Trendyol/Hepsiburada specific
            '.prc-dsc', '.prc-slg', '.price-value',
            # Fallback
            '[class*="price"]', '[id*="price"]'
        ]

        for selector in price_selectors:
            el = soup.select_one(selector)
            if el:
                price_text = el.get_text(strip=True)
                # Fiyat temizleme (virgül ve nokta normalize et)
                price_clean = re.sub(r'[^\d,.]', '', price_text)
                price_clean = price_clean.replace('.', '').replace(',', '.')
                try:
                    price = float(price_clean)
                    if price > 0:
                        result['price'] = price
                        break
                except:
                    continue

    # ============ BRAND ============
    if not result['brand']:
        brand_selectors = [
            # Generic
            '[itemprop="brand"]', '.brand', '.product-brand',
            '.pr-new-br a', '.product_brand', '.brand-name',
            'a.product-brand', '.manufacturer', '[data-testid="brand"]',
            # Magento
            '.product-brand', '.brand-logo', '.product-manufacturer',
            # PrestaShop
            '#product_manufacturer', '.manufacturer-name',
            # OpenCart
            '.manufacturer', 'a[href*="manufacturer"]',
            # WooCommerce
            '.posted_in a', '.product-brands',
            # Trendyol/Hepsiburada
            '.product-brand a', '[data-test-id="brand"]',
            # Fallback
            '[class*="brand"]', '[class*="manufacturer"]'
        ]

        for selector in brand_selectors:
            el = soup.select_one(selector)
            if el:
                brand_text = el.get_text(strip=True) or el.get('content', '')
                if brand_text:
                    result['brand'] = brand_text[:100]
                    break

    # ============ IMAGE (Ayrı fonksiyonda) ============
    result['image_url'] = extract_image(soup, url, domain)

    # ============ SPECS TABLE ============
    # Trendyol tarzı
    spec_rows = soup.select('.product-feature-list li, .product-property-list li, .detail-attr-item')
    for row in spec_rows:
        spans = row.find_all('span')
        if len(spans) >= 2:
            key = spans[0].get_text(strip=True).lower().replace(' ', '_')
            val = spans[1].get_text(strip=True)
            if key and val:
                result['specs'][key] = val

    # dt/dd tarzı
    for dt in soup.select('dt, .spec-name, .spec-label, .property-name'):
        dd = dt.find_next_sibling(['dd', 'span', 'div'])
        if dd:
            key = dt.get_text(strip=True).lower().replace(' ', '_').replace(':', '')
            val = dd.get_text(strip=True)
            if key and val and len(key) < 50:
                result['specs'][key] = val

    # tr/td tarzı
    for row in soup.select('table tr, .spec-row, .feature-row'):
        cells = row.select('td, th')
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True).lower().replace(' ', '_').replace(':', '')
            val = cells[1].get_text(strip=True)
            if key and val and len(key) < 50:
                result['specs'][key] = val

    # li içinde : ile ayrılmış
    for li in soup.select('.product-features li, .features li, .spec-list li'):
        text = li.get_text(strip=True)
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip().lower().replace(' ', '_')
                val = parts[1].strip()
                if key and val and len(key) < 50:
                    result['specs'][key] = val

    return result

# ============================================
# 4. AKILLI KATEGORİ TESPİTİ (GENİŞLETİLMİŞ)
# ============================================
def detect_category_and_room(url, title, specs):
    """
    GENİŞLETİLMİŞ KELİME HAVUZU:
    - Baharatlık, Kavanoz, Saklama Kabı
    - Ajanda, Defter, Planlayıcı
    - Nevresim kumaş tipi (Saten, Pamuk, Ranforce)
    - Mobilya tipleri (3'lü, Köşe Takımı, Berjer)
    """
    url_lower = url.lower()
    title_lower = (title or '').lower()
    combined = url_lower + ' ' + title_lower

    # ============ BEYAZ EŞYA ============
    if any(x in combined for x in ['buzdolabı', 'buzdolabi', 'refrigerator', 'fridge']):
        return 'Beyaz Eşya', 'Buzdolabı', 'Mutfak'
    if any(x in combined for x in ['çamaşır', 'camasir', 'washing', 'washer']):
        return 'Beyaz Eşya', 'Çamaşır Makinesi', 'Banyo'
    if any(x in combined for x in ['bulaşık', 'bulasik', 'dishwasher']):
        return 'Beyaz Eşya', 'Bulaşık Makinesi', 'Mutfak'
    if any(x in combined for x in ['kurutma', 'dryer']):
        return 'Beyaz Eşya', 'Kurutma Makinesi', 'Banyo'
    if any(x in combined for x in ['fırın', 'firin', 'oven']):
        return 'Beyaz Eşya', 'Fırın', 'Mutfak'
    if any(x in combined for x in ['derin dondurucu', 'freezer']):
        return 'Beyaz Eşya', 'Derin Dondurucu', 'Mutfak'

    # ============ MUTFAK GEREÇİ (YENİ) ============
    if any(x in combined for x in ['baharatlık', 'baharatlik', 'spice rack']):
        return 'Mutfak Gereci', 'Düzenleyici', 'Mutfak'
    if any(x in combined for x in ['kavanoz', 'saklama kabı', 'saklama kabi', 'storage jar']):
        return 'Mutfak Gereci', 'Düzenleyici', 'Mutfak'
    if any(x in combined for x in ['blender', 'mikser', 'kahve makinesi', 'çay makinesi', 'cay makinesi', 'coffee maker', 'tea maker']):
        return 'Mutfak Gereci', 'Genel', 'Mutfak'

    # ============ OFİS/KIRTASIYE (YENİ) ============
    if any(x in combined for x in ['ajanda', 'defter', 'planlayıcı', 'planlayici', 'notebook', 'planner']):
        return 'Diğer', 'Kırtasiye', 'Çalışma Odası'

    # ============ MOBİLYA (GENİŞLETİLMİŞ) ============
    # Mobilya tipi tespiti (Regex ile)
    mobilya_match = re.search(REGEX_PATTERNS['mobilya_tipi'], title_lower, re.IGNORECASE)
    mobilya_tipi_ek = f" ({mobilya_match.group(1).title()})" if mobilya_match else ""

    if any(x in combined for x in ['koltuk', 'sofa', 'couch', 'berjer', 'chester', 'kanepe']):
        alt_kat = 'Koltuk Takımı' + mobilya_tipi_ek
        return 'Mobilya', alt_kat.strip(), 'Salon'
    if any(x in combined for x in ['masa', 'table', 'desk']):
        return 'Mobilya', 'Yemek Masası', 'Salon'
    if any(x in combined for x in ['dolap', 'cabinet', 'wardrobe']):
        return 'Mobilya', 'Dolap', 'Yatak Odası'
    if any(x in combined for x in ['tv ünitesi', 'tv-unitesi', 'tv unite', 'tv unit']):
        return 'Mobilya', 'TV Ünitesi', 'Salon'
    if any(x in combined for x in ['zigon', 'sehpa', 'coffee table']):
        return 'Mobilya', 'Zigon Sehpa', 'Salon'

    # ============ ELEKTRONİK ============
    if any(x in combined for x in ['televizyon', 'tv', 'led tv', 'smart tv']):
        return 'Elektronik', 'Televizyon', 'Salon'
    if any(x in combined for x in ['klima', 'air conditioner']):
        return 'Elektronik', 'Klima', 'Salon'
    if any(x in combined for x in ['laptop', 'notebook', 'bilgisayar', 'zenbook', 'macbook']):
        return 'Elektronik', 'Genel', 'Çalışma Odası'
    if any(x in combined for x in ['monitör', 'monitor']):
        return 'Elektronik', 'Genel', 'Çalışma Odası'

    # ============ TEKSTİL (GENİŞLETİLMİŞ - KUMAŞ TİPİ) ============
    if any(x in combined for x in ['yatak', 'mattress', 'bedding']):
        return 'Tekstil', 'Genel', 'Yatak Odası'

    # Nevresim - Kumaş tipi tespiti (YENİ)
    if any(x in combined for x in ['nevresim', 'pike', 'yorgan', 'duvet']):
        kumas_match = re.search(REGEX_PATTERNS['kumas_tipi'], title_lower, re.IGNORECASE)
        if kumas_match:
            kumas_tipi = kumas_match.group(1).title()
            return 'Tekstil', f'Nevresim Takımı ({kumas_tipi})', 'Yatak Odası'
        return 'Tekstil', 'Nevresim Takımı', 'Yatak Odası'

    # ============ KÜÇÜK EV ALETLERİ ============
    if any(x in combined for x in ['süpürge', 'supurge', 'vacuum', 'mop']):
        return 'Diğer', 'Genel', 'Diğer'

    # ============ BANYO ============
    if any(x in combined for x in ['lavabo', 'klozet', 'duş', 'dus', 'batarya', 'banyo']):
        return 'Banyo', 'Genel', 'Banyo'

    return 'Diğer', 'Genel', 'Salon'

# ============================================
# JSON-LD, META TAGS (Aynı)
# ============================================
def extract_json_ld(soup):
    """JSON-LD verilerinden ürün bilgilerini çıkar"""
    result = {
        'title': '',
        'price': 0,
        'image_url': '',
        'description': '',
        'brand': '',
        'sku': '',
        'gtin': '',
        'specs': {}
    }

    try:
        json_ld_scripts = soup.find_all('script', type='application/ld+json')

        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)

                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Product':
                            data = item
                            break
                    else:
                        continue

                if '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Product':
                            data = item
                            break
                    else:
                        continue

                if data.get('@type') not in ['Product', 'product', 'IndividualProduct']:
                    continue

                result['title'] = data.get('name', '') or result['title']
                result['description'] = data.get('description', '') or result['description']
                result['sku'] = data.get('sku', '') or data.get('mpn', '') or result['sku']
                result['gtin'] = data.get('gtin13', '') or data.get('gtin', '') or result['gtin']

                # Marka
                brand = data.get('brand', {})
                if isinstance(brand, dict):
                    result['brand'] = brand.get('name', '')
                elif isinstance(brand, str):
                    result['brand'] = brand

                # Resim
                image = data.get('image', '')
                if isinstance(image, list) and len(image) > 0:
                    result['image_url'] = image[0] if isinstance(image[0], str) else image[0].get('url', '')
                elif isinstance(image, str):
                    result['image_url'] = image
                elif isinstance(image, dict):
                    result['image_url'] = image.get('url', '')

                # Fiyat
                offers = data.get('offers', {})
                if isinstance(offers, list) and len(offers) > 0:
                    offers = offers[0]
                if isinstance(offers, dict):
                    price = offers.get('price', 0)
                    if price:
                        try:
                            result['price'] = float(str(price).replace(',', '.'))
                        except:
                            pass

                # Ek özellikler
                additional_props = data.get('additionalProperty', [])
                if isinstance(additional_props, list):
                    for prop in additional_props:
                        if isinstance(prop, dict):
                            name = prop.get('name', '').lower().replace(' ', '_')
                            value = prop.get('value', '')
                            if name and value:
                                result['specs'][name] = value

            except:
                continue
    except:
        pass

    return result

def extract_meta_tags(soup):
    """Meta etiketlerinden ürün bilgilerini çıkar"""
    result = {
        'title': '',
        'price': 0,
        'image_url': '',
        'description': '',
        'brand': ''
    }

    try:
        # OG Tags
        og_title = soup.find('meta', property='og:title')
        if og_title:
            result['title'] = og_title.get('content', '').split('|')[0].strip()

        og_image = soup.find('meta', property='og:image')
        if og_image:
            result['image_url'] = og_image.get('content', '')

        og_description = soup.find('meta', property='og:description')
        if og_description:
            result['description'] = og_description.get('content', '')

        # Product meta tags
        product_price = soup.find('meta', property='product:price:amount')
        if product_price:
            try:
                result['price'] = float(product_price.get('content', '0').replace(',', '.'))
            except:
                pass

        product_brand = soup.find('meta', property='product:brand')
        if product_brand:
            result['brand'] = product_brand.get('content', '')

        # Twitter cards
        if not result['title']:
            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            if twitter_title:
                result['title'] = twitter_title.get('content', '')
    except:
        pass

    return result

def extract_with_regex(soup, title='', existing_specs=None):
    """Regex ile teknik özellik çıkar (aynı)"""
    if existing_specs is None:
        existing_specs = {}

    specs = existing_specs.copy()
    text = soup.get_text(separator=' ', strip=True).lower()

    # Boyut
    if 'boyut' not in specs and 'olculer' not in specs:
        match = re.search(REGEX_PATTERNS['boyut_wxhxd'], text, re.IGNORECASE)
        if match:
            w, h, d = match.groups()
            specs['olculer'] = f"{w}x{h}x{d} cm"

    # Kapasite
    if 'kapasite' not in specs:
        match = re.search(REGEX_PATTERNS['kapasite_litre'], text, re.IGNORECASE)
        if match:
            specs['kapasite_lt'] = f"{match.group(1)} L"

    # Enerji sınıfı
    if 'enerji_sinifi' not in specs:
        match = re.search(REGEX_PATTERNS['enerji_sinifi'], text, re.IGNORECASE)
        if match:
            specs['enerji_sinifi'] = match.group(1).upper()

    # Devir
    if 'devir' not in specs:
        match = re.search(REGEX_PATTERNS['devir'], text, re.IGNORECASE)
        if match:
            specs['devir_sayisi'] = f"{match.group(1)} rpm"

    # Kumaş tipi (YENİ)
    if 'kumas_tipi' not in specs:
        match = re.search(REGEX_PATTERNS['kumas_tipi'], text, re.IGNORECASE)
        if match:
            specs['kumas_tipi'] = match.group(1).title()

    return specs

# ============================================
# DEBUG UTILITIES
# ============================================
def save_debug_html(url, html_content, soup):
    """
    Debug için HTML'i dosyaya kaydet

    Args:
        url: Ürün URL'i
        html_content: HTML içeriği
        soup: BeautifulSoup objesi

    Returns:
        str: Kaydedilen dosya yolu
    """
    try:
        from pathlib import Path
        from datetime import datetime
        import os

        # Debug dizini oluştur
        debug_dir = Path('debug_html')
        debug_dir.mkdir(exist_ok=True)

        # Dosya adı oluştur
        domain = urlparse(url).netloc.replace('www.', '').replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_{timestamp}.html"
        filepath = debug_dir / filename

        # HTML'i kaydet
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"💾 HTML saved to: {filepath}")

        # Platform tespit bilgilerini ayrı dosyaya yaz
        info_file = debug_dir / f"{domain}_{timestamp}_info.txt"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"Timestamp: {timestamp}\n\n")

            f.write("="*50 + "\n")
            f.write("PLATFORM DETECTION MARKERS\n")
            f.write("="*50 + "\n\n")

            # Shopify marker
            f.write(f"[Shopify] /products/ in URL: {'/products/' in url}\n")

            # Akinon marker
            has_akinon = 'js-datalayer-group-item' in html_content or 'akinoncloud.com' in html_content
            f.write(f"[Akinon] Marker found: {has_akinon}\n")

            # JSON-LD count
            jsonld_count = len(soup.find_all('script', type='application/ld+json'))
            f.write(f"[JSON-LD] Script count: {jsonld_count}\n")

            # Next.js
            has_nextjs = soup.find('script', id='__NEXT_DATA__') is not None
            f.write(f"[Next.js] __NEXT_DATA__ found: {has_nextjs}\n")

            # dataLayer
            has_datalayer = 'datalayer' in html_content.lower()
            f.write(f"[dataLayer] GTM found: {has_datalayer}\n")

            # WooCommerce
            has_woo = 'woocommerce' in html_content.lower()
            f.write(f"[WooCommerce] Marker found: {has_woo}\n")

            f.write("\n" + "="*50 + "\n")
            f.write("META TAGS\n")
            f.write("="*50 + "\n\n")

            for meta in soup.find_all('meta')[:20]:
                prop = meta.get('property') or meta.get('name')
                content = meta.get('content', '')[:100]
                if prop:
                    f.write(f"{prop}: {content}\n")

        logger.info(f"📝 Debug info saved to: {info_file}")

        print(f"\n{'='*60}")
        print(f"💾 DEBUG FILES SAVED")
        print(f"{'='*60}")
        print(f"HTML: {filepath}")
        print(f"Info: {info_file}")
        print(f"\n💡 NEXT STEPS:")
        print(f"1. Open {filepath} in browser")
        print(f"2. Check {info_file} for platform markers")
        print(f"3. Search HTML for product data (price, title, etc.)")
        print(f"{'='*60}\n")

        return str(filepath)

    except Exception as e:
        logger.error(f"Failed to save debug HTML: {e}")
        return None


# ============================================
# 5. USER-AGENT ROTASYONU VE RETRY
# ============================================
def fetch_with_retry(url, max_retries=3, use_cloudscraper=False, timeout=30):
    """
    Cloudflare bypass ile retry mekanizması

    Args:
        url: Fetch edilecek URL
        max_retries: Maksimum deneme sayısı
        use_cloudscraper: Cloudscraper kullan (Cloudflare bypass için)
        timeout: Timeout süresi (saniye)

    Returns:
        (response, error): Response objesi ve hata mesajı
    """
    # Cloudscraper kullanılacaksa ve mevcut değilse uyar
    if use_cloudscraper and not CLOUDSCRAPER_AVAILABLE:
        logger.warning("Cloudscraper istendi ama yüklü değil, normal requests kullanılacak")
        use_cloudscraper = False

    for attempt in range(max_retries):
        headers = USER_AGENTS[attempt % len(USER_AGENTS)].copy()

        try:
            if use_cloudscraper and CLOUDSCRAPER_AVAILABLE:
                # Cloudscraper kullan
                scraper = cloudscraper.create_scraper(
                    browser={
                        'browser': 'chrome',
                        'platform': 'windows',
                        'desktop': True
                    },
                    delay=3
                )
                response = scraper.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            else:
                # Normal requests kullan
                session = requests.Session()
                session.trust_env = False
                response = session.get(url, headers=headers, timeout=timeout, allow_redirects=True, proxies={})

            # 403/503 hatası
            if response.status_code in [403, 503]:
                logger.warning(f"HTTP {response.status_code} - Attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(2 + attempt)  # Progressive delay
                    continue
                return None, f'HTTP hatası: {response.status_code} (Bot koruması)'

            response.raise_for_status()

            # Encoding düzelt
            if response.encoding in ['ISO-8859-1', 'ISO-8859-9', None]:
                response.encoding = 'utf-8'

            return response, None

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout - Attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None, 'Site yanıt vermedi (timeout)'

        except Exception as e:
            logger.error(f"Error: {type(e).__name__}: {str(e)[:100]}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None, f'Bağlantı hatası: {str(e)}'

    return None, 'Maksimum deneme sayısı aşıldı'

# ============================================
# PLATFORM TESPİT SİSTEMİ
# ============================================
def detect_ecommerce_platform(url, html_content, soup=None):
    """
    E-ticaret platformunu otomatik tespit eder

    Args:
        url: Ürün URL'i
        html_content: HTML içeriği
        soup: BeautifulSoup objesi (opsiyonel, yoksa oluşturulur)

    Returns:
        tuple: (platform_name, detection_reason)
        Platformlar: 'shopify', 'akinon', 'jsonld', 'nextjs', 'datalayer', 'woocommerce', 'meta_html'
    """
    if soup is None:
        soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Shopify testi - /products/ içeren URL'ler için JSON endpoint kontrolü
    if '/products/' in url:
        try:
            # URL'den handle çıkar
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            if 'products' in path_parts:
                idx = path_parts.index('products')
                if idx + 1 < len(path_parts):
                    handle = path_parts[idx + 1].split('?')[0]
                    json_url = f"{parsed.scheme}://{parsed.netloc}/products/{handle}.json"

                    # HEAD request ile kontrol et
                    try:
                        resp = requests.head(json_url, timeout=5, allow_redirects=True)
                        if resp.status_code == 200:
                            logger.info(f"✓ Shopify platform detected: {json_url} endpoint exists")
                            return ('shopify', 'JSON endpoint available')
                    except:
                        pass
        except Exception as e:
            logger.debug(f"Shopify test error: {e}")

    # 2. Akinon platform testi
    if 'js-datalayer-group-item' in html_content or 'akinoncloud.com' in html_content:
        logger.info("✓ Akinon platform detected: marker classes found")
        return ('akinon', 'Akinon marker detected')

    # 3. JSON-LD schema testi
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            # @type kontrolü
            if isinstance(data, dict):
                if data.get('@type') == 'Product':
                    logger.info("✓ JSON-LD platform detected: Product schema found")
                    return ('jsonld', 'Product schema in JSON-LD')
                # @graph içinde Product ara
                if '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Product':
                            logger.info("✓ JSON-LD platform detected: Product in @graph")
                            return ('jsonld', 'Product in @graph')
        except:
            continue

    # 4. Next.js testi
    nextjs_script = soup.find('script', id='__NEXT_DATA__')
    if nextjs_script:
        logger.info("✓ Next.js platform detected: __NEXT_DATA__ found")
        return ('nextjs', '__NEXT_DATA__ script found')

    # 5. dataLayer testi
    if re.search(r'dataLayer\.push|var dataLayer|window\.dataLayer', html_content):
        logger.info("✓ DataLayer platform detected: dataLayer pattern found")
        return ('datalayer', 'dataLayer variables found')

    # 6. WooCommerce testi
    if 'woocommerce' in html_content.lower() or 'wp-content/plugins/woocommerce' in html_content:
        logger.info("✓ WooCommerce platform detected: WooCommerce markers found")
        return ('woocommerce', 'WooCommerce detected')

    # 7. Fallback - Meta/HTML
    logger.info("⚡ No specific platform detected, using meta_html fallback")
    return ('meta_html', 'Generic fallback')


def scrape_jsonld_from_soup(soup, url):
    """
    JSON-LD schema'dan ürün bilgilerini çıkarır

    Args:
        soup: BeautifulSoup objesi
        url: Ürün URL'i

    Returns:
        dict veya None: Ürün bilgileri
    """
    try:
        json_ld_scripts = soup.find_all('script', type='application/ld+json')

        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                product_data = None

                # Direct Product
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    product_data = data
                # Product in @graph
                elif isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Product':
                            product_data = item
                            break

                if product_data:
                    # Offers bilgilerini çıkar
                    offers = product_data.get('offers', {})
                    if isinstance(offers, list) and len(offers) > 0:
                        offers = offers[0]

                    price = 0
                    if offers.get('price'):
                        try:
                            price = float(offers['price'])
                        except:
                            price = 0

                    # Image URL
                    image_url = ''
                    if 'image' in product_data:
                        img = product_data['image']
                        if isinstance(img, list):
                            image_url = img[0] if img else ''
                        elif isinstance(img, dict):
                            image_url = img.get('url', '')
                        else:
                            image_url = str(img)

                    result = {
                        'title': product_data.get('name', ''),
                        'price': price,
                        'brand': product_data.get('brand', {}).get('name', '') if isinstance(product_data.get('brand'), dict) else str(product_data.get('brand', '')),
                        'description': product_data.get('description', ''),
                        'image_url': image_url,
                        'sku': product_data.get('sku', ''),
                        'category': product_data.get('category', ''),
                    }

                    logger.info(f"✓ JSON-LD parsed: {result['title'][:50]}... - {result['price']} TL")
                    return result

            except Exception as e:
                logger.debug(f"JSON-LD parse error: {e}")
                continue

        return None

    except Exception as e:
        logger.error(f"✗ JSON-LD extraction failed: {e}")
        return None


def scrape_datalayer_from_soup(soup, url, html_content):
    """
    dataLayer değişkenlerinden ürün bilgilerini çıkarır

    Args:
        soup: BeautifulSoup objesi
        url: Ürün URL'i
        html_content: HTML içeriği

    Returns:
        dict veya None: Ürün bilgileri
    """
    try:
        # dataLayer pattern'lerini ara
        patterns = [
            r'dataLayer\.push\((\{[^}]+\})\)',
            r'var dataLayer = (\[.+?\]);',
            r'window\.dataLayer = (\[.+?\]);',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)

                    # Array ise ilk elementi al
                    if isinstance(data, list) and len(data) > 0:
                        data = data[0]

                    # ecommerce.detail.products yapısını ara
                    product_data = None
                    if 'ecommerce' in data:
                        ecom = data['ecommerce']
                        if 'detail' in ecom and 'products' in ecom['detail']:
                            products = ecom['detail']['products']
                            if isinstance(products, list) and len(products) > 0:
                                product_data = products[0]
                        elif 'products' in ecom:
                            products = ecom['products']
                            if isinstance(products, list) and len(products) > 0:
                                product_data = products[0]

                    if product_data:
                        result = {
                            'title': product_data.get('name', ''),
                            'price': float(product_data.get('price', 0)),
                            'brand': product_data.get('brand', ''),
                            'category': product_data.get('category', ''),
                            'image_url': product_data.get('image', ''),
                        }

                        logger.info(f"✓ DataLayer parsed: {result['title'][:50]}... - {result['price']} TL")
                        return result

                except Exception as e:
                    logger.debug(f"DataLayer parse attempt failed: {e}")
                    continue

        # Bulunamadıysa meta_html fallback
        logger.info("⚡ DataLayer not found, falling back to meta_html")
        return scrape_meta_html_from_soup(soup, url)

    except Exception as e:
        logger.error(f"✗ DataLayer extraction failed: {e}")
        return None


def scrape_nextjs_from_soup(soup, url):
    """
    Next.js __NEXT_DATA__ script'inden ürün bilgilerini çıkarır

    Args:
        soup: BeautifulSoup objesi
        url: Ürün URL'i

    Returns:
        dict veya None: Ürün bilgileri
    """
    try:
        nextjs_script = soup.find('script', id='__NEXT_DATA__')
        if not nextjs_script:
            return None

        data = json.loads(nextjs_script.string)

        # Yaygın Next.js yapıları
        product_data = None

        # props.pageProps.product
        if 'props' in data and 'pageProps' in data['props']:
            page_props = data['props']['pageProps']
            if 'product' in page_props:
                product_data = page_props['product']
            elif 'productData' in page_props:
                product_data = page_props['productData']
            elif 'initialData' in page_props and 'product' in page_props['initialData']:
                product_data = page_props['initialData']['product']

        if product_data:
            result = {
                'title': product_data.get('name', '') or product_data.get('title', ''),
                'price': float(product_data.get('price', 0)),
                'brand': product_data.get('brand', ''),
                'description': product_data.get('description', ''),
                'image_url': product_data.get('image', '') or product_data.get('imageUrl', ''),
            }

            logger.info(f"✓ Next.js parsed: {result['title'][:50]}... - {result['price']} TL")
            return result

        return None

    except Exception as e:
        logger.error(f"✗ Next.js extraction failed: {e}")
        return None


def scrape_woocommerce_from_soup(soup, url):
    """
    WooCommerce sitelerinden ürün bilgilerini çıkarır

    Args:
        soup: BeautifulSoup objesi
        url: Ürün URL'i

    Returns:
        dict veya None: Ürün bilgileri
    """
    try:
        # Title selectors
        title = ''
        title_selectors = [
            'h1.product_title',
            'h1.product-title',
            '.product-name',
            'h1[itemprop="name"]',
        ]
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break

        # Price selectors
        price = 0
        price_selectors = [
            '.price .woocommerce-Price-amount',
            '.woocommerce-Price-amount.amount',
            'p.price',
            '.price ins .amount',
            '[itemprop="price"]',
        ]
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                # Sadece sayıları çıkar
                price_match = re.search(r'[\d,.]+', price_text.replace('.', '').replace(',', '.'))
                if price_match:
                    try:
                        price = float(price_match.group(0))
                        break
                    except:
                        pass

        # Image
        image_url = ''
        img_selectors = [
            '.woocommerce-product-gallery__image img',
            '.product-images img',
            'img.wp-post-image',
        ]
        for selector in img_selectors:
            elem = soup.select_one(selector)
            if elem:
                image_url = elem.get('src', '') or elem.get('data-src', '')
                if image_url:
                    break

        if title and price:
            result = {
                'title': title,
                'price': price,
                'image_url': image_url,
                'brand': '',
            }
            logger.info(f"✓ WooCommerce parsed: {result['title'][:50]}... - {result['price']} TL")
            return result

        return None

    except Exception as e:
        logger.error(f"✗ WooCommerce extraction failed: {e}")
        return None


def scrape_meta_html_from_soup(soup, url):
    """
    Meta tag'ler ve HTML selector'lardan ürün bilgilerini çıkarır (Generic fallback)

    Args:
        soup: BeautifulSoup objesi
        url: Ürün URL'i

    Returns:
        dict veya None: Ürün bilgileri
    """
    try:
        # Meta tags
        title = ''
        price = 0
        image_url = ''
        brand = ''
        description = ''

        # Title
        og_title = soup.find('meta', property='og:title')
        if og_title:
            title = og_title.get('content', '')
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)

        # Price
        price_meta = soup.find('meta', property='og:price:amount')
        if price_meta:
            try:
                price = float(price_meta.get('content', 0))
            except:
                pass

        # Image
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image_url = og_image.get('content', '')

        # Brand
        brand_meta = soup.find('meta', property='product:brand')
        if brand_meta:
            brand = brand_meta.get('content', '')

        # Description
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            description = og_desc.get('content', '')

        # HTML fallback - title
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)

        # HTML fallback - price (yaygın class'lar)
        if not price:
            price_selectors = [
                '.price', '.product-price', '.price-tag',
                '[class*="price"]', '[id*="price"]'
            ]
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.get_text(strip=True)
                    price_match = re.search(r'[\d,.]+', price_text.replace('.', '').replace(',', '.'))
                    if price_match:
                        try:
                            price = float(price_match.group(0))
                            break
                        except:
                            pass

        result = {
            'title': title,
            'price': price,
            'image_url': image_url,
            'brand': brand,
            'description': description,
        }

        logger.info(f"✓ Meta/HTML parsed: {result['title'][:50]}... - {result['price']} TL")
        return result

    except Exception as e:
        logger.error(f"✗ Meta/HTML extraction failed: {e}")
        return None


# ============================================
# ANA FONKSİYON - YENİ MİMARİ v3.0
# ============================================
def scrape_product(url):
    """
    YENİ MİMARİ v3.0 - Otomatik Platform Tespit Sistemi

    Artık her yeni site için manuel konfigürasyon gerekmez!
    Sistem otomatik olarak platformu tespit edip uygun parser'ı kullanır.

    3 Aşamalı Mimari:
    1. Bilinen siteler → Hızlı yönlendirme
    2. Bilinmeyen siteler → Otomatik platform tespiti
    3. Platform-handler routing → Uygun parser çağrısı

    Returns:
        dict: {
            'success': bool,
            'data': {...},
            'error': str
        }
    """
    try:
        logger.info(f"═══ Starting scrape for {url} ═══")
        # 0. CACHE KONTROLÜ
        cached_result = get_from_cache(url)
        if cached_result:
            return cached_result

        # Cache temizliği (her 10 istekten birinde)
        import random
        if random.randint(1, 10) == 1:
            clear_expired_cache()

        # 1. MOBİL URL NORMALİZASYONU
        normalized_url, was_mobile = normalize_mobile_url(url)

        # Rate limiting - domain bazlı
        domain = urlparse(normalized_url).netloc.lower()
        wait_for_rate_limit(domain)

        # ============ AŞAMA 1: BİLİNEN SİTELER - HIZLI YÖNLENDİRME ============
        # Bilinen siteler için domain → (name, type) mapping
        KNOWN_SITES = {
            'trendyol.com': ('trendyol', 'api'),
            'hepsiburada.com': ('hepsiburada', 'jsonld'),
            'karaca.com': ('karaca', 'datalayer'),
            'ikea.com': ('ikea', 'ikea'),
            'enzahome.com': ('enzahome', 'akinon'),
            'alfemo.com': ('alfemo', 'akinon'),
            'istikbal.com': ('istikbal', 'akinon'),
            'bellona.com': ('bellona', 'akinon'),
        }

        # Cloudflare korumalı siteler
        cloudflare_sites = ['hepsiburada.com', 'ikea.com', 'karaca.com', 'vatan.com',
                            'teknosa.com', 'mediamarkt.com.tr', 'n11.com', 'ciceksepeti.com']

        # Domain kontrolü
        is_known_site = False
        handler_name = None
        handler_type = None

        for site_domain, (name, htype) in KNOWN_SITES.items():
            if site_domain in domain:
                is_known_site = True
                handler_name = name
                handler_type = htype
                logger.info(f"✓ Known site detected: {handler_name} (type: {handler_type})")
                break

        site_specific_data = None
        parser_error = None
        detected_platform = None
        soup = None
        html_text = None
        session = None

        # BİLİNEN SİTE - Direkt handler çağır
        if is_known_site:
            try:
                # Cloudflare kontrolü
                use_cf = any(site in domain for site in cloudflare_sites)
                timeout = 30 if 'ikea' in domain else 20

                # Handler type'a göre çağır
                if handler_type == 'api':
                    # Trendyol API
                    session = requests.Session()
                    session.trust_env = False
                    site_specific_data = scrape_api_trendyol(normalized_url, session)

                elif handler_type == 'jsonld':
                    # Hepsiburada JSON-LD
                    site_specific_data = scrape_hepsiburada(normalized_url, use_cloudscraper=True)

                elif handler_type == 'datalayer':
                    # Karaca dataLayer
                    response, error = fetch_with_retry(normalized_url, use_cloudscraper=True, timeout=20)
                    if not response or response.status_code != 200:
                        logger.error(f"✗ Failed to fetch {normalized_url}: {error}")
                        return {'success': False, 'error': error or 'Bilinmeyen hata'}
                    soup = BeautifulSoup(response.content, 'html.parser')
                    html_text = response.text
                    site_specific_data = scrape_datalayer_karaca(normalized_url, soup, html_text, use_cloudscraper=True)

                elif handler_type == 'ikea':
                    # IKEA özel parser
                    response, error = fetch_with_retry(normalized_url, use_cloudscraper=True, timeout=30)
                    if not response or response.status_code != 200:
                        logger.error(f"✗ Failed to fetch {normalized_url}: {error}")
                        return {'success': False, 'error': error or 'Bilinmeyen hata'}
                    soup = BeautifulSoup(response.content, 'html.parser')
                    site_specific_data = scrape_ikea(normalized_url, soup, use_cloudscraper=True)

                elif handler_type == 'akinon':
                    # Akinon platform (Enza, Alfemo, İstikbal, Bellona)
                    site_specific_data = scrape_enza_akinon(normalized_url, use_cloudscraper=False)

                logger.info(f"→ Used {handler_name} handler (type: {handler_type})")

            except Exception as e:
                parser_error = f"{handler_name} handler error: {str(e)}"
                logger.error(f"✗ {parser_error}")
                import traceback
                logger.debug(traceback.format_exc())

        # ============ AŞAMA 2: BİLİNMEYEN SİTELER - OTOMATIK PLATFORM TESPİTİ ============
        else:
            logger.info("⚡ Unknown site - starting automatic platform detection...")

            try:
                # Fetch HTML
                use_cf = any(site in domain for site in cloudflare_sites)
                timeout = 30 if 'ikea' in domain else 20
                response, error = fetch_with_retry(normalized_url, use_cloudscraper=use_cf, timeout=timeout)

                # Mobil fallback
                if not response and was_mobile:
                    response, error = fetch_with_retry(url, use_cloudscraper=use_cf, timeout=timeout)
                    if response:
                        normalized_url = url

                if not response or response.status_code != 200:
                    logger.error(f"✗ Failed to fetch {normalized_url}: {error}")
                    return {'success': False, 'error': error or 'Bilinmeyen hata'}

                soup = BeautifulSoup(response.content, 'html.parser')
                html_text = response.text

                # Platform tespit et
                detected_platform, detection_reason = detect_ecommerce_platform(normalized_url, html_text, soup)
                logger.info(f"✓ Platform detected: {detected_platform} ({detection_reason})")

                # DEBUG MODE: HTML kaydet
                import os
                if os.environ.get('SCRAPER_DEBUG') == 'true':
                    save_debug_html(normalized_url, html_text, soup)

                    # Detaylı platform bilgisi
                    print(f"\n{'='*60}")
                    print(f"🔍 PLATFORM DETECTION DEBUG")
                    print(f"{'='*60}")
                    print(f"URL: {normalized_url}")
                    print(f"Domain: {domain}")
                    print(f"Detected Platform: {detected_platform}")
                    print(f"Detection Reason: {detection_reason}")
                    print(f"Cloudscraper Used: {use_cf}")
                    print(f"{'='*60}\n")

                # ============ AŞAMA 3: PLATFORM-HANDLER ROUTING ============
                logger.info(f"→ Routing to {detected_platform} handler...")

                try:
                    if detected_platform == 'shopify':
                        site_specific_data = scrape_shopify(normalized_url)

                    elif detected_platform == 'akinon':
                        site_specific_data = scrape_enza_akinon(normalized_url, use_cloudscraper=use_cf)

                    elif detected_platform == 'jsonld':
                        site_specific_data = scrape_jsonld_from_soup(soup, normalized_url)

                    elif detected_platform == 'nextjs':
                        site_specific_data = scrape_nextjs_from_soup(soup, normalized_url)

                    elif detected_platform == 'datalayer':
                        site_specific_data = scrape_datalayer_from_soup(soup, normalized_url, html_text)

                    elif detected_platform == 'woocommerce':
                        site_specific_data = scrape_woocommerce_from_soup(soup, normalized_url)

                    elif detected_platform == 'meta_html':
                        site_specific_data = scrape_meta_html_from_soup(soup, normalized_url)

                    if site_specific_data:
                        logger.info(f"✓ {detected_platform} handler succeeded")
                    else:
                        logger.warning(f"⚠ {detected_platform} handler returned None, will use fallback")

                        # DEBUG MODE: Parser failure analysis
                        import os
                        import re
                        if os.environ.get('SCRAPER_DEBUG') == 'true':
                            print(f"\n{'='*60}")
                            print(f"⚠️  PARSER FAILURE ANALYSIS")
                            print(f"{'='*60}")
                            print(f"Handler: {detected_platform}")
                            print(f"Trying fallback chain...")

                            # JSON-LD kontrol
                            jsonld_scripts = soup.find_all('script', type='application/ld+json')
                            print(f"\nJSON-LD scripts: {len(jsonld_scripts)}")
                            for i, script in enumerate(jsonld_scripts[:3]):
                                try:
                                    import json
                                    data = json.loads(script.string)
                                    print(f"  Script {i+1} @type: {data.get('@type')}")
                                except:
                                    print(f"  Script {i+1}: Parse error")

                            # dataLayer kontrol
                            has_datalayer = 'datalayer' in html_text.lower()
                            print(f"\ndataLayer found: {has_datalayer}")
                            if has_datalayer:
                                patterns = re.findall(r'dataLayer\.push\(', html_text)
                                print(f"  dataLayer.push calls: {len(patterns)}")

                            # Meta tags
                            print(f"\nMeta tags:")
                            og_title = soup.find('meta', property='og:title')
                            print(f"  og:title: {og_title.get('content', 'N/A')[:50] if og_title else 'NOT FOUND'}")
                            og_price = soup.find('meta', property='og:price:amount')
                            print(f"  og:price:amount: {og_price.get('content', 'N/A') if og_price else 'NOT FOUND'}")
                            print(f"{'='*60}\n")

                except Exception as e:
                    parser_error = f"{detected_platform} handler error: {str(e)}"
                    logger.error(f"✗ {parser_error}")
                    import traceback
                    logger.debug(traceback.format_exc())

            except Exception as e:
                parser_error = f"Platform detection failed: {str(e)}"
                logger.error(f"✗ {parser_error}")
                import traceback
                logger.debug(traceback.format_exc())

        # ============ SOUP OLUŞTUR (Eğer henüz yoksa) ============
        # Bazı handler'lar fetch yapmadığı için soup yoksa oluştur
        if soup is None:
            use_cf = any(site in domain for site in cloudflare_sites)
            timeout = 30 if 'ikea' in domain else 20
            response, error = fetch_with_retry(normalized_url, use_cloudscraper=use_cf, timeout=timeout)

            if not response and was_mobile:
                response, error = fetch_with_retry(url, use_cloudscraper=use_cf, timeout=timeout)
                if response:
                    normalized_url = url

            if not response or response.status_code != 200:
                logger.error(f"✗ Failed to fetch {normalized_url}: {error}")
                return {'success': False, 'error': error or 'Bilinmeyen hata'}

            soup = BeautifulSoup(response.content, 'html.parser')
            html_text = response.text

        # ============ VERİ ÇIKARMA (FALLBACK CHAIN) ============
        json_ld_data = extract_json_ld(soup)
        meta_data = extract_meta_tags(soup)
        hidden_json_data = extract_hidden_json_data(soup, html_text) or {}
        html_data = extract_html_elements(soup, normalized_url, html_text)

        # Handler bilgisi (logging için)
        handler = handler_name if is_known_site else detected_platform
        parser_used = handler

        # Birleştir (Öncelik: Site-Specific > JSON-LD > Hidden JSON > Meta > HTML)
        special_data = site_specific_data or {}

        # Fallback chain tracking
        data_sources = {
            'title': None,
            'price': None,
            'image_url': None,
            'brand': None,
            'description': None
        }

        # Title fallback (Öncelik: Site-Specific > JSON-LD > Hidden JSON > Meta > HTML)
        title = (special_data.get('title', '') or
                 json_ld_data['title'] or
                 hidden_json_data.get('title', '') or
                 meta_data['title'] or
                 html_data['title'])
        if special_data.get('title'):
            data_sources['title'] = handler
        elif json_ld_data['title']:
            data_sources['title'] = 'json-ld'
        elif hidden_json_data.get('title'):
            data_sources['title'] = 'hidden-json'
        elif meta_data['title']:
            data_sources['title'] = 'meta-tags'
        elif html_data['title']:
            data_sources['title'] = 'html-selectors'

        # Price fallback
        price = (special_data.get('price', 0) or
                 json_ld_data['price'] or
                 hidden_json_data.get('price', 0) or
                 meta_data['price'] or
                 html_data['price'])
        if special_data.get('price', 0):
            data_sources['price'] = handler
        elif json_ld_data['price']:
            data_sources['price'] = 'json-ld'
        elif hidden_json_data.get('price'):
            data_sources['price'] = 'hidden-json'
        elif meta_data['price']:
            data_sources['price'] = 'meta-tags'
        elif html_data['price']:
            data_sources['price'] = 'html-selectors'

        # Image URL fallback
        image_url = (special_data.get('image_url', '') or
                     json_ld_data['image_url'] or
                     hidden_json_data.get('image_url', '') or
                     meta_data['image_url'] or
                     html_data['image_url'])
        if special_data.get('image_url'):
            data_sources['image_url'] = handler
        elif json_ld_data['image_url']:
            data_sources['image_url'] = 'json-ld'
        elif hidden_json_data.get('image_url'):
            data_sources['image_url'] = 'hidden-json'
        elif meta_data['image_url']:
            data_sources['image_url'] = 'meta-tags'
        elif html_data['image_url']:
            data_sources['image_url'] = 'html-selectors'

        # Brand fallback
        brand = (special_data.get('brand', '') or
                 json_ld_data['brand'] or
                 hidden_json_data.get('brand', '') or
                 meta_data['brand'] or
                 html_data['brand'])
        if special_data.get('brand'):
            data_sources['brand'] = handler
        elif json_ld_data['brand']:
            data_sources['brand'] = 'json-ld'
        elif hidden_json_data.get('brand'):
            data_sources['brand'] = 'hidden-json'
        elif meta_data['brand']:
            data_sources['brand'] = 'meta-tags'
        elif html_data['brand']:
            data_sources['brand'] = 'html-selectors'

        # Description fallback
        description = (special_data.get('description', '') or
                      json_ld_data['description'] or
                      hidden_json_data.get('description', '') or
                      meta_data['description'])
        if special_data.get('description'):
            data_sources['description'] = handler
        elif json_ld_data['description']:
            data_sources['description'] = 'json-ld'
        elif hidden_json_data.get('description'):
            data_sources['description'] = 'hidden-json'
        elif meta_data['description']:
            data_sources['description'] = 'meta-tags'

        result = {
            'title': title,
            'price': price,
            'image_url': image_url,
            'brand': brand,
            'description': description,
            'link': normalized_url,
            'sku': json_ld_data['sku'],
            'gtin': json_ld_data['gtin'],
            'specs': {}
        }

        # Specs birleştir
        all_specs = {}
        all_specs.update(json_ld_data.get('specs', {}))
        all_specs.update(html_data.get('specs', {}))

        # Regex madenciliği
        all_specs = extract_with_regex(soup, result['title'], all_specs)

        # Kategori ve Oda tahmini
        kategori, alt_kategori, oda = detect_category_and_room(normalized_url, result['title'], all_specs)

        result['kategori_tahmini'] = kategori
        result['alt_kategori_tahmini'] = alt_kategori
        result['oda_tahmini'] = oda
        result['specs'] = {k: v for k, v in all_specs.items() if not k.startswith('_')}

        # Marka yoksa domain'den tahmin
        if not result['brand']:
            brand_map = {
                'samsung': 'Samsung',
                'arcelik': 'Arçelik',
                'beko': 'Beko',
                'enzahome': 'Enza Home',
                'yatas': 'Yataş',
                'bellona': 'Bellona',
                'ikea': 'IKEA',
            }
            for key, value in brand_map.items():
                if key in domain:
                    result['brand'] = value
                    break

        # Debug metadata (sadece debug modunda göster)
        debug_info = {
            'handler': handler,
            'parser_used': parser_used,
            'data_sources': data_sources,
        }
        if parser_error:
            debug_info['parser_error'] = parser_error

        # Debug modunda metadata ekle
        import os
        if os.environ.get('SCRAPER_DEBUG') == 'true':
            result['_debug'] = debug_info
            print(f"\n{'='*50}")
            print(f"🔍 SCRAPING DEBUG INFO")
            print(f"{'='*50}")
            print(f"Domain: {domain}")
            print(f"Handler: {handler}")
            if parser_error:
                print(f"⚠️  Parser Error: {parser_error}")
            print(f"\nData Sources:")
            for field, source in data_sources.items():
                if source:
                    print(f"  • {field}: {source}")
            print(f"{'='*50}\n")

        # Sonucu cache'e kaydet
        final_result = {
            'success': True,
            'data': result
        }
        save_to_cache(url, final_result)

        return final_result

    except Exception as e:
        return {'success': False, 'error': f'Beklenmeyen hata: {str(e)}'}

# ============================================
# TEST
# ============================================
# ============================================
# MAIN - CLI INTERFACE
# ============================================
if __name__ == '__main__':
    """
    USAGE EXAMPLES:
    ===============

    # Normal scraping
    python scraper.py --url "https://www.trendyol.com/product/..."

    # Debug mode (detailed logging + HTML save)
    python scraper.py --url "https://unknown-site.com/product/123" --debug

    # Run all tests
    python scraper.py --test

    # Debug mode + tests
    python scraper.py --test --debug
    """
    import argparse
    import sys
    import os

    parser = argparse.ArgumentParser(
        description='Türk E-Ticaret Scraper v3.0 - Otomatik Platform Tespit Sistemi',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --url "https://www.trendyol.com/product/..."
  %(prog)s --url "https://unknown-site.com/product/123" --debug
  %(prog)s --test
  %(prog)s --test --debug
        """
    )
    parser.add_argument('--url', type=str, help='Scrape edilecek ürün URL\'i')
    parser.add_argument('--debug', action='store_true', help='Debug mode - detaylı log ve HTML kaydet')
    parser.add_argument('--test', action='store_true', help='Tüm test URL\'lerini çalıştır')

    args = parser.parse_args()

    # Debug mode ayarla
    if args.debug:
        os.environ['SCRAPER_DEBUG'] = 'true'
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        print(f"\n{'='*60}")
        print(f"🐛 DEBUG MODE ENABLED")
        print(f"{'='*60}\n")

    # Test mode
    if args.test:
        test_urls = [
            ('Trendyol (API)', 'https://www.trendyol.com/matt-notebook/a5-spiralli-suresiz-planlayici-ajanda-motivasyon-sayfali-potikare-p-797529053'),
            ('Hepsiburada (JSON-LD)', 'https://www.hepsiburada.com/mien-bambu-kapakli-12-adet-cam-baharatlik-seti-kavanoz-seti-ve-16-adet-etiket-hediyeli-p-HBCV00006Y57VM'),
            ('Karaca (dataLayer)', 'https://www.karaca.com/urun/karaca-tea-break-cay-makinesi-inox-siyah'),
            ('Enza Home (Akinon)', 'https://www.enzahome.com.tr/aldea-koltuk-takimi-3-1-20260107/'),
            ('Normod (Shopify)', 'https://normod.com/products/klem-butter-blush-cagla-yesili-3-3-1-koltuk-takimi-kadife'),
            ('Arçelik (JSON-LD)', 'https://www.arcelik.com.tr/9-kg-camasir-makinesi/9120-mp-og-camasir-makinesi'),
            ('IKEA', 'https://www.ikea.com.tr/tr/urunler/mutfak-urunleri/mutfak-esyasi-ve-taksim-sistemleri/uppspretta-yagdanlik'),
        ]

        passed = 0
        failed = 0

        for site_name, url in test_urls:
            print(f"\n{'='*80}")
            print(f"🧪 TEST: {site_name}")
            print(f"🔗 URL: {url}")
            print('='*80)

            try:
                result = scrape_product(url)

                if result['success']:
                    data = result['data']
                    print(f"✓ Başlık: {data['title'][:60]}...")
                    print(f"✓ Fiyat: {data['price']} TL")
                    print(f"✓ Marka: {data['brand']}")
                    print(f"✓ Kategori: {data['kategori_tahmini']} > {data['alt_kategori_tahmini']}")
                    print(f"✓ Görsel: {data['image_url'][:80]}..." if data['image_url'] else "✓ Görsel: N/A")
                    if data['specs']:
                        print(f"✓ Teknik Özellikler ({len(data['specs'])} adet):")
                        for k, v in list(data['specs'].items())[:5]:
                            print(f"    - {k}: {v}")
                    passed += 1
                else:
                    print(f"✗ Hata: {result['error']}")
                    failed += 1
            except Exception as e:
                print(f"✗ Exception: {e}")
                failed += 1

        print(f"\n{'='*80}")
        print(f"📊 TEST RESULTS")
        print(f"{'='*80}")
        print(f"✓ Passed: {passed}/{len(test_urls)}")
        print(f"✗ Failed: {failed}/{len(test_urls)}")
        print(f"{'='*80}\n")

        sys.exit(0 if failed == 0 else 1)

    # Tek URL scrape
    if args.url:
        result = scrape_product(args.url)

        if result['success']:
            import json
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"✗ Hata: {result['error']}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)
