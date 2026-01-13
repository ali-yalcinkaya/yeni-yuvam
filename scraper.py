"""
Akıllı Ürün Scraping Modülü
- JSON-LD Parser
- Regex ile Teknik Özellik Çıkarımı
- Site-Özel Kurallar
"""

import re
import json
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

# ============================================
# HEADERS - Bot koruması bypass
# ============================================
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}

# ============================================
# REGEX PATTERNS - Teknik özellik yakalama
# ============================================
REGEX_PATTERNS = {
    # Boyut kalıpları
    'boyut_wxhxd': r'(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)\s*[xX×]\s*(\d+(?:[.,]\d+)?)\s*(?:cm|mm|m)?',
    'genislik': r'(?:genişlik|en|width)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:cm|mm|m)?',
    'yukseklik': r'(?:yükseklik|boy|height)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:cm|mm|m)?',
    'derinlik': r'(?:derinlik|depth)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:cm|mm|m)?',
    
    # Kapasite kalıpları
    'kapasite_litre': r'(\d+(?:[.,]\d+)?)\s*(?:litre|lt|l)\b',
    'kapasite_kg': r'(\d+(?:[.,]\d+)?)\s*(?:kg|kilo)',
    
    # Enerji sınıfı
    'enerji_sinifi': r'(?:enerji\s*sınıfı|energy\s*class)[:\s]*([A-Ga-g](?:\+{1,3})?)',
    'enerji_sinifi_alt': r'\b([A-G](?:\+{1,3})?)\s*(?:enerji|energy)',
    
    # Ekran boyutu (TV/Monitör)
    'ekran_inç': r"(\d+(?:[.,]\d+)?)\s*(?:inç|inch|''|\"|\"|in\b)",
    'ekran_cm': r'(\d+)\s*(?:ekran|cm\s*ekran)',
    
    # Güç/Watt
    'watt': r'(\d+(?:[.,]\d+)?)\s*(?:watt|w)\b',
    
    # Devir (Çamaşır makinesi)
    'devir': r'(\d+)\s*(?:devir|rpm|d/dk)',
    
    # Su tüketimi
    'su_tuketimi': r'(?:su\s*tüketimi)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:lt|litre|l)',
    
    # Gürültü
    'gurultu_db': r'(\d+(?:[.,]\d+)?)\s*(?:db|dba|desibel)',
    
    # İşlemci (Bilgisayar)
    'islemci': r'(?:intel|amd|apple|qualcomm|core|ryzen|m\d+)[^\n,]{0,50}',
    
    # RAM
    'ram': r'(\d+)\s*(?:gb|tb)\s*(?:ram|bellek|memory)',
    
    # Depolama
    'depolama': r'(\d+)\s*(?:gb|tb)\s*(?:ssd|hdd|emmc|storage|depolama)',
    
    # Çözünürlük
    'cozunurluk': r'(\d{3,4})\s*[xX×]\s*(\d{3,4})',
    'cozunurluk_alt': r'(4K|8K|FHD|Full\s*HD|UHD|QHD|2K)',
    
    # Malzeme
    'malzeme': r'(?:malzeme|materyal|material|kumaş|fabric)[:\s]*([A-Za-zğüşıöçĞÜŞİÖÇ\s,]+)',
}

# ============================================
# ADIM 1: JSON-LD PARSER
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
        # Tüm JSON-LD script'lerini bul
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                
                # Bazen liste olarak geliyor
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Product' or item.get('@type') == 'product':
                            data = item
                            break
                    else:
                        continue
                
                # @graph içinde olabilir
                if '@graph' in data:
                    for item in data['@graph']:
                        if item.get('@type') == 'Product':
                            data = item
                            break
                    else:
                        continue
                
                # Product tipini kontrol et
                if data.get('@type') not in ['Product', 'product', 'IndividualProduct']:
                    continue
                
                # Verileri çıkar
                result['title'] = data.get('name', '') or result['title']
                result['description'] = data.get('description', '') or result['description']
                result['sku'] = data.get('sku', '') or data.get('mpn', '') or result['sku']
                result['gtin'] = data.get('gtin13', '') or data.get('gtin', '') or data.get('gtin14', '') or result['gtin']
                
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
                
            except json.JSONDecodeError:
                continue
            except Exception:
                continue
    
    except Exception:
        pass
    
    return result

# ============================================
# ADIM 2: META TAG PARSER
# ============================================
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
        
        # Product specific meta tags
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
    
    except Exception:
        pass
    
    return result

