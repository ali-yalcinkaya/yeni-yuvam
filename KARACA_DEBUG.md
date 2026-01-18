# Karaca Debug Rehberi

## Sorun
Karaca sitesinden sadece `teknik_ozellikler` çekiliyor, `urun_adi`, `fiyat`, `marka`, `resim_url` boş.

## Debug Modu ile Test

### Yöntem 1: Flask Uygulamasında Debug

1. **Flask'ı debug modunda başlat:**
   ```bash
   export SCRAPER_DEBUG=true
   python3 app.py
   ```

2. **Tarayıcıda ürün ekle:**
   - URL: `https://www.karaca.com/urun/karaca-tea-break-cay-makinesi-inox-siyah`
   - Scrape butonuna bas

3. **Terminal/Console'u izle** - Debug çıktısı göreceksin:
   ```
   ✅ __NEXT_DATA__ bulundu! Keys: ['props', 'page', 'query', ...]
      pageProps keys: ['product', 'relatedProducts', ...]
      product keys: ['name', 'price', 'image', ...]
      name: Karaca Tea Break Çay Makinesi
      price: 1499.90
   ```

4. **Eğer "⚠️ __NEXT_DATA__ script tag bulunamadı!" görüyorsan:**
   - Karaca Next.js kullanmıyor demektir
   - Generic HTML parser kullanmalıyız

### Yöntem 2: Python Script ile Test

```python
import os
os.environ['SCRAPER_DEBUG'] = 'true'

from scraper import scrape_product
import json

result = scrape_product('https://www.karaca.com/urun/karaca-tea-break-cay-makinesi-inox-siyah')
print(json.dumps(result, indent=2, ensure_ascii=False))
```

## Beklenen Debug Çıktısı

### Başarılı Durum:
```
✅ __NEXT_DATA__ bulundu! Keys: ['props', 'page', 'query']
   pageProps keys: ['product', 'relatedProducts']
   product keys: ['name', 'price', 'image', 'brand']
   name: Karaca Tea Break Çay Makinesi Inox Siyah
   price: 1499.90
```

### Sorunlu Durum 1 (Script Yok):
```
⚠️ __NEXT_DATA__ script tag bulunamadı!
```
**Çözüm**: Karaca için Generic HTML selector'lar ekleyeceğiz

### Sorunlu Durum 2 (Veri Yapısı Farklı):
```
✅ __NEXT_DATA__ bulundu! Keys: ['props', 'page']
   pageProps keys: ['initialState', 'config']
   ⚠️ product key bulunamadı!
   Alternatif aramalar:
      Bulundu: productData -> <class 'dict'>
```
**Çözüm**: Doğru key'i bulup parser'ı güncelleyeceğiz

## Çıktıyı Bana Gönder

Debug çıktısını buraya yapıştır, hemen düzeltelim:

```
[Debug çıktısını buraya yapıştır]
```

## Manuel HTML İnceleme (Alternatif)

Eğer debug çalışmazsa:

1. Tarayıcıda siteyi aç
2. Sağ tık → "Kaynağı Görüntüle" (View Page Source)
3. Ctrl+F ile ara:
   - `__NEXT_DATA__` → Var mı?
   - `<h1` → Başlık nerede?
   - `class="price"` → Fiyat nerede?

4. Bulduklarını bana söyle:
   - Başlık hangi tag'de? Örn: `<h1 class="product-title">...</h1>`
   - Fiyat hangi tag'de? Örn: `<span class="price">1499,90 TL</span>`
   - Görsel hangi tag'de? Örn: `<img src="..." class="main-image">`

## Hızlı Çözüm

Eğer __NEXT_DATA__ yoksa, Karaca'yı generic HTML parser'a ekleyebiliriz:

```python
# Karaca için özel selector'lar
if 'karaca' in domain:
    title_el = soup.select_one('h1.product-name')  # veya doğru selector
    price_el = soup.select_one('.price-value')      # veya doğru selector
    # ...
```

**Hadi test et ve sonuçları paylaş!** 🚀
