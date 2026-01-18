#!/usr/bin/env python3
"""
Scraper.py v2.0 Test Script
Test edilecek siteler:
1. Enza Home - Koltuk takımı (mobilya tipi)
2. Hepsiburada - Baharatlık (yeni kategori)
3. Trendyol - Ajanda (yeni kategori)
4. Zara Home - Nevresim (kumaş tipi + JS değişken)
5. Karaca - Çay makinesi (JS-heavy)
6. Normod - Koltuk takımı (3+3+1 tipi)
"""

import sys
sys.path.insert(0, '/home/user/yeni-yuvam')

from scraper import scrape_product

TEST_URLS = [
    {
        'name': '1. ENZA HOME - Koltuk Takımı',
        'url': 'https://www.enzahome.com.tr/aldea-koltuk-takimi-3-1-20260107/',
        'expected': {
            'kategori': 'Mobilya',
            'alt_kategori': 'Koltuk Takımı',
            'features': ['3+1 tipi tespit', 'marka: Enza Home']
        }
    },
    {
        'name': '2. HEPSIBURADA - Baharatlık Seti',
        'url': 'http://hepsiburada.com/mien-bambu-kapakli-12-adet-cam-baharatlik-seti-kavanoz-seti-ve-16-adet-etiket-hediyeli-p-HBCV00006Y57VM',
        'expected': {
            'kategori': 'Mutfak Gereci',
            'alt_kategori': 'Düzenleyici',
            'features': ['Baharatlık algılandı', 'format:webp eklendi mi?']
        }
    },
    {
        'name': '3. TRENDYOL - Ajanda/Planlayıcı',
        'url': 'https://www.trendyol.com/matt-notebook/a5-spiralli-suresiz-planlayici-ajanda-motivasyon-sayfali-potikare-p-797529053?boutiqueId=61&merchantId=113478',
        'expected': {
            'kategori': 'Diğer',
            'alt_kategori': 'Kırtasiye',
            'features': ['Ajanda/planlayıcı algılandı']
        }
    },
    {
        'name': '4. ZARA HOME - Saten Nevresim',
        'url': 'https://www.zarahome.com/tr/cicek-desenli-saten-nevresim-l45131088',
        'expected': {
            'kategori': 'Tekstil',
            'alt_kategori': 'Nevresim Takımı (Saten)',
            'features': ['Kumaş tipi: Saten', 'JS değişken madenciliği']
        }
    },
    {
        'name': '5. KARACA - Çay Makinesi',
        'url': 'https://www.karaca.com/urun/karaca-tea-break-cay-makinesi-inox-siyah',
        'expected': {
            'kategori': 'Mutfak Gereci',
            'alt_kategori': 'Genel',
            'features': ['JS-heavy site', 'window.__NEXT_DATA__']
        }
    },
    {
        'name': '6. NORMOD - 3+3+1 Koltuk Takımı',
        'url': 'https://normod.com/products/klem-butter-blush-cagla-yesili-3-3-1-koltuk-takimi-kadife',
        'expected': {
            'kategori': 'Mobilya',
            'alt_kategori': 'Koltuk Takımı',
            'features': ['3+3+1 tipi regex', 'kadife kumaş']
        }
    }
]

def print_separator(char='=', length=80):
    print(char * length)