# ============================================
# ADIM 3: HTML ELEMENT PARSER
# ============================================
def extract_html_elements(soup, url):
    """HTML elementlerinden ürün bilgilerini çıkar"""
    result = {
        'title': '',
        'price': 0,
        'image_url': '',
        'brand': '',
        'specs': {}
    }
    
    domain = urlparse(url).netloc.lower()
    
    # =============== TITLE ===============
    title_selectors = [
        'h1.product-name', 'h1.product-title', 'h1#productName',
        'h1[itemprop="name"]', '.product-name h1', '.pr-new-br h1',
        'h1.product_name', '.product-title h1', 'h1.pdp-title',
        'h1.product-detail-name', 'h1'
    ]
    
    for selector in title_selectors:
        el = soup.select_one(selector)
        if el and el.get_text(strip=True):
            result['title'] = el.get_text(strip=True)[:300]
            break
    
    # =============== PRICE ===============
    price_selectors = [
        '.product-price', '.prc-dsc', '.price', '[data-test-id="price"]',
        '.product_price', '[itemprop="price"]', '.current-price',
        '.sale-price', '.pdp-price', '.price-value', '.product-detail-price',
        '.new-price', '.discount-price'
    ]
    
    for selector in price_selectors:
        el = soup.select_one(selector)
        if el:
            price_text = el.get_text(strip=True)
            # Fiyat temizleme
            price_clean = re.sub(r'[^\d,.]', '', price_text)
            price_clean = price_clean.replace('.', '').replace(',', '.')
            try:
                price = float(price_clean)
                if price > 0:
                    result['price'] = price
                    break
            except:
                continue
    
    # =============== BRAND ===============
    brand_selectors = [
        '[itemprop="brand"]', '.brand', '.product-brand',
        '.pr-new-br a', '.product_brand', '.brand-name',
        'a.product-brand', '.manufacturer'
    ]
    
    for selector in brand_selectors:
        el = soup.select_one(selector)
        if el:
            brand_text = el.get_text(strip=True) or el.get('content', '')
            if brand_text:
                result['brand'] = brand_text[:100]
                break
    
    # =============== IMAGE ===============
    img_selectors = [
        '.product-image img', '.gallery-image img', '[itemprop="image"]',
        '.product-gallery img', '.pdp-gallery img', '.main-image img',
        '.product-detail-image img', 'img.product-image', '.slick-slide img'
    ]
    
    for selector in img_selectors:
        el = soup.select_one(selector)
        if el:
            img_url = el.get('src') or el.get('data-src') or el.get('data-original')
            if img_url and 'placeholder' not in img_url.lower():
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    parsed = urlparse(url)
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                result['image_url'] = img_url
                break
    
    # =============== SPECS TABLE ===============
    # Trendyol tarzı
    spec_rows = soup.select('.product-feature-list li, .product-property-list li, .detail-attr-item')
    for row in spec_rows:
        spans = row.find_all('span')
        if len(spans) >= 2:
            key = spans[0].get_text(strip=True).lower().replace(' ', '_')
            val = spans[1].get_text(strip=True)
            if key and val:
                result['specs'][key] = val
    
    # Tablo tarzı (dt/dd veya tr/td)
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
# ADIM 4: REGEX MADENCILIĞI
# ============================================
def extract_with_regex(soup, title='', existing_specs=None):
    """Regex ile sayfadan teknik özellik çıkar"""
    if existing_specs is None:
        existing_specs = {}
    
    specs = existing_specs.copy()
    
    # Sayfa metnini al
    text = soup.get_text(separator=' ', strip=True).lower()
    
    # Boyut çıkarımı (WxHxD)
    if 'boyut' not in specs and 'olculer' not in specs:
        match = re.search(REGEX_PATTERNS['boyut_wxhxd'], text, re.IGNORECASE)
        if match:
            w, h, d = match.groups()
            specs['olculer'] = f"{w}x{h}x{d} cm"
    
    # Genişlik, Yükseklik, Derinlik ayrı ayrı
    for dim, pattern in [('genislik', 'genislik'), ('yukseklik', 'yukseklik'), ('derinlik', 'derinlik')]:
        if dim not in specs:
            match = re.search(REGEX_PATTERNS[pattern], text, re.IGNORECASE)
            if match:
                specs[dim] = f"{match.group(1)} cm"
    
    # Kapasite (Litre)
    if 'kapasite' not in specs and 'hacim' not in specs:
        match = re.search(REGEX_PATTERNS['kapasite_litre'], text, re.IGNORECASE)
        if match:
            specs['kapasite_lt'] = f"{match.group(1)} L"
    
    # Kapasite (KG)
    if 'kapasite_kg' not in specs:
        match = re.search(REGEX_PATTERNS['kapasite_kg'], text, re.IGNORECASE)
        if match:
            specs['kapasite_kg'] = f"{match.group(1)} kg"
    
    # Enerji sınıfı
    if 'enerji_sinifi' not in specs and 'enerji' not in specs:
        match = re.search(REGEX_PATTERNS['enerji_sinifi'], text, re.IGNORECASE)
        if match:
            specs['enerji_sinifi'] = match.group(1).upper()
        else:
            match = re.search(REGEX_PATTERNS['enerji_sinifi_alt'], text, re.IGNORECASE)
            if match:
                specs['enerji_sinifi'] = match.group(1).upper()
    
    # Ekran boyutu
    if 'ekran' not in specs and 'ekran_boyutu' not in specs:
        match = re.search(REGEX_PATTERNS['ekran_inç'], text, re.IGNORECASE)
        if match:
            specs['ekran_boyutu'] = f'{match.group(1)}"'
        else:
            match = re.search(REGEX_PATTERNS['ekran_cm'], text, re.IGNORECASE)
            if match:
                specs['ekran_cm'] = f"{match.group(1)} cm"
    
    # Güç (Watt)
    if 'watt' not in specs and 'guc' not in specs:
        match = re.search(REGEX_PATTERNS['watt'], text, re.IGNORECASE)
        if match:
            specs['guc_watt'] = f"{match.group(1)} W"
    
    # Devir
    if 'devir' not in specs:
        match = re.search(REGEX_PATTERNS['devir'], text, re.IGNORECASE)
        if match:
            specs['devir_sayisi'] = f"{match.group(1)} rpm"
    
    # Gürültü
    if 'gurultu' not in specs:
        match = re.search(REGEX_PATTERNS['gurultu_db'], text, re.IGNORECASE)
        if match:
            specs['gurultu_db'] = f"{match.group(1)} dB"
    
    # Çözünürlük - SADECE TV/Monitör/Ekran ürünlerinde ara
    if 'cozunurluk' not in specs:
        # Önce ürünün TV/Monitör/Ekran olup olmadığını kontrol et
        # Başlık ve kategori bilgilerini kontrol et (daha güvenilir)
        text_lower = text.lower()
        title_lower = (title or '').lower()

        # Kesinlikle ekran ürünü olmalı
        is_display_product = any(keyword in title_lower for keyword in [
            'televizyon', 'tv', 'smart tv', 'monitör', 'monitor'
        ]) or any(keyword in text_lower[:500] for keyword in [  # Sadece ilk 500 karakter
            'televizyon özellikleri', 'tv özellikleri', 'monitör özellikleri',
            'ekran boyutu', 'ekran çözünürlüğü'
        ])

        # Kesinlikle beyaz eşya DEĞİL olmalı
        is_not_appliance = not any(keyword in title_lower for keyword in [
            'buzdolabı', 'çamaşır', 'bulaşık', 'fırın', 'kurutma',
            'klima', 'aspiratör', 'davlumbaz'
        ])

        if is_display_product and is_not_appliance:
            # Context-aware arama: çözünürlük kelimesinin yakınında ara
            context_patterns = [
                r'(?:ekran|çözünürlük|resolution|panel)[\s\w]{0,30}?(4K|8K|FHD|Full\s*HD|UHD|QHD|2K)',
                r'(4K|8K|FHD|Full\s*HD|UHD|QHD|2K)[\s\w]{0,30}?(?:ekran|çözünürlük|resolution|panel)',
            ]
            for pattern in context_patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    specs['cozunurluk'] = match.group(1).upper()
                    break

            # Piksel çözünürlüğü de TV/Monitör için ara
            if 'cozunurluk' not in specs:
                match = re.search(REGEX_PATTERNS['cozunurluk'], text)
                if match:
                    w, h = match.groups()
                    if int(w) > 500 and int(h) > 500:  # Gerçek çözünürlük olması için
                        specs['cozunurluk'] = f"{w}x{h}"
    
    # RAM
    if 'ram' not in specs:
        match = re.search(REGEX_PATTERNS['ram'], text, re.IGNORECASE)
        if match:
            specs['ram'] = f"{match.group(1)} GB"
    
    # Depolama
    if 'depolama' not in specs and 'ssd' not in specs:
        match = re.search(REGEX_PATTERNS['depolama'], text, re.IGNORECASE)
        if match:
            specs['depolama'] = f"{match.group(1)} GB"
    
    return specs

