# Error Handling & Debug Rehberi

Scraper v3.1 ile gelen gelişmiş hata yönetimi ve debug özellikleri.

## 🎯 YENİ ÖZELLİKLER

### 1. Fallback Chain Logging ✅
Her field için hangi veri kaynağının kullanıldığını takip eder.

**Öncelik Sırası:**
```
Site-Specific Parser > JSON-LD > Meta Tags > HTML Selectors
```

### 2. Debug Mode ✅
Detaylı scraping bilgisi görmek için debug modu aktif et.

**Kullanım:**
```bash
export SCRAPER_DEBUG=true
python3 app.py
```

**Debug Çıktısı:**
```
==================================================
🔍 SCRAPING DEBUG INFO
==================================================
Domain: www.karaca.com
Handler: datalayer

Data Sources:
  • title: datalayer
  • price: datalayer
  • image_url: meta-tags
  • brand: datalayer
==================================================
```

### 3. Rate Limiting ✅
API çağrıları arası otomatik bekleme.

**Ayarlar:**
- Minimum interval: 1.5 saniye
- Domain bazlı tracking
- Otomatik bekleme mesajı

**Örnek:**
```
⏱️  Rate limit: 0.8s bekliyor (trendyol.com)
```

### 4. Cache Sistemi ✅
Aynı URL için 5 dakika cache.

**Özellikler:**
- TTL: 300 saniye (5 dakika)
- In-memory cache
- Otomatik expired cache temizliği
- Cache hit mesajı

**Örnek:**
```
✅ Cache hit: https://www.karaca.com/urun/cay-makinesi
```

---

## 🐛 HATA MESAJLARI

### Trendyol API Hataları

```
⚠️ Trendyol: Product ID bulunamadı (URL pattern: -p-XXXXX)
```
**Çözüm:** URL formatı doğru mu kontrol et (`-p-123456` pattern olmalı)

```
⚠️ Trendyol API: HTTP 404
```
**Çözüm:** Ürün ID yanlış veya ürün kaldırılmış

```
⚠️ Trendyol API: Timeout (10 saniye)
```
**Çözüm:** İnternet bağlantısı veya Trendyol API'si yavaş

```
⚠️ Trendyol API: Network error - ...
```
**Çözüm:** Bağlantı problemi, tekrar dene

```
⚠️ Trendyol API: JSON parse error - ...
```
**Çözüm:** API yanıtı bozuk, Trendyol tarafında sorun olabilir

```
⚠️ Trendyol API: 'result' field bulunamadı
```
**Çözüm:** API yanıt formatı değişmiş, parser güncellemesi gerekebilir

```
⚠️ Trendyol API: Başlık boş
```
**Uyarı:** API başlık döndürmedi, fallback devreye girecek

```
⚠️ Trendyol API: Fiyat bulunamadı
```
**Uyarı:** API fiyat döndürmedi, fallback devreye girecek

### IKEA Parser Hataları

```
⚠️ IKEA: og:title meta tag bulunamadı
```
**Uyarı:** Meta tag eksik, HTML selector denenecek

```
⚠️ IKEA: Fiyat bulunamadı (selectors: .pip-price, .price-module__container, ...)
```
**Uyarı:** Tüm fiyat selector'ları başarısız, fallback devreye girecek

```
⚠️ IKEA: Başlık boş
```
**Hata:** Hiçbir kaynaktan başlık alınamadı

```
⚠️ IKEA: Geçerli fiyat bulunamadı
```
**Hata:** Fiyat 0 veya negatif

### Generic Parser Hataları

```
⚠️ datalayer parser error: ...
```
**Uyarı:** Site-specific parser başarısız, generic parser devreye girecek

```
⚠️ api_trendyol parser error: ...
```
**Uyarı:** API parser başarısız, generic parser devreye girecek

---

## 📊 VERİ KAYNAĞI TRAKİNG

Debug modunda her field için kullanılan kaynak gösterilir:

```python
{
  "title": "Karaca Tea Break Çay Makinesi",
  "_debug": {
    "handler": "datalayer",
    "parser_used": "datalayer",
    "data_sources": {
      "title": "datalayer",      # dataLayer'dan alındı
      "price": "datalayer",      # dataLayer'dan alındı
      "image_url": "meta-tags",  # Meta tag'den alındı
      "brand": "datalayer",      # dataLayer'dan alındı
      "description": "json-ld"   # JSON-LD'den alındı
    }
  }
}
```