def test_scraper():
    print("\n🧪 SCRAPER.PY v2.0 TEST RAPORU")
    print_separator('=')

    results = []

    for i, test in enumerate(TEST_URLS, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}/{len(TEST_URLS)}: {test['name']}")
        print(f"URL: {test['url']}")
        print(f"Beklenen: {test['expected']}")
        print('='*80)

        try:
            result = scrape_product(test['url'])

            if result['success']:
                data = result['data']

                # Başarı durumu
                success = {
                    'test_name': test['name'],
                    'status': '✅ BAŞARILI',
                    'title': data.get('title', 'N/A')[:80],
                    'price': data.get('price', 0),
                    'brand': data.get('brand', 'N/A'),
                    'kategori': data.get('kategori_tahmini', 'N/A'),
                    'alt_kategori': data.get('alt_kategori_tahmini', 'N/A'),
                    'oda': data.get('oda_tahmini', 'N/A'),
                    'image_url': data.get('image_url', 'N/A')[:100],
                    'specs_count': len(data.get('specs', {})),
                    'specs': list(data.get('specs', {}).items())[:5]
                }

                # Sonuçları yazdır
                print(f"\n✅ BAŞARILI")
                print(f"   📝 Başlık: {success['title']}")
                print(f"   💰 Fiyat: {success['price']} TL")
                print(f"   🏷️  Marka: {success['brand']}")
                print(f"   📂 Kategori: {success['kategori']} > {success['alt_kategori']}")
                print(f"   🏠 Oda: {success['oda']}")
                print(f"   🖼️  Görsel: {success['image_url']}")
                print(f"   🔧 Teknik Özellikler: {success['specs_count']} adet")

                if success['specs']:
                    print(f"\n   📋 İlk 5 Özellik:")
                    for key, val in success['specs']:
                        print(f"      - {key}: {val}")

                # Beklenen değerleri kontrol et
                print(f"\n   🎯 Beklenen Kontroller:")
                expected = test['expected']

                if 'kategori' in expected:
                    match = success['kategori'] == expected['kategori']
                    icon = '✅' if match else '❌'
                    status_text = '(DOĞRU)' if match else f"(Beklenen: {expected['kategori']}, Gelen: {success['kategori']})"
                    print(f"      {icon} Kategori: {expected['kategori']} {status_text}")

                if 'alt_kategori' in expected:
                    # Kısmi eşleşme (örn: "Nevresim Takımı (Saten)" içinde "Nevresim" var mı?)
                    match = expected['alt_kategori'].lower() in success['alt_kategori'].lower() or success['alt_kategori'].lower() in expected['alt_kategori'].lower()
                    icon = '✅' if match else '❌'
                    status_text = '(DOĞRU)' if match else f"(Beklenen: {expected['alt_kategori']}, Gelen: {success['alt_kategori']})"
                    print(f"      {icon} Alt Kategori: {expected['alt_kategori']} {status_text}")

                # Özel kontroller
                if 'Baharatlık' in test['name'] and 'hepsiburada' in test['url']:
                    has_format = '/format:webp' in success['image_url'] if success['image_url'] != 'N/A' else False
                    icon = '✅' if has_format else '❌'
                    print(f"      {icon} Hepsiburada format:webp eklendi mi? {has_format}")

                if 'Saten' in test['name']:
                    has_saten = 'saten' in success['alt_kategori'].lower()
                    icon = '✅' if has_saten else '❌'
                    print(f"      {icon} Kumaş tipi (Saten) tespit edildi mi? {has_saten}")

                if '3+3+1' in test['url']:
                    has_type = '3' in success['alt_kategori'] or '3+3+1' in success['title'].lower()
                    icon = '✅' if has_type else '⚠️'
                    print(f"      {icon} Mobilya tipi (3+3+1) tespit edildi mi? {has_type}")

                results.append(success)

            else:
                # Hata durumu
                error = result.get('error', 'Bilinmeyen hata')
                print(f"\n❌ HATA: {error}")
                results.append({
                    'test_name': test['name'],
                    'status': '❌ BAŞARISIZ',
                    'error': error
                })

        except Exception as e:
            print(f"\n💥 İSTİSNA: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append({
                'test_name': test['name'],
                'status': '💥 İSTİSNA',
                'error': str(e)
            })

    # Özet rapor
    print(f"\n\n{'='*80}")
    print("📊 ÖZET RAPOR")
    print('='*80)

    success_count = sum(1 for r in results if r['status'] == '✅ BAŞARILI')
    fail_count = len(results) - success_count

    print(f"\n✅ Başarılı: {success_count}/{len(results)}")
    print(f"❌ Başarısız: {fail_count}/{len(results)}")
    print(f"📈 Başarı Oranı: {(success_count/len(results)*100):.1f}%")

    print(f"\n📋 Detaylı Liste:")
    for r in results:
        print(f"   {r['status']}: {r['test_name']}")
        if r['status'] == '✅ BAŞARILI':
            print(f"      → {r['kategori']} > {r['alt_kategori']}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    test_scraper()