# ============================================
# ADIM 5: SİTE-ÖZEL PARSER'LAR
# ============================================
def parse_samsung(soup, url):
    """Samsung sitesi için özel parser"""
    specs = {}
    
    # Ölçüler - Samsung formatı
    dim_section = soup.select('.spec-dimension, .product-dimension')
    for section in dim_section:
        for item in section.select('li, .item'):
            text = item.get_text(strip=True)
            if 'Genişlik' in text:
                match = re.search(r'(\d+)', text)
                if match:
                    specs['genislik'] = f"{match.group(1)} mm"
            elif 'Yükseklik' in text:
                match = re.search(r'(\d+)', text)
                if match:
                    specs['yukseklik'] = f"{match.group(1)} mm"
            elif 'Derinlik' in text:
                match = re.search(r'(\d+)', text)
                if match:
                    specs['derinlik'] = f"{match.group(1)} mm"
    
    # Kapasite - başlıktan
    title = soup.select_one('h1')
    if title:
        text = title.get_text()
        match = re.search(r'(\d+)\s*(?:L|Litre)', text, re.IGNORECASE)
        if match:
            specs['kapasite_lt'] = f"{match.group(1)} L"
    
    return specs

def parse_arcelik(soup, url):
    """Arçelik sitesi için özel parser"""
    specs = {}
    
    # Enerji etiketi linki varsa
    energy_link = soup.select_one('a[href*="energylabel"]')
    if energy_link:
        # Enerji sınıfı genellikle badge olarak gösterilir
        energy_badge = soup.select_one('.energy-class, [class*="energy"]')
        if energy_badge:
            text = energy_badge.get_text(strip=True)
            match = re.search(r'([A-G](?:\+{1,3})?)', text)
            if match:
                specs['enerji_sinifi'] = match.group(1)
    
    return specs

