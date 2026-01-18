#!/usr/bin/env python3
"""
DEBUG SCRAPER - HTML çıktısını göster
Kullanım: python3 debug_scraper.py <URL>
"""

import sys
import requests
from bs4 import BeautifulSoup

if len(sys.argv) < 2:
    print("Kullanım: python3 debug_scraper.py <URL>")
    sys.exit(1)

url = sys.argv[1]

# Scraper.py ile aynı headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8',
}

print(f"URL: {url}")
print("="*80)

try:
    session = requests.Session()
    session.trust_env = False

    response = session.get(url, headers=HEADERS, timeout=20, allow_redirects=True, proxies={})
    response.raise_for_status()

    if response.encoding in ['ISO-8859-1', 'ISO-8859-9', None]:
        response.encoding = 'utf-8'

    soup = BeautifulSoup(response.content, 'html.parser')

    print(f"\n✅ Başarılı - Status: {response.status_code}")
    print(f"Content-Length: {len(response.content)} bytes")
    print(f"Encoding: {response.encoding}")

    # Title selectors
    print("\n" + "="*80)
    print("TITLE SELECTORS:")
    print("="*80)

    title_selectors = [
        'h1.product-name', 'h1.product-title', 'h1#productName',
        'h1[itemprop="name"]', '.product-name h1',
        'h1.product_name', '.product-title h1', 'h1.pdp-title',
        '[data-testid="product-name"]', 'h1'
    ]

    for selector in title_selectors:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)[:100]
            print(f"  ✅ {selector}: {text}")
        else:
            print(f"  ❌ {selector}: Bulunamadı")

    # Price selectors
    print("\n" + "="*80)
    print("PRICE SELECTORS:")
    print("="*80)

    price_selectors = [
        '.product-price', '.prc-dsc', '.price',
        '[data-test-id="price"]', '[data-testid="price"]',
        '.product_price', '[itemprop="price"]', '.current-price'
    ]

    for selector in price_selectors:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            print(f"  ✅ {selector}: {text}")
        else:
            print(f"  ❌ {selector}: Bulunamadı")

    # JSON-LD Check
    print("\n" + "="*80)
    print("JSON-LD:")
    print("="*80)

    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    if json_ld_scripts:
        print(f"  ✅ {len(json_ld_scripts)} adet JSON-LD bulundu")
        for i, script in enumerate(json_ld_scripts[:2]):  # İlk 2 tanesini göster
            print(f"\n  JSON-LD #{i+1} (ilk 200 karakter):")
            print(f"  {script.string[:200] if script.string else 'Boş'}...")
    else:
        print("  ❌ JSON-LD bulunamadı")

    # Meta Tags
    print("\n" + "="*80)
    print("META TAGS:")
    print("="*80)

    og_title = soup.find('meta', property='og:title')
    if og_title:
        print(f"  ✅ og:title: {og_title.get('content', '')[:100]}")
    else:
        print("  ❌ og:title bulunamadı")

    og_image = soup.find('meta', property='og:image')
    if og_image:
        print(f"  ✅ og:image: {og_image.get('content', '')[:100]}")
    else:
        print("  ❌ og:image bulunamadı")

    # Hidden JS Variables
    print("\n" + "="*80)
    print("HIDDEN JS VARIABLES:")
    print("="*80)

    js_patterns = [
        'window.__PRELOADED_STATE__',
        'window.__NEXT_DATA__',
        'var product',
        'const product',
        'window.productData'
    ]

    html_text = response.text
    for pattern in js_patterns:
        if pattern in html_text:
            print(f"  ✅ {pattern} bulundu!")
            # Pattern'den sonraki 200 karakteri göster
            idx = html_text.find(pattern)
            snippet = html_text[idx:idx+200]
            print(f"     {snippet}...")
        else:
            print(f"  ❌ {pattern} bulunamadı")

    # HTML ilk 1000 karakter
    print("\n" + "="*80)
    print("HTML ÖRNEĞİ (ilk 1000 karakter):")
    print("="*80)
    print(html_text[:1000])

except Exception as e:
    print(f"\n❌ HATA: {e}")
    import traceback
    traceback.print_exc()
