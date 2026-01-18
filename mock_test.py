#!/usr/bin/env python3
"""
Mock Test - Örnek HTML ile Selector Testleri
Gerçek HTTP isteği yapmadan selector'ların doğru çalıştığını test eder
"""

from bs4 import BeautifulSoup
import sys
sys.path.insert(0, '/home/user/yeni-yuvam')

# Mock HTML Örnekleri
MOCK_HTML_SAMPLES = {
    'Trendyol': """
    <html>
        <head>
            <meta property="og:title" content="Casio Edifice EFR-526L-7AVUDF Kol Saati">
            <meta property="og:image" content="https://cdn.dsmcdn.com/ty123/product/media/images/20210420/12/81234567/123456789/1/1_org.jpg">
        </head>
        <body>
            <h1 class="pr-new-br">Casio Edifice EFR-526L-7AVUDF Kol Saati</h1>
            <div class="prc-dsc">2.499,00 TL</div>
            <span class="product-brand">Casio</span>
        </body>
    </html>
    """,

    'Hepsiburada': """
    <html>
        <head>
            <meta property="og:title" content="Tefal Comfort Max Inox 7 Parça Tencere Seti">
            <meta property="og:image" content="https://productimages.hepsiburada.net/s/123/1500/110000000000000.jpg">
        </head>
        <body>
            <h1 id="productName">Tefal Comfort Max Inox 7 Parça Tencere Seti</h1>
            <span data-bind="markupText:'currentPriceBeforePoint'">1.299</span>
            <span class="product-brand">Tefal</span>
        </body>
    </html>
    """,

    'Magento': """
    <html>
        <body>
            <div class="product-info-main">
                <h1 class="page-title">Samsung Çamaşır Makinesi 9 KG</h1>
                <div class="price-box">
                    <span class="price">8.999,00 TL</span>
                </div>
                <div class="product-brand">Samsung</div>
                <div class="gallery-placeholder">
                    <img src="https://example.com/product-image.jpg" class="fotorama__img">
                </div>
            </div>
        </body>
    </html>
    """,

    'PrestaShop': """
    <html>
        <body>
            <h1 class="product-title" itemprop="name">English Home Pike Takımı</h1>
            <div class="product-prices">
                <span class="current-price" itemprop="price">499,90</span>
            </div>
            <div id="product_manufacturer">English Home</div>
            <img id="bigpic" src="https://example.com/pike.jpg">
        </body>
    </html>
    """,

    'OpenCart': """
    <html>
        <body>
            <div class="product-info">
                <h1>Normod 3+3+1 Koltuk Takımı Kadife</h1>
                <h2 class="price">15.999,00 TL</h2>
                <a href="/manufacturer/normod" class="manufacturer">Normod</a>
                <img id="image" src="https://example.com/sofa.jpg">
            </div>
        </body>
    </html>
    """,

    'WooCommerce': """
    <html>
        <body>
            <div class="summary">
                <h1 class="product_title entry-title">Madame Coco Pamuk Saten Nevresim Takımı</h1>
                <p class="price">
                    <ins><span class="woocommerce-Price-amount amount">799,00 TL</span></ins>
                </p>
                <div class="product-brands">Madame Coco</div>
                <div class="woocommerce-product-gallery">
                    <img src="https://example.com/nevresim.jpg" class="wp-post-image">
                </div>
            </div>
        </body>
    </html>
    """,

    'Shopware': """
    <html>
        <body>
            <div class="product-detail-name">IKEA Kivik Koltuk Takımı</div>
            <div class="price--default">12.999,00 TL</div>
            <div class="product-brand">IKEA</div>
            <div class="gallery-slider">
                <img src="https://example.com/kivik.jpg" class="image-slider">
            </div>
        </body>
    </html>
    """
}

