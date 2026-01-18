#!/usr/bin/env python3
"""
Karaca Debug - Next.js __NEXT_DATA__ yapısını incele
Kullanıcının aldığı boş sonucun nedenini bul
"""

# Karaca sitesinin yapısı için debug önerileri
print("""
=== KARACA DEBUG REHBERİ ===

SORUN: urun_adi, fiyat, marka, resim_url boş geliyor

OLASI NEDENLER:
1. __NEXT_DATA__ script tag'i farklı formatta olabilir
2. Karaca Next.js kullanmıyor olabilir
3. Data yapısı değişmiş olabilir

MANUEL DEBUG ADIMI:

1. Flask uygulamasını çalıştır
2. Tarayıcıda şu URL'yi aç:
   https://www.karaca.com/urun/karaca-tea-break-cay-makinesi-inox-siyah

3. Tarayıcıda sağ tık → "Kaynağı Görüntüle" (View Page Source)

4. Ctrl+F ile ara:
   - "__NEXT_DATA__" → Varsa Next.js kullanıyor
   - "window.dataLayer" → Google Tag Manager
   - "product" → Ürün datası
   - "application/ld+json" → JSON-LD structured data

5. Eğer __NEXT_DATA__ yoksa:
   - Başlık nereden geliyor? (h1, .product-title, vb.)
   - Fiyat nereden geliyor? (.price, .product-price, vb.)
   - Görsel nereden geliyor? (img tag'leri)

HIZLI TEST:

Python'dan şunu çalıştır:

```python
from scraper import scrape_product
import json

# Debug mode ile test
result = scrape_product('https://www.karaca.com/urun/karaca-tea-break-cay-makinesi-inox-siyah')

# Detaylı sonuç
print(json.dumps(result, indent=2, ensure_ascii=False))
```

VEYA debug_scraper.py kullan (eğer varsa):

```bash
python3 debug_scraper.py https://www.karaca.com/urun/karaca-tea-break-cay-makinesi-inox-siyah
```

BEKLENTİ:
- Başlık: "Karaca Tea Break Çay Makinesi Inox Siyah"
- Fiyat: ~1000-2000 TL arası
- Marka: "Karaca"
- Görsel: https://... ile başlayan tam URL

ÇÖZÜM ÖNERİSİ:
Eğer __NEXT_DATA__ yoksa veya farklı formattaysa, Karaca için:
1. Generic HTML parser'a özel selector'lar ekleyelim
2. Veya Karaca-specific parser yazalım

BEKLİYORUM:
Lütfen tarayıcıdan kaynak kodunu kontrol et ve:
- __NEXT_DATA__ var mı?
- Başlık hangi tag'de? (h1, h2, .title, vb.)
- Fiyat hangi class'ta? (.price, .product-price, vb.)

Bu bilgileri ver, hemen düzeltelim!
""")