def parse_trendyol(soup, url):
    """Trendyol sitesi için özel parser"""
    specs = {}
    
    # Ürün özellikleri bölümü
    for row in soup.select('.detail-attr-container .detail-attr-item'):
        key_el = row.select_one('.detail-attr-name')
        val_el = row.select_one('.detail-attr-value')
        if key_el and val_el:
            key = key_el.get_text(strip=True).lower().replace(' ', '_')
            val = val_el.get_text(strip=True)
            specs[key] = val
    
    return specs

def parse_hepsiburada(soup, url):
    """Hepsiburada sitesi için özel parser"""
    specs = {}
    
    # Ürün özellikleri tablosu
    for row in soup.select('.tech-spec-row, [data-test-id="spec-row"]'):
        key_el = row.select_one('.spec-name, [data-test-id="spec-name"]')
        val_el = row.select_one('.spec-value, [data-test-id="spec-value"]')
        if key_el and val_el:
            key = key_el.get_text(strip=True).lower().replace(' ', '_')
            val = val_el.get_text(strip=True)
            specs[key] = val
    
    return specs

def parse_enzahome(soup, url):
    """Enza Home sitesi için özel parser"""
    specs = {}
    
    # Kategori tahmini
    specs['_kategori'] = 'Mobilya'
    
    # URL'den alt kategori
    url_lower = url.lower()
    if 'koltuk' in url_lower:
        specs['_alt_kategori'] = 'Koltuk Takımı'
    elif 'yatak' in url_lower:
        specs['_alt_kategori'] = 'Yatak'
    elif 'masa' in url_lower:
        specs['_alt_kategori'] = 'Yemek Masası'
    
    return specs

def parse_vatan(soup, url):
    """Vatan Bilgisayar sitesi için özel parser"""
    specs = {}
    
    # Ürün özellikleri tablosu
    for row in soup.select('.product-table tr, .product-spec tr'):
        cells = row.select('td')
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True).lower().replace(' ', '_').replace(':', '')
            val = cells[1].get_text(strip=True)
            if key and val:
                specs[key] = val
    
    return specs

def parse_teknosa(soup, url):
    """Teknosa sitesi için özel parser"""
    specs = {}
    
    # Ürün özellikleri
    for row in soup.select('.product-spec-item, .spec-list li'):
        text = row.get_text(strip=True)
        if ':' in text:
            parts = text.split(':', 1)
            key = parts[0].strip().lower().replace(' ', '_')
            val = parts[1].strip()
            specs[key] = val
    
    return specs