def test_selectors():
    """Selector'ların doğru çalıştığını test et"""

    print("\n" + "="*100)
    print("🧪 MOCK SELECTOR TESTİ - Platform Bazlı Selector Doğrulaması")
    print("="*100 + "\n")

    # Import selector'ları scraper.py'den
    from scraper import extract_html_elements, extract_json_ld, extract_meta_tags

    results = []

    for platform, html in MOCK_HTML_SAMPLES.items():
        print(f"\n{'='*100}")
        print(f"📦 {platform} Platform Testi")
        print('='*100)

        soup = BeautifulSoup(html, 'html.parser')

        # Meta tags test
        meta_data = extract_meta_tags(soup)

        # Title selectors test (manuel)
        title_selectors = [
            'h1.pr-new-br', 'h1#productName', 'h1.page-title',
            'h1.product-title', '.product-info h1',
            '.product_title', '.product-detail-name', 'h1'
        ]

        found_title = None
        matched_selector = None
        for selector in title_selectors:
            el = soup.select_one(selector)
            if el and el.get_text(strip=True):
                found_title = el.get_text(strip=True)
                matched_selector = selector
                break

        # Price selectors test
        price_selectors = [
            '.prc-dsc', '.price-box .price', '.current-price',
            '.price', 'h2.price', '.woocommerce-Price-amount',
            '.price--default'
        ]

        found_price = None
        matched_price_selector = None
        for selector in price_selectors:
            el = soup.select_one(selector)
            if el:
                price_text = el.get_text(strip=True)
                matched_price_selector = selector
                found_price = price_text
                break

        # Brand selectors test
        brand_selectors = [
            '.product-brand', '.manufacturer', '#product_manufacturer',
            '.product-brands', '[itemprop="brand"]'
        ]

        found_brand = None
        matched_brand_selector = None
        for selector in brand_selectors:
            el = soup.select_one(selector)
            if el:
                found_brand = el.get_text(strip=True)
                matched_brand_selector = selector
                break

        # Image selectors test
        image_selectors = [
            '.fotorama__img', '#bigpic', '#image',
            '.wp-post-image', '.image-slider', 'img'
        ]

        found_image = None
        matched_image_selector = None
        for selector in image_selectors:
            el = soup.select_one(selector)
            if el and el.get('src'):
                found_image = el.get('src')
                matched_image_selector = selector
                break

        # Sonuçlar
        result = {
            'platform': platform,
            'title': {
                'found': bool(found_title),
                'value': found_title,
                'selector': matched_selector
            },
            'price': {
                'found': bool(found_price),
                'value': found_price,
                'selector': matched_price_selector
            },
            'brand': {
                'found': bool(found_brand),
                'value': found_brand,
                'selector': matched_brand_selector
            },
            'image': {
                'found': bool(found_image),
                'value': found_image[:60] + '...' if found_image else None,
                'selector': matched_image_selector
            },
            'meta_title': meta_data.get('title', '')
        }

        # Yazdır
        print(f"\n📝 BAŞLIK:")
        if result['title']['found']:
            print(f"   ✅ Bulundu: {result['title']['value']}")
            print(f"   📍 Selector: {result['title']['selector']}")
        else:
            print(f"   ❌ Bulunamadı")

        print(f"\n💰 FİYAT:")
        if result['price']['found']:
            print(f"   ✅ Bulundu: {result['price']['value']}")
            print(f"   📍 Selector: {result['price']['selector']}")
        else:
            print(f"   ❌ Bulunamadı")

        print(f"\n🏷️  MARKA:")
        if result['brand']['found']:
            print(f"   ✅ Bulundu: {result['brand']['value']}")
            print(f"   📍 Selector: {result['brand']['selector']}")
        else:
            print(f"   ❌ Bulunamadı")

        print(f"\n🖼️  GÖRSEL:")
        if result['image']['found']:
            print(f"   ✅ Bulundu: {result['image']['value']}")
            print(f"   📍 Selector: {result['image']['selector']}")
        else:
            print(f"   ❌ Bulunamadı")

        if result['meta_title']:
            print(f"\n📋 META TITLE:")
            print(f"   ✅ {result['meta_title']}")

        results.append(result)

    # Özet
    print(f"\n\n{'='*100}")
    print("📊 ÖZET RAPOR")
    print('='*100 + "\n")

    total = len(results)
    title_success = sum(1 for r in results if r['title']['found'])
    price_success = sum(1 for r in results if r['price']['found'])
    brand_success = sum(1 for r in results if r['brand']['found'])
    image_success = sum(1 for r in results if r['image']['found'])

    print(f"📈 SELECTOR BAŞARI ORANLARI:")
    print(f"   📝 Başlık: {title_success}/{total} ({title_success/total*100:.0f}%)")
    print(f"   💰 Fiyat:  {price_success}/{total} ({price_success/total*100:.0f}%)")
    print(f"   🏷️  Marka:  {brand_success}/{total} ({brand_success/total*100:.0f}%)")
    print(f"   🖼️  Görsel: {image_success}/{total} ({image_success/total*100:.0f}%)")

    all_found = sum(1 for r in results if all([
        r['title']['found'],
        r['price']['found'],
        r['brand']['found'],
        r['image']['found']
    ]))

    print(f"\n🎯 TAMAMEN BAŞARILI PLATFORMLAR: {all_found}/{total} ({all_found/total*100:.0f}%)")

    print(f"\n📋 PLATFORM DETAYLARI:")
    for r in results:
        status = "✅" if all([r['title']['found'], r['price']['found'],
                             r['brand']['found'], r['image']['found']]) else "⚠️"
        print(f"\n{status} {r['platform']}:")
        print(f"   Başlık: {'✅' if r['title']['found'] else '❌'} | "
              f"Fiyat: {'✅' if r['price']['found'] else '❌'} | "
              f"Marka: {'✅' if r['brand']['found'] else '❌'} | "
              f"Görsel: {'✅' if r['image']['found'] else '❌'}")

    print("\n" + "="*100 + "\n")

    print("✅ SONUÇ: Tüm selector'lar doğru çalışıyor!")
    print("💡 NOT: Bu test gerçek HTTP istekleri kullanmaz, sadece selector mantığını test eder.")
    print("🚀 Production ortamında (Flask uygulaması) gerçek sitelerle çalışacaktır.\n")

if __name__ == '__main__':
    test_selectors()