**Veri Kaynağı Değerleri:**
- `api_trendyol` - Trendyol Public API
- `shopify` - Shopify JSON API
- `datalayer` - Google Tag Manager
- `nextjs` - __NEXT_DATA__ script
- `woocommerce` - WooCommerce HTML
- `ikea` - IKEA özel parser
- `json-ld` - Schema.org JSON-LD
- `meta-tags` - OG/Product meta tags
- `html-selectors` - Generic HTML selectors

---

## 🔧 DEBUG KULLANIM ÖRNEKLERİ

### Flask Uygulamasında Debug

```bash
export SCRAPER_DEBUG=true
python3 app.py
```

Tarayıcıda ürün ekle, terminal'de detaylı çıktıyı gör.

### Python Script'te Debug

```python
import os
os.environ['SCRAPER_DEBUG'] = 'true'

from scraper import scrape_product
import json

result = scrape_product('https://www.karaca.com/urun/cay-makinesi')
print(json.dumps(result, indent=2, ensure_ascii=False))
```

### Cache Test

```python
from scraper import scrape_product

# İlk çağrı - HTTP isteği yapar
result1 = scrape_product('https://www.example.com/product')
# ✅ Cache'e kaydedildi

# İkinci çağrı (5 dk içinde) - Cache'den döner
result2 = scrape_product('https://www.example.com/product')
# ✅ Cache hit: https://www.example.com/product
```

### Rate Limit Test

```python
import time
from scraper import scrape_product

# Aynı domain'den hızlı ardışık istekler
result1 = scrape_product('https://www.trendyol.com/product-1')
result2 = scrape_product('https://www.trendyol.com/product-2')
# ⏱️  Rate limit: 1.2s bekliyor (trendyol.com)
```

---

## 📈 PERFORMANS OPTİMİZASYONU

### Cache İstatistikleri

Cache sistemi sayesinde:
- **5 dakika içinde aynı URL:** HTTP isteği YOK
- **Hız:** ~1000x daha hızlı (cache'den okuma)
- **Yük:** API/site yükü azalır

### Rate Limiting Faydaları

- **Anti-ban:** Sitelerin rate limit korumasını tetiklemez
- **Saygılı scraping:** Server'a aşırı yük bindirmez
- **Stabilite:** 403/429 hatalarını önler

---

## 🎯 BEST PRACTICES

### 1. Debug Modu Sadece Development'ta Kullan

```python
# ❌ Production'da YAPMA
os.environ['SCRAPER_DEBUG'] = 'true'

# ✅ Sadece development/testing
if os.getenv('ENV') == 'development':
    os.environ['SCRAPER_DEBUG'] = 'true'
```

### 2. Cache'i Temizle (Gerekirse)

```python
from scraper import SCRAPE_CACHE

# Cache'i manuel temizle
SCRAPE_CACHE.clear()
```

### 3. Rate Limit'i Ayarla (Gerekirse)

```python
from scraper import MIN_REQUEST_INTERVAL

# Daha yavaş scraping için artır
MIN_REQUEST_INTERVAL = 3.0  # 3 saniye
```

---

## 🚨 SORUN GİDERME

### Problem: Cache güncellenmiyor

```python
# Çözüm: URL'den önce cache'i temizle
from scraper import SCRAPE_CACHE
del SCRAPE_CACHE['https://example.com/product']
```

### Problem: Rate limit çok yavaş

```python
# Çözüm: MIN_REQUEST_INTERVAL'i azalt
from scraper import MIN_REQUEST_INTERVAL
MIN_REQUEST_INTERVAL = 0.5  # 500ms
```

### Problem: Debug mesajları gözükmüyor

```bash
# Çözüm 1: Environment variable doğru set edilmiş mi?
echo $SCRAPER_DEBUG

# Çözüm 2: Python içinden set et
python3 -c "import os; os.environ['SCRAPER_DEBUG']='true'; exec(open('app.py').read())"
```

---

## 📝 NOTLAR

1. **Cache TTL:** Varsayılan 5 dakika, `CACHE_TTL_SECONDS` ile değiştirilebilir
2. **Rate Limit:** Varsayılan 1.5 saniye, `MIN_REQUEST_INTERVAL` ile değiştirilebilir
3. **Debug Metadata:** Sadece `SCRAPER_DEBUG=true` olduğunda `_debug` field eklenir
4. **Cache Temizliği:** Her 10 istekten birinde otomatik expired cache temizliği yapılır
5. **Rate Limit Domain Bazlı:** `trendyol.com` ve `ikea.com.tr` farklı rate limit'e sahip

---

**Son Güncelleme:** 2026-01-18
**Versiyon:** 3.1 (Error Handling + Caching)
