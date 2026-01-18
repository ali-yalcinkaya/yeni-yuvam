# Veri Kaynağı Öncelik Listesi

Scraper'ın her platform için kullandığı veri kaynaklarının öncelik sırası.

## 🎯 GENEL KURAL

**Cascade Yaklaşımı**: En güvenilir kaynaktan başla, yoksa bir sonrakine geç.

```
Site-Özel Parser > JSON-LD > Meta Tags > HTML Selectors
```

---

## 📊 PLATFORM BAZLI ÖNCELİKLER

### 1. SHOPIFY SİTELERİ
**Sites**: Enza Home, Normod, Vivense, Alfemo

**Veri Kaynağı Priority:**
```
1️⃣ Shopify JSON API (/products/{handle}.json)
   ✅ En güvenilir
   ✅ Tam yapılandırılmış veri
   ✅ Variants, images, pricing

2️⃣ Klaviyo Tracking (var item = {...})
   ✅ Shopify sitelerinin çoğunda var
   ✅ Name, Price, Brand, ImageURL
   ⚠️ Fiyat formatı: "101.360TL"

3️⃣ Meta Tags (og:, product:)
   ⚠️ Temel bilgiler
   ❌ Variants/options yok

4️⃣ HTML Selectors
   ❌ Shopify JS-heavy olduğu için güvensiz
```

**Örnek Kod:**
```javascript
// Shopify JSON
{
  "product": {
    "title": "Klem Koltuk Takımı",
    "variants": [{"price": "101360.00"}],
    "images": [{"src": "..."}]
  }
}

// Klaviyo Tracking
var item = {
    Name: "Klem Butter Blush Çağla Yeşili 3-3-1 Koltuk Takımı - Kadife",
    Price: "101.360TL",
    Brand: "Normod",
    ImageURL: "https://normod.com/cdn/shop/..."
};
```

---

### 2. GOOGLE TAG MANAGER SİTELERİ (dataLayer)
**Sites**: Karaca, MediaMarkt, Teknosa

**Veri Kaynağı Priority:**
```
1️⃣ window.dataLayer (GTM Ecommerce)
   ✅ GA Universal: ecommerce.detail.products[]
   ✅ GA4: ecommerce.items[]
   ✅ Name, Price, Brand, Category

2️⃣ Meta Tags (og:, product:)
   ✅ og:title, product:price:amount
   ✅ Yedek veri kaynağı

3️⃣ HTML Selectors
   ⚠️ Fallback
```

**Örnek Kod:**
```javascript
// GA Universal Format
dataLayer.push({
  "ecommerce": {
    "detail": {
      "products": [{
        "name": "Karaca Tea Break Çay Makinesi",
        "price": "2699.00",
        "brand": "Karaca"
      }]
    }
  }
});

// GA4 Format
dataLayer.push({
  "ecommerce": {
    "items": [{
      "item_name": "...",
      "price": "...",
      "item_brand": "..."
    }]
  }
});
```

---

### 3. NEXT.JS SİTELERİ
**Sites**: Zara Home, (H&M Home kontrol edilecek)

**Veri Kaynağı Priority:**
```
1️⃣ __NEXT_DATA__ Script Tag
   ✅ props.pageProps.product
   ✅ Tam yapılandırılmış veri
   ⚠️ Yapı site'a göre değişebilir

2️⃣ Meta Tags
   ✅ og:title, og:image, og:price

3️⃣ HTML Selectors
   ❌ Next.js SSR olduğu için çalışabilir
```

**Örnek Kod:**
```html
<script id="__NEXT_DATA__" type="application/json">
{
  "props": {
    "pageProps": {
      "product": {
        "name": "Çiçek Desenli Saten Nevresim",
        "price": 1299,
        "brand": "Zara Home"
      }
    }
  }
}
</script>
```

---

### 4. WOOCOMMERCE SİTELERİ
**Sites**: English Home, Madame Coco, IKEA, Yataş, Taç, Chakra

**Veri Kaynağı Priority:**
```
1️⃣ WooCommerce HTML Selectors
   ✅ .product_title, .woocommerce-Price-amount
   ✅ .wp-post-image, .summary
   ✅ WordPress standart yapısı

2️⃣ Meta Tags
   ✅ og:title, og:image

3️⃣ JSON-LD (Bazı WooCommerce siteler kullanır)
   ⚠️ Opsiyonel
```

**Örnek HTML:**
```html
<h1 class="product_title entry-title">Pike Takımı</h1>
<p class="price">
  <ins>
    <span class="woocommerce-Price-amount amount">799,00 TL</span>
  </ins>
</p>
<img class="wp-post-image" src="...">
```

