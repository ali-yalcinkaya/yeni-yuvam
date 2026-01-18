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
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin

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
    'kumas_tipi': r'\b(pamuk|saten|ranforce|penye|floş|pike|şardonlu|jakarlı)\b',

    # Mobilya tipleri
    'mobilya_tipi': r"(\d+['']lü|köşe\s*takımı|berjer|chester|kanepe|zigon)",
}

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
            '.product-image img', '.gallery-image img', '[itemprop="image"]',
            '.product-gallery img', '.pdp-gallery img', '.main-image img',
            '.product-detail-image img', 'img.product-image', '.slick-slide img',
            '.carousel-item img', '.product-img img', '[data-testid*="image"] img'
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
    """
    result = {
        'title': '',
        'price': 0,
        'brand': '',
        'specs': {}
    }

    # Pattern 1: window.__PRELOADED_STATE__ veya __NEXT_DATA__
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

    # ============ TITLE ============
    if not result['title']:
        title_selectors = [
            'h1.product-name', 'h1.product-title', 'h1#productName',
            'h1[itemprop="name"]', '.product-name h1', '.pr-new-br h1',
            'h1.product_name', '.product-title h1', 'h1.pdp-title',
            'h1.product-detail-name', '[data-testid="product-name"]', 'h1'
        ]

        for selector in title_selectors:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                result['title'] = el.get_text(strip=True)[:300]
                break

    # ============ PRICE (GENİŞLETİLMİŞ) ============
    if not result['price']:
        price_selectors = [
            '.product-price', '.prc-dsc', '.price', '[data-test-id="price"]',
            '[data-testid="price"]', '[data-testid="product-price"]',
            '.product_price', '[itemprop="price"]', '.current-price',
            '.sale-price', '.pdp-price', '.price-value', '.product-detail-price',
            '.new-price', '.discount-price', '.sales-price', '.selling-price',
            '.price-current', '.price-box .price', '.product-price-value',
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
            '[itemprop="brand"]', '.brand', '.product-brand',
            '.pr-new-br a', '.product_brand', '.brand-name',
            'a.product-brand', '.manufacturer', '[data-testid="brand"]'
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
    if any(x in combined for x in ['blender', 'mikser', 'kahve makinesi', 'coffee maker']):
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
# 5. USER-AGENT ROTASYONU VE RETRY
# ============================================
def fetch_with_retry(url, max_retries=3):
    """
    User-Agent rotasyonu ile retry mekanizması
    403/503 hatası alırsa farklı UA ile tekrar dener
    """
    session = requests.Session()
    # Proxy'leri devre dışı bırak (Replit ortamı için)
    session.trust_env = False

    for attempt in range(max_retries):
        headers = USER_AGENTS[attempt % len(USER_AGENTS)].copy()

        try:
            response = session.get(url, headers=headers, timeout=20, allow_redirects=True, proxies={})

            # 403/503 hatası - farklı UA ile tekrar dene
            if response.status_code in [403, 503] and attempt < max_retries - 1:
                time.sleep(1)  # Kısa bekle
                continue

            response.raise_for_status()

            # Encoding düzelt
            if response.encoding in ['ISO-8859-1', 'ISO-8859-9', None]:
                response.encoding = 'utf-8'

            return response, None

        except requests.exceptions.HTTPError as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None, f'HTTP hatası: {e.response.status_code}'

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None, 'Site yanıt vermedi (timeout)'

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None, f'Bağlantı hatası: {str(e)}'

    return None, 'Maksimum deneme sayısı aşıldı'

# ============================================
# ANA FONKSİYON
# ============================================
def scrape_product(url):
    """
    YENİ MİMARİ v2.0 - Akıllı Scraping

    Returns:
        dict: {
            'success': bool,
            'data': {...},
            'error': str
        }
    """
    try:
        # 1. MOBİL URL NORMALİZASYONU
        normalized_url, was_mobile = normalize_mobile_url(url)

        # Önce masaüstü URL'i dene
        response, error = fetch_with_retry(normalized_url)

        # Masaüstü başarısız olduysa ve orijinal mobil ise, mobil'i dene
        if not response and was_mobile:
            response, error = fetch_with_retry(url)
            if response:
                normalized_url = url  # Mobil çalıştı, onu kullan

        if not response:
            return {'success': False, 'error': error or 'Bilinmeyen hata'}

        soup = BeautifulSoup(response.content, 'html.parser')
        html_text = response.text
        domain = urlparse(normalized_url).netloc.lower()

        # ============ VERİ ÇIKARMA ============
        json_ld_data = extract_json_ld(soup)
        meta_data = extract_meta_tags(soup)
        html_data = extract_html_elements(soup, normalized_url, html_text)

        # Birleştir (Öncelik: JSON-LD > Meta > HTML)
        result = {
            'title': json_ld_data['title'] or meta_data['title'] or html_data['title'],
            'price': json_ld_data['price'] or meta_data['price'] or html_data['price'],
            'image_url': json_ld_data['image_url'] or meta_data['image_url'] or html_data['image_url'],
            'brand': json_ld_data['brand'] or meta_data['brand'] or html_data['brand'],
            'description': json_ld_data['description'] or meta_data['description'],
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

        return {
            'success': True,
            'data': result
        }

    except Exception as e:
        return {'success': False, 'error': f'Beklenmeyen hata: {str(e)}'}

# ============================================
# TEST
# ============================================
if __name__ == '__main__':
    test_urls = [
        'https://www.arcelik.com.tr/9-kg-camasir-makinesi/9120-mp-og-camasir-makinesi',
        'https://m.trendyol.com/arpelia/tek-kanatli-katlanir-masa-100x50x75-p-939075585',
    ]

    for url in test_urls:
        print(f"\n{'='*70}")
        print(f"URL: {url}")
        print('='*70)

        result = scrape_product(url)

        if result['success']:
            data = result['data']
            print(f"✓ Başlık: {data['title'][:60]}...")
            print(f"✓ Fiyat: {data['price']} TL")
            print(f"✓ Marka: {data['brand']}")
            print(f"✓ Kategori: {data['kategori_tahmini']} > {data['alt_kategori_tahmini']}")
            print(f"✓ Görsel: {data['image_url'][:80]}...")
            print(f"✓ Teknik Özellikler ({len(data['specs'])} adet):")
            for k, v in list(data['specs'].items())[:5]:
                print(f"    - {k}: {v}")
        else:
            print(f"✗ Hata: {result['error']}")
