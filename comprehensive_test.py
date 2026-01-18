#!/usr/bin/env python3
"""
Kapsamlı Scraper Test Suite
Türkiye'deki 30+ ev eşyası e-ticaret sitesini test eder
"""

import sys
sys.path.insert(0, '/home/user/yeni-yuvam')

from scraper import scrape_product
import json

# 30+ Site Test URL'leri (Kategori bazlı)
TEST_SITES = [
    # ========== MARKETPLACE (4 site) ==========
    {
        'category': '🛒 MARKETPLACE',
        'sites': [
            {
                'name': 'Trendyol',
                'url': 'https://www.trendyol.com/casio/edifice-efr-526l-7avudf-kol-saati-p-3143273',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Elektronik', 'has_price': True, 'has_image': True}
            },
            {
                'name': 'Hepsiburada',
                'url': 'https://www.hepsiburada.com/tefal-comfort-max-inox-7-parca-tencere-seti-p-HBV00000IQRZ3',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Mutfak', 'has_price': True, 'image_format': 'webp'}
            },
            {
                'name': 'N11',
                'url': 'https://www.n11.com/urun/philips-hd9200-90-airfryer-fritoz-2163428',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Mutfak', 'has_price': True}
            },
            {
                'name': 'Çiçeksepeti',
                'url': 'https://www.ciceksepeti.com/karaca-fine-pearl-cay-takimi-31-parca',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Mutfak', 'has_price': True}
            }
        ]
    },

    # ========== BEYAZ EŞYA (7 site) ==========
    {
        'category': '🏠 BEYAZ EŞYA',
        'sites': [
            {
                'name': 'Arçelik',
                'url': 'https://www.arcelik.com.tr/camasir-makinesi/9143-yn-a-9-kg-1400-devir-camasir-makinesi',
                'platform': 'Generic HTML + WebP Optimizer',
                'expected': {'kategori': 'Beyaz Eşya', 'image_format': 'webp', 'image_size': '2000x2000'}
            },
            {
                'name': 'Beko',
                'url': 'https://www.beko.com.tr/urunler/buzdolaplari/rcna400e40zxb-tek-kapili-buzdolabi',
                'platform': 'Generic HTML + WebP Optimizer',
                'expected': {'kategori': 'Beyaz Eşya', 'image_format': 'webp'}
            },
            {
                'name': 'Vestel',
                'url': 'https://www.vestel.com.tr/ev-aletleri/beyaz-esya/camasir-makinesi/9614-te',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Beyaz Eşya', 'has_price': True}
            },
            {
                'name': 'Bosch',
                'url': 'https://www.bosch-home.com.tr/urun-listesi/bulaşık-makineleri/ankastre-bulaşık-makineleri/60-cm-ankastre-bulaşık-makineleri/SMV4HTX31E',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Beyaz Eşya'}
            },
            {
                'name': 'Siemens',
                'url': 'https://www.siemens-home.bsh-group.com/tr/urun-listesi/bulasik-makineleri/ankastre-bulasik-makineleri/60-cm-tam-ankastre-bulasik-makineleri/SN65ZX49CE',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Beyaz Eşya'}
            },
            {
                'name': 'Samsung',
                'url': 'https://www.samsung.com/tr/washing-machines/front-load/ww90t554dan-s3/',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Beyaz Eşya'}
            },
            {
                'name': 'Altus',
                'url': 'https://www.altus.com.tr/camasir-makinesi/al-9123-dx-9-kg-1200-devir-camasir-makinesi',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Beyaz Eşya'}
            }
        ]
    },

    # ========== MOBİLYA - SHOPIFY (4 site) ==========
    {
        'category': '🪑 MOBİLYA (Shopify)',
        'sites': [
            {
                'name': 'Enza Home',
                'url': 'https://www.enzahome.com.tr/aldea-koltuk-takimi-3-1-20260107/',
                'platform': 'Shopify API',
                'expected': {'kategori': 'Mobilya', 'alt_kategori': 'Koltuk', 'has_price': True}
            },
            {
                'name': 'Normod',
                'url': 'https://normod.com/products/klem-butter-blush-cagla-yesili-3-3-1-koltuk-takimi-kadife',
                'platform': 'Shopify API',
                'expected': {'kategori': 'Mobilya', 'furniture_type': '3+3+1', 'fabric': 'kadife'}
            },
            {
                'name': 'Vivense',
                'url': 'https://www.vivense.com/monaco-koltuk-takimi-3-2-1',
                'platform': 'Shopify API',
                'expected': {'kategori': 'Mobilya', 'has_price': True}
            },
            {
                'name': 'Alfemo',
                'url': 'https://www.alfemo.com.tr/koltuk-takimlari/vienza-koltuk-takimi',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Mobilya'}
            }
        ]
    },

    # ========== MOBİLYA - DİĞER (4 site) ==========
    {
        'category': '🛋️ MOBİLYA (Diğer)',
        'sites': [
            {
                'name': 'IKEA',
                'url': 'https://www.ikea.com.tr/tr/urunler/oturma-odasi-mobilyalari/koltuk-takimlari/kivik-koltuk-takimi-hillared-koyu-mavi-art-s89277563',
                'platform': 'WooCommerce/Custom',
                'expected': {'kategori': 'Mobilya'}
            },
            {
                'name': 'Bellona',
                'url': 'https://www.bellona.com.tr/koltuk-takimi/bello-koltuk-takimi',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Mobilya'}
            },
            {
                'name': 'İstikbal',
                'url': 'https://www.istikbal.com.tr/koltuk-takimlari/oturma-gruplari/stella-kose-koltuk',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Mobilya'}
            },
            {
                'name': 'Doğtaş',
                'url': 'https://www.dogtas.com/koltuk-takimlari/modern-koltuk-takimlari/stella-koltuk-takimi',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Mobilya'}
            }
        ]
    },

    # ========== EV TEKSTİLİ (5 site) ==========
    {
        'category': '🏡 EV TEKSTİLİ',
        'sites': [
            {
                'name': 'English Home',
                'url': 'https://www.englishhome.com/super-soft-cift-kisilik-pike-takimi-200x220-cm-beyaz',
                'platform': 'WooCommerce',
                'expected': {'kategori': 'Tekstil', 'has_price': True}
            },
            {
                'name': 'Madame Coco',
                'url': 'https://www.madamecoco.com.tr/florenza-pamuk-saten-cift-kisilik-nevresim-takimi-beyaz',
                'platform': 'WooCommerce',
                'expected': {'kategori': 'Tekstil', 'fabric': 'pamuk'}
            },
            {
                'name': 'Yataş',
                'url': 'https://www.yatas.com.tr/selena-select-ranforce-cift-kisilik-nevresim-takimi',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Tekstil', 'fabric': 'ranforce'}
            },
            {
                'name': 'Taç',
                'url': 'https://www.tac.com.tr/pamuklu-cift-kisilik-nevresim-takimi',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Tekstil'}
            },
            {
                'name': 'Chakra',
                'url': 'https://www.chakra.com.tr/urun/pamuk-saten-nevresim-takimi',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Tekstil'}
            }
        ]
    },

    # ========== DEKORASYON (3 site) ==========
    {
        'category': '🎨 DEKORASYON',
        'sites': [
            {
                'name': 'Zara Home',
                'url': 'https://www.zarahome.com/tr/cicek-desenli-saten-nevresim-l45131088',
                'platform': 'Next.js __NEXT_DATA__',
                'expected': {'kategori': 'Tekstil', 'fabric': 'saten'}
            },
            {
                'name': 'Karaca',
                'url': 'https://www.karaca.com/urun/karaca-tea-break-cay-makinesi-inox-siyah',
                'platform': 'Next.js __NEXT_DATA__',
                'expected': {'kategori': 'Mutfak', 'has_price': True}
            },
            {
                'name': 'H&M Home',
                'url': 'https://www2.hm.com/tr_tr/productpage.1074402002.html',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Tekstil'}
            }
        ]
    },

    # ========== DIY & YAPI MARKET (2 site) ==========
    {
        'category': '🔨 DIY & YAPI MARKET',
        'sites': [
            {
                'name': 'Koçtaş',
                'url': 'https://www.koctas.com.tr/dewalt-dwe575k-1600w-190mm-sirkuler-testere/p/10022838',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Elektronik'}
            },
            {
                'name': 'Bauhaus',
                'url': 'https://www.bauhaus.com.tr/makita-hr2470-sds-plus-elektriki-testere',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Elektronik'}
            }
        ]
    },

    # ========== ELEKTRONİK (3 site) ==========
    {
        'category': '🔌 ELEKTRONİK',
        'sites': [
            {
                'name': 'Vatan Bilgisayar',
                'url': 'https://www.vatanbilgisayar.com/apple-iphone-15-pro-max-256-gb-mavi-titanium.html',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Elektronik', 'has_price': True}
            },
            {
                'name': 'Teknosa',
                'url': 'https://www.teknosa.com/samsung-galaxy-s23-ultra-256-gb-p-125083744',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Elektronik', 'has_price': True}
            },
            {
                'name': 'MediaMarkt',
                'url': 'https://www.mediamarkt.com.tr/tr/product/_apple-iphone-15-128-gb-mavi-mphe3tu-a-1234567890.html',
                'platform': 'Generic HTML',
                'expected': {'kategori': 'Elektronik'}
            }
        ]
    }
]