---

### 5. GENERIC HTML SİTELERİ
**Sites**: Trendyol, Hepsiburada, N11, Arçelik, Beko, Vestel, Bosch, Samsung, vb.

**Veri Kaynağı Priority:**
```
1️⃣ JSON-LD (application/ld+json)
   ✅ Schema.org Product standardı
   ✅ name, offers.price, brand, image

2️⃣ Hidden JS Variables
   ✅ window.__PRELOADED_STATE__
   ✅ var product = {...}
   ⚠️ Site'a özel

3️⃣ Meta Tags (OG, Product, Twitter)
   ✅ og:title, og:image, og:price
   ✅ product:price:amount

4️⃣ HTML Selectors (Platform-Specific)
   ✅ Magento: .page-title, .price-box
   ✅ PrestaShop: .product-title, .current-price
   ✅ OpenCart: .product-info h1, h2.price
   ✅ Trendyol: h1.pr-new-br, .prc-dsc
   ✅ Hepsiburada: h1#productName, [data-bind]
```

**Örnek JSON-LD:**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Çamaşır Makinesi 9 KG",
  "offers": {
    "price": "8999.00",
    "priceCurrency": "TRY"
  },
  "brand": {"name": "Arçelik"},
  "image": "https://..."
}
</script>
```

---

## 🔄 FALLBACK MEKANİZMASI

Her aşamada veri yoksa bir sonrakine geç:

```python
# Pseudo-code
result = {
  'title': (
    site_specific_parser.title or
    json_ld.title or
    meta_tags.title or
    html_selectors.title
  ),
  'price': (
    site_specific_parser.price or
    json_ld.price or
    meta_tags.price or
    html_selectors.price
  )
}
```

---

## 📈 VERİ KAYNAĞI İSTATİSTİKLERİ

| Veri Kaynağı | Kullanım | Güvenilirlik | Kapsam |
|--------------|----------|--------------|--------|
| **Shopify JSON API** | 4 site | ⭐⭐⭐⭐⭐ | Tam veri |
| **dataLayer (GTM)** | 3+ site | ⭐⭐⭐⭐⭐ | Tam veri |
| **Klaviyo** | 4 site | ⭐⭐⭐⭐ | Yedek |
| **__NEXT_DATA__** | 2 site | ⭐⭐⭐⭐⭐ | Tam veri |
| **JSON-LD** | 20+ site | ⭐⭐⭐⭐ | Standart |
| **Meta Tags** | 30+ site | ⭐⭐⭐ | Temel |
| **HTML Selectors** | 30+ site | ⭐⭐ | Fallback |

---

## 🎯 PLATFORM TESPİTİ

Scraper otomatik olarak platformu tespit eder:

```python
# Domain-based detection
if 'enzahome' in domain or 'normod' in domain:
    use_shopify_parser()

if 'karaca' in domain:
    use_datalayer_parser()  # Generic parser içinde

if 'zarahome' in domain:
    use_nextjs_parser()

if 'englishhome' in domain or 'madamecoco' in domain:
    use_woocommerce_parser()

else:
    use_generic_parser()  # JSON-LD + Meta + HTML
```

---

## 🧪 TEST EDİLEN VERİ KAYNAKLARI

### ✅ Test Edildi ve Çalışıyor
- Shopify JSON API (Enza Home, Normod)
- dataLayer GTM (Karaca)
- Klaviyo Tracking (Normod)
- Meta Tags (Tüm siteler)
- JSON-LD (Mock test)
- HTML Selectors (7 platform mock test)

### 🔄 Test Edilecek
- __NEXT_DATA__ (Zara Home - gerçek URL ile)
- WooCommerce (English Home - gerçek URL ile)
- Magento (Gerçek Magento site bulunursa)
- PrestaShop (Gerçek PrestaShop site bulunursa)

---

## 📝 NOTLAR

1. **Klaviyo Fiyat Formatı**: `"101.360TL"` → Nokta binlik ayracı, virgül ondalık
   ```python
   price_str.replace('TL', '').replace('.', '').replace(',', '.')
   # "101.360TL" → "101360.0"
   ```

2. **GA4 Price Format**: Cent cinsinden olabilir
   ```python
   price_cent = 269900  # 2699.00 TL
   price_tl = price_cent / 100
   ```

3. **Image URL Normalization**:
   - Arçelik/Beko: `/2000Wx2000H/image.webp`
   - Hepsiburada: `/format:webp`
   - Shopify: `?v=timestamp` query parametresi var

---

**Son Güncelleme**: 2026-01-18
**Toplam Veri Kaynağı**: 7 farklı tip
**Toplam Desteklenen Site**: 30+