def parse_mediamarkt(soup, url):
    """MediaMarkt sitesi için özel parser"""
    specs = {}
    
    # Ürün özellikleri
    for row in soup.select('.product-feature, [data-test="product-feature"]'):
        key_el = row.select_one('.feature-name')
        val_el = row.select_one('.feature-value')
        if key_el and val_el:
            key = key_el.get_text(strip=True).lower().replace(' ', '_')
            val = val_el.get_text(strip=True)
            specs[key] = val
    
    return specs

def parse_yatas(soup, url):
    """Yataş sitesi için özel parser"""
    specs = {}
    
    specs['_kategori'] = 'Tekstil'
    specs['_alt_kategori'] = 'Yatak'
    
    return specs

# ============================================
# KATEGORİ VE ODA TAHMİNİ
# ============================================
def detect_category_and_room(url, title, specs):
    """URL ve başlıktan kategori ve oda tahmini"""
    url_lower = url.lower()
    title_lower = (title or '').lower()
    combined = url_lower + ' ' + title_lower

    # Beyaz Eşya
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

    # Mobilya
    if any(x in combined for x in ['koltuk', 'sofa', 'couch']):
        return 'Mobilya', 'Koltuk Takımı', 'Salon'
    if any(x in combined for x in ['masa', 'table', 'desk']):
        return 'Mobilya', 'Yemek Masası', 'Salon'
    if any(x in combined for x in ['dolap', 'cabinet', 'wardrobe']):
        return 'Mobilya', 'Dolap', 'Yatak Odası'
    if any(x in combined for x in ['tv ünitesi', 'tv-unitesi', 'tv unite']):
        return 'Mobilya', 'TV Ünitesi', 'Salon'

    # Elektronik
    if any(x in combined for x in ['televizyon', 'tv', 'led tv', 'smart tv']):
        return 'Elektronik', 'Televizyon', 'Salon'
    if any(x in combined for x in ['klima', 'air conditioner']):
        return 'Elektronik', 'Klima', 'Salon'
    if any(x in combined for x in ['laptop', 'notebook', 'bilgisayar', 'zenbook', 'macbook']):
        return 'Elektronik', 'Genel', 'Çalışma Odası'
    if any(x in combined for x in ['monitör', 'monitor']):
        return 'Elektronik', 'Genel', 'Çalışma Odası'

    # Tekstil
    if any(x in combined for x in ['yatak', 'mattress', 'bedding']):
        return 'Tekstil', 'Genel', 'Yatak Odası'
    if any(x in combined for x in ['nevresim', 'pike', 'yorgan']):
        return 'Tekstil', 'Nevresim Takımı', 'Yatak Odası'

    # Küçük Ev Aletleri
    if any(x in combined for x in ['süpürge', 'supurge', 'vacuum', 'mop']):
        return 'Diğer', 'Genel', 'Diğer'
    if any(x in combined for x in ['blender', 'mikser', 'kahve makinesi']):
        return 'Mutfak Gereci', 'Genel', 'Mutfak'

    # Banyo ürünleri
    if any(x in combined for x in ['lavabo', 'klozet', 'duş', 'dus', 'batarya', 'banyo']):
        return 'Banyo', 'Genel', 'Banyo'

    return 'Diğer', 'Genel', 'Salon'

# Geriye uyumluluk için eski fonksiyon
def detect_category(url, title, specs):
    """Eski API - kategori ve alt kategori döndürür"""
    kategori, alt_kategori, _ = detect_category_and_room(url, title, specs)
    return kategori, alt_kategori

