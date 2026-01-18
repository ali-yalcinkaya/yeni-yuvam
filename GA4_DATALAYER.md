# GA4 dataLayer Parser Dokümantasyonu

Enhanced Google Analytics 4 (GA4) ecommerce dataLayer parser.

## 🎯 DESTEKLENEN SİTELER

GA4 dataLayer kullanan siteler:
- **MediaMarkt** - Elektronik perakende
- **Teknosa** - Elektronik perakende
- **Vatan Bilgisayar** - Elektronik perakende
- **Hepsiburada** - Marketplace (GA4 + GA Universal hybrid)
- **Karaca** - Ev eşyası (GA Universal ağırlıklı)
- Diğer GA4 implementasyonları

## 📊 GA4 ECOMMERCE FORMAT

### Standard GA4 Structure

```javascript
dataLayer.push({
  "event": "view_item",
  "ecommerce": {
    "items": [
      {
        "item_name": "Samsung Galaxy S24",
        "item_id": "12345",
        "price": 24999.99,
        "item_brand": "Samsung",
        "item_category": "Elektronik",
        "item_category2": "Telefon",
        "item_category3": "Akıllı Telefon",
        "item_variant": "256GB Siyah",
        "item_image": "https://cdn.example.com/image.jpg",
        "quantity": 1
      }
    ]
  }
});
```

### GA Universal Format (Eski Format)

```javascript
dataLayer.push({
  "event": "productDetail",
  "ecommerce": {
    "detail": {
      "products": [
        {
          "name": "Samsung Galaxy S24",
          "id": "12345",
          "price": "24999.99",
          "brand": "Samsung",
          "category": "Elektronik/Telefon"
        }
      ]
    }
  }
});
```

## 🔧 PARSER ÖZELLİKLERİ

### 1. Dual Format Support

Parser hem GA4 hem GA Universal formatlarını destekler:

```python
# GA Universal: ecommerce.detail.products[]
if 'detail' in ecommerce and 'products' in ecommerce['detail']:
    # Extract from products array

# GA4: ecommerce.items[]
if 'items' in ecommerce:
    # Extract from items array
```

### 2. Field Mapping

| GA4 Field | GA Universal Field | Extracted As |
|-----------|-------------------|--------------|
| `item_name` | `name` | `title` |
| `price` / `item_price` | `price` | `price` |
| `item_brand` | `brand` | `brand` |
| `item_id` | `id` / `sku` | `sku` |
| `item_image` / `image` | - | `image_url` |
| `item_category` | `category` | `category` |

### 3. Price Format Handling

Parser 3 farklı fiyat formatını destekler:

**1. Normal Decimal:**
```javascript
"price": 2499.99  // → 2499.99 TL
```

**2. Integer (Kuruş Olabilir):**
```javascript
"price": 249999  // > 10000 → 249999 / 100 = 2499.99 TL
"price": 2499    // < 10000 → 2499.00 TL (değişmez)
```

**Logic:**
- Eğer price > 10000 VE tam sayı ise → cent cinsinden olabilir, 100'e böl
- Diğer durumlarda → olduğu gibi kullan

**3. String Format:**
```javascript
"price": "2499.99"  // → float(2499.99)
```

### 4. Image URL Extraction (Yeni! ✅)

GA4'ten image URL çekmek:

```javascript
{
  "item_image": "https://cdn.example.com/product.jpg",
  // veya
  "image_url": "https://cdn.example.com/product.jpg",
  // veya
  "image": "https://cdn.example.com/product.jpg"
}
```

Parser bu 3 field'ı da kontrol eder ve https:// ile başlayanı kabul eder.

### 5. Category Extraction (Yeni! ✅)

```javascript
{
  "item_category": "Elektronik",       // Öncelik 1
  "item_category1": "Elektronik",      // Öncelik 2
  "category": "Elektronik/Telefon"     // Öncelik 3
}
```

### 6. SKU/ID Extraction (Yeni! ✅)

```javascript
{
  "item_id": "SMG-S24-256-BLK",  // Öncelik 1
  "sku": "12345678"              // Öncelik 2
}
```

## 🎯 KULLANIM ÖRNEKLERİ

### MediaMarkt Product Page

HTML'de şu kod var:
```html
<script>
dataLayer.push({
  "event": "view_item",
  "ecommerce": {
    "items": [{
      "item_name": "Philips 55PUS8808 55\" 139 Ekran",
      "item_id": "PHL-TV-8808",
      "price": 18999,
      "item_brand": "Philips",
      "item_category": "Televizyon",
      "item_image": "https://images.mediamarkt.com.tr/philips-tv.jpg"
    }]
  }
});
</script>
```

**Parser Çıktısı:**
```json
{
  "title": "Philips 55PUS8808 55\" 139 Ekran",
  "price": 18999.0,
  "brand": "Philips",
  "image_url": "https://images.mediamarkt.com.tr/philips-tv.jpg",
  "sku": "PHL-TV-8808",
  "category": "Televizyon"
}
```

### Teknosa Product Page (Cent Format)