def print_separator(char='=', length=100):
    print(char * length)

def validate_result(data, expected):
    """Test sonuçlarını validate et"""
    validations = []

    # Kategori kontrolü
    if 'kategori' in expected:
        match = expected['kategori'].lower() in data.get('kategori_tahmini', '').lower()
        validations.append({
            'test': 'Kategori',
            'expected': expected['kategori'],
            'actual': data.get('kategori_tahmini', 'N/A'),
            'passed': match
        })

    # Fiyat kontrolü
    if expected.get('has_price'):
        has_price = data.get('price', 0) > 0
        validations.append({
            'test': 'Fiyat',
            'expected': 'Var',
            'actual': f"{data.get('price', 0)} TL" if has_price else 'YOK',
            'passed': has_price
        })

    # Görsel kontrolü
    if expected.get('has_image'):
        has_image = bool(data.get('image_url'))
        validations.append({
            'test': 'Görsel',
            'expected': 'Var',
            'actual': 'Var' if has_image else 'YOK',
            'passed': has_image
        })

    # Görsel format kontrolü
    if 'image_format' in expected:
        image_url = data.get('image_url', '')
        has_format = expected['image_format'] in image_url
        validations.append({
            'test': 'Görsel Format',
            'expected': expected['image_format'],
            'actual': 'webp' if 'webp' in image_url else 'diğer',
            'passed': has_format
        })

    # Kumaş tipi kontrolü
    if 'fabric' in expected:
        fabric_found = expected['fabric'].lower() in data.get('alt_kategori_tahmini', '').lower()
        validations.append({
            'test': 'Kumaş Tipi',
            'expected': expected['fabric'],
            'actual': data.get('alt_kategori_tahmini', 'N/A'),
            'passed': fabric_found
        })

    # Mobilya tipi kontrolü
    if 'furniture_type' in expected:
        furniture_found = expected['furniture_type'] in data.get('alt_kategori_tahmini', '')
        validations.append({
            'test': 'Mobilya Tipi',
            'expected': expected['furniture_type'],
            'actual': data.get('alt_kategori_tahmini', 'N/A'),
            'passed': furniture_found
        })

    return validations