# ============================================
# ANA FONKSİYON
# ============================================
def scrape_product(url):
    """
    Ana scraping fonksiyonu - URL'den akıllıca ürün bilgisi çeker
    
    Returns:
        dict: {
            'success': bool,
            'data': {
                'title': str,
                'price': float,
                'image_url': str,
                'brand': str,
                'description': str,
                'link': str,
                'kategori_tahmini': str,
                'alt_kategori_tahmini': str,
                'specs': dict
            },
            'error': str (if success=False)
        }
    """
    try:
        # Request gönder
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        response.raise_for_status()
        
        # Encoding düzelt
        if response.encoding in ['ISO-8859-1', 'ISO-8859-9', None]:
            response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.content, 'html.parser')
        domain = urlparse(url).netloc.lower()
        
        # ============ ADIM 1: JSON-LD ============
        json_ld_data = extract_json_ld(soup)
        
        # ============ ADIM 2: META TAGS ============
        meta_data = extract_meta_tags(soup)
        
        # ============ ADIM 3: HTML ELEMENTS ============
        html_data = extract_html_elements(soup, url)
        
        # ============ ADIM 4: SİTE-ÖZEL PARSER ============
        site_specs = {}
        if 'samsung.com' in domain:
            site_specs = parse_samsung(soup, url)
        elif 'arcelik.com' in domain:
            site_specs = parse_arcelik(soup, url)
        elif 'trendyol.com' in domain:
            site_specs = parse_trendyol(soup, url)
        elif 'hepsiburada.com' in domain:
            site_specs = parse_hepsiburada(soup, url)
        elif 'enzahome.com' in domain:
            site_specs = parse_enzahome(soup, url)
        elif 'vatanbilgisayar.com' in domain:
            site_specs = parse_vatan(soup, url)
        elif 'teknosa.com' in domain:
            site_specs = parse_teknosa(soup, url)
        elif 'mediamarkt.com' in domain:
            site_specs = parse_mediamarkt(soup, url)
        elif 'yatasbedding.com' in domain or 'yatas.com' in domain:
            site_specs = parse_yatas(soup, url)
        
        # ============ VERİLERİ BİRLEŞTİR ============
        # Öncelik: JSON-LD > Meta > HTML
        result = {
            'title': json_ld_data['title'] or meta_data['title'] or html_data['title'],
            'price': json_ld_data['price'] or meta_data['price'] or html_data['price'],
            'image_url': json_ld_data['image_url'] or meta_data['image_url'] or html_data['image_url'],
            'brand': json_ld_data['brand'] or meta_data['brand'] or html_data['brand'],
            'description': json_ld_data['description'] or meta_data['description'],
            'link': url,
            'sku': json_ld_data['sku'],
            'gtin': json_ld_data['gtin'],
            'specs': {}
        }
        
        # Tüm specs'leri birleştir
        all_specs = {}
        all_specs.update(json_ld_data.get('specs', {}))
        all_specs.update(html_data.get('specs', {}))
        all_specs.update(site_specs)
        
        # ============ ADIM 5: REGEX MADENCİLİĞİ ============
        all_specs = extract_with_regex(soup, result['title'], all_specs)
        
        # Kategori ve Oda al (site-özel'den veya tahmin et)
        kategori = site_specs.get('_kategori', '')
        alt_kategori = site_specs.get('_alt_kategori', '')
        oda = ''

        if not kategori:
            kategori, alt_kategori, oda = detect_category_and_room(url, result['title'], all_specs)

        result['kategori_tahmini'] = kategori
        result['alt_kategori_tahmini'] = alt_kategori
        result['oda_tahmini'] = oda
        
        # _kategori gibi internal key'leri temizle
        result['specs'] = {k: v for k, v in all_specs.items() if not k.startswith('_')}
        
        # Marka yoksa domain'den tahmin et
        if not result['brand']:
            if 'samsung' in domain:
                result['brand'] = 'Samsung'
            elif 'arcelik' in domain:
                result['brand'] = 'Arçelik'
            elif 'enzahome' in domain:
                result['brand'] = 'Enza Home'
            elif 'yatas' in domain:
                result['brand'] = 'Yataş'
        
        return {
            'success': True,
            'data': result
        }
    
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Site yanıt vermedi (timeout)'}
    except requests.exceptions.HTTPError as e:
        return {'success': False, 'error': f'HTTP hatası: {e.response.status_code}'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Bağlantı hatası: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Beklenmeyen hata: {str(e)}'}


# ============================================
# TEST
# ============================================
if __name__ == '__main__':
    test_urls = [
        'https://www.trendyol.com/arpelia/tek-kanatli-katlanir-masa-100x50x75-p-939075585',
    ]
    
    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"URL: {url}")
        print('='*60)
        
        result = scrape_product(url)
        
        if result['success']:
            data = result['data']
            print(f"✓ Başlık: {data['title'][:60]}...")
            print(f"✓ Fiyat: {data['price']} TL")
            print(f"✓ Marka: {data['brand']}")
            print(f"✓ Kategori: {data['kategori_tahmini']} > {data['alt_kategori_tahmini']}")
            print(f"✓ Teknik Özellikler ({len(data['specs'])} adet):")
            for k, v in list(data['specs'].items())[:10]:
                print(f"    - {k}: {v}")
        else:
            print(f"✗ Hata: {result['error']}")