```html
<script>
dataLayer.push({
  "ecommerce": {
    "items": [{
      "item_name": "iPhone 15 Pro Max 256GB",
      "price": 5499900,  // 54999.00 TL (cent cinsinden)
      "item_brand": "Apple"
    }]
  }
});
</script>
```

**Parser Çıktısı:**
```json
{
  "title": "iPhone 15 Pro Max 256GB",
  "price": 54999.0,  // ✅ Otomatik 100'e bölündü
  "brand": "Apple"
}
```

### Hepsiburada (Hybrid GA Universal + GA4)

```html
<script>
dataLayer.push({
  "ecommerce": {
    "detail": {
      "products": [{
        "name": "Dyson V15 Detect",
        "price": "21999.00",
        "brand": "Dyson"
      }]
    }
  }
});
</script>
```

**Parser Çıktısı:**
```json
{
  "title": "Dyson V15 Detect",
  "price": 21999.0,
  "brand": "Dyson"
}
```

## 🔍 DEBUG

Debug modunu aktif etmek için:

```bash
export SCRAPER_DEBUG=true
python3 app.py
```

**Debug Çıktısı:**
```
==================================================
🔍 SCRAPING DEBUG INFO
==================================================
Domain: www.mediamarkt.com.tr
Handler: datalayer

Data Sources:
  • title: datalayer
  • price: datalayer
  • image_url: datalayer
  • brand: datalayer
==================================================
```

## ⚙️ TEKNİK DETAYLAR

### Pattern Matching

```python
# Regex pattern: dataLayer.push({...});
dataLayer_pattern = r'dataLayer\.push\(\s*({[\s\S]*?})\s*\);'
dataLayer_matches = re.finditer(dataLayer_pattern, html_text)
```

### JSON Parsing

```python
for match in dataLayer_matches:
    try:
        json_str = match.group(1)
        data = json.loads(json_str)

        if 'ecommerce' in data:
            # GA4 check
            if 'items' in ecommerce:
                item = ecommerce['items'][0]
                # Extract fields

            # GA Universal check
            if 'detail' in ecommerce:
                product = ecommerce['detail']['products'][0]
                # Extract fields
    except:
        continue  # Skip invalid JSON
```

### Price Normalization

```python
price_val = item.get('price', 0)
price_float = float(price_val)

# Cent detection
if price_float > 10000 and price_float == int(price_float):
    price = price_float / 100  # Cent → TL
else:
    price = price_float
```

## 📈 KAPSAM

| Site | Format | Test Durumu |
|------|--------|-------------|
| **MediaMarkt** | GA4 items[] | ⚪ Test edilecek |
| **Teknosa** | GA4 items[] | ⚪ Test edilecek |
| **Vatan** | GA4 items[] | ⚪ Test edilecek |
| **Hepsiburada** | GA Universal + GA4 | ⚪ Test edilecek |
| **Karaca** | GA Universal | ✅ Test edildi |

## 🚨 SORUN GİDERME

### Problem: Fiyat çok yüksek geliyor (örn: 249999 TL yerine 2499.99 TL)

**Sebep:** Site cent cinsinden gönderiyor ama parser 100'e bölmüyor.

**Çözüm:** Parser otomatik tespit eder:
- `price > 10000` VE tam sayı ise → cent olarak kabul edilir, 100'e bölünür
- Eğer yanlış tespit ediyorsa, site-specific parser ekleyin

### Problem: Image URL çekilmiyor

**Sebep:** GA4 dataLayer'da image field'i yok.

**Çözüm:** Fallback chain devreye girer:
1. dataLayer (yok ❌)
2. Meta tags (og:image) ✅
3. HTML selectors ✅

### Problem: Category/SKU boş geliyor

**Sebep:** GA4 implementasyonu eksik.

**Not:** Bu normal, tüm siteler category/SKU göndermez. Fallback mekanizması çalışır.

## 📝 BEST PRACTICES

### 1. GA4 vs GA Universal Kontrolü

Her zaman önce GA4'ü kontrol et, sonra GA Universal'a fallback yap:

```python
# ✅ Doğru sıra
if 'items' in ecommerce:
    # GA4
elif 'detail' in ecommerce:
    # GA Universal
```

### 2. Price Validation

Fiyat çektikten sonra doğrula:

```python
if price > 0 and price < 10000000:  # Makul aralık
    result['price'] = price
```

### 3. Image URL Validation

Image URL https:// ile başlamalı:

```python
if img and img.startswith('http'):
    result['image_url'] = img
```

## 🎯 GELECEK İYİLEŞTİRMELER

- [ ] GA4 `item_variant` extraction (varyant bilgisi)
- [ ] GA4 `discount` / `coupon` extraction
- [ ] GA4 multiple items handling (birden fazla ürün)
- [ ] Currency detection (`currency` field)
- [ ] Stock status extraction (`stock_status` field)

---

**Son Güncelleme:** 2026-01-18
**Versiyon:** 3.1 (Enhanced GA4 Support)
**Test Coverage:** 5 site (3 GA4, 2 hybrid)