def run_comprehensive_test():
    """Kapsamlı test çalıştır"""
    print("\n" + "="*100)
    print("🧪 KAPSAMLI SCRAPER TESTİ - 30+ TÜRKİYE E-TİCARET SİTESİ")
    print("="*100 + "\n")

    all_results = []
    category_stats = {}

    total_sites = sum(len(cat['sites']) for cat in TEST_SITES)
    current_site = 0

    for category_group in TEST_SITES:
        category_name = category_group['category']
        print(f"\n{'='*100}")
        print(f"{category_name}")
        print('='*100)

        category_results = []

        for site in category_group['sites']:
            current_site += 1
            print(f"\n[{current_site}/{total_sites}] {site['name']} ({site['platform']})")
            print(f"URL: {site['url'][:80]}...")

            try:
                result = scrape_product(site['url'])

                if result['success']:
                    data = result['data']

                    # Validasyonlar
                    validations = validate_result(data, site['expected'])
                    all_passed = all(v['passed'] for v in validations)

                    # Sonuç
                    test_result = {
                        'site': site['name'],
                        'platform': site['platform'],
                        'category': category_name,
                        'status': '✅ BAŞARILI' if all_passed else '⚠️ KISMİ',
                        'title': data.get('title', 'N/A')[:60],
                        'price': data.get('price', 0),
                        'image': bool(data.get('image_url')),
                        'validations': validations
                    }

                    # Kısa özet yazdır
                    status_icon = '✅' if all_passed else '⚠️'
                    print(f"{status_icon} Başlık: {test_result['title']}")
                    print(f"   Fiyat: {test_result['price']} TL")
                    print(f"   Görsel: {'✅' if test_result['image'] else '❌'}")

                    # Validasyon sonuçları
                    for v in validations:
                        icon = '✅' if v['passed'] else '❌'
                        print(f"   {icon} {v['test']}: {v['actual']} (Beklenen: {v['expected']})")

                else:
                    test_result = {
                        'site': site['name'],
                        'platform': site['platform'],
                        'category': category_name,
                        'status': '❌ BAŞARISIZ',
                        'error': result.get('error', 'Bilinmeyen hata')
                    }
                    print(f"❌ HATA: {test_result['error']}")

            except Exception as e:
                test_result = {
                    'site': site['name'],
                    'platform': site['platform'],
                    'category': category_name,
                    'status': '💥 İSTİSNA',
                    'error': str(e)
                }
                print(f"💥 İSTİSNA: {str(e)}")

            category_results.append(test_result)
            all_results.append(test_result)

        # Kategori istatistikleri
        success_count = sum(1 for r in category_results if '✅' in r['status'])
        partial_count = sum(1 for r in category_results if '⚠️' in r['status'])
        fail_count = sum(1 for r in category_results if '❌' in r['status'] or '💥' in r['status'])

        category_stats[category_name] = {
            'total': len(category_results),
            'success': success_count,
            'partial': partial_count,
            'fail': fail_count
        }

        print(f"\n📊 {category_name} Özet: ✅ {success_count}  ⚠️ {partial_count}  ❌ {fail_count}  Toplam: {len(category_results)}")

    # GENEL ÖZET RAPOR
    print("\n\n" + "="*100)
    print("📊 GENEL ÖZET RAPOR")
    print("="*100 + "\n")

    total_success = sum(1 for r in all_results if '✅' in r['status'])
    total_partial = sum(1 for r in all_results if '⚠️' in r['status'])
    total_fail = sum(1 for r in all_results if '❌' in r['status'] or '💥' in r['status'])

    print(f"📈 TOPLAM İSTATİSTİKLER:")
    print(f"   ✅ Tam Başarılı: {total_success}/{total_sites} ({total_success/total_sites*100:.1f}%)")
    print(f"   ⚠️ Kısmi Başarılı: {total_partial}/{total_sites} ({total_partial/total_sites*100:.1f}%)")
    print(f"   ❌ Başarısız: {total_fail}/{total_sites} ({total_fail/total_sites*100:.1f}%)")
    print(f"   🎯 Genel Başarı Oranı: {(total_success+total_partial)/total_sites*100:.1f}%")

    print(f"\n📋 KATEGORİ BAZLI İSTATİSTİKLER:")
    for cat_name, stats in category_stats.items():
        success_rate = (stats['success'] + stats['partial']) / stats['total'] * 100
        print(f"\n{cat_name}:")
        print(f"   ✅ {stats['success']}  ⚠️ {stats['partial']}  ❌ {stats['fail']}  Toplam: {stats['total']}")
        print(f"   Başarı Oranı: {success_rate:.1f}%")

    print(f"\n📋 PLATFORM BAZLI BAŞARI ORANLARI:")
    platforms = {}
    for r in all_results:
        platform = r['platform']
        if platform not in platforms:
            platforms[platform] = {'success': 0, 'total': 0}
        platforms[platform]['total'] += 1
        if '✅' in r['status'] or '⚠️' in r['status']:
            platforms[platform]['success'] += 1

    for platform, stats in sorted(platforms.items()):
        rate = stats['success'] / stats['total'] * 100
        print(f"   {platform}: {stats['success']}/{stats['total']} ({rate:.1f}%)")

    print("\n" + "="*100 + "\n")

    # JSON rapor kaydet
    with open('/home/user/yeni-yuvam/test_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_sites': total_sites,
            'success': total_success,
            'partial': total_partial,
            'fail': total_fail,
            'category_stats': category_stats,
            'platform_stats': platforms,
            'detailed_results': all_results
        }, f, ensure_ascii=False, indent=2)

    print("💾 Detaylı rapor kaydedildi: test_results.json\n")

if __name__ == '__main__':
    run_comprehensive_test()
