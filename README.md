# 🏠 Yeni Yuva - Ev Eşyası Yönetim Sistemi

Evlilik hazırlıkları için akıllı ev eşyası takip ve yönetim sistemi.

## ✨ Özellikler

- 📦 **Ürün Yönetimi**: Manuel giriş veya link ile otomatik bilgi çekme
- 🔗 **Akıllı Scraping**: Arçelik, Enza Home, Trendyol, Hepsiburada ve daha fazlası
- 💰 **Bütçe Takibi**: Toplam bütçe, harcanan, planlanan, kalan
- 🧮 **Senaryo Hesaplayıcı**: Seçili ürünlerin toplam fiyatını hesapla
- 📊 **Dashboard**: Kategori ve oda bazlı dağılım grafikleri
- 📥 **Excel Export**: Tüm verileri Excel'e aktar
- 📱 **Responsive**: Mobil uyumlu Pinterest tarzı tasarım

## 🚀 Replit'te Çalıştırma

### Yöntem 1: Otomatik (Önerilen)

1. Bu projeyi Replit'e import edin
2. "Run" butonuna tıklayın
3. Otomatik olarak başlayacaktır

### Yöntem 2: Manuel

1. Replit'te yeni Python projesi oluşturun
2. Tüm dosyaları yükleyin
3. Shell'de çalıştırın:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

## 🔐 Güvenlik Yapılandırması

Üretim ortamında mutlaka güvenli bir SECRET_KEY kullanın:

1. `.env.example` dosyasını `.env` olarak kopyalayın:
   ```bash
   cp .env.example .env
   ```

2. `.env` dosyasını düzenleyerek güvenli bir SECRET_KEY oluşturun:
   ```bash
   python -c 'import secrets; print(secrets.token_hex(32))'
   ```

3. Çıkan değeri `.env` dosyasına yapıştırın:
   ```
   SECRET_KEY=oluşturduğunuz-güvenli-anahtar-buraya
   ```

**Not**: `.env` dosyası git'e eklenmez, sadece sizin bilgisayarınızda kalır.

## 📂 Proje Yapısı

```
ev-esyasi-yonetim/
├── app.py                 # Flask backend
├── requirements.txt       # Python bağımlılıkları
├── .replit               # Replit yapılandırması
├── replit.nix            # Nix paketleri
├── pyproject.toml        # Poetry yapılandırması
├── templates/
│   └── index.html        # Vue.js frontend
└── static/
    └── uploads/          # Yüklenen görseller
```

## 🔧 Teknik Özellikler (Beyaz Eşya)

Sistem aşağıdaki teknik özellikleri destekler:

### Çamaşır Makinesi
- Enerji sınıfı
- Kapasite (kg)
- Devir sayısı (rpm)
- Su tüketimi (lt)
- Yıllık su tüketimi (lt)
- Yıkama/sıkma gürültüsü (dB)
- Program sayısı
- Ölçüler

### Bulaşık Makinesi
- Enerji sınıfı
- Kapasite (kişilik)
- Su tüketimi (lt)
- Gürültü (dB)
- Kurutma sınıfı

### Buzdolabı
- Enerji sınıfı
- Brüt/net hacim (lt)
- Soğutma tipi (No Frost vb.)
- Dondurucu hacmi
- Yıllık enerji tüketimi (kWh)

### Mobilya (Koltuk Takımı)
- 3'lü koltuk ölçüleri
- 2'li koltuk ölçüleri
- Berjer ölçüleri
- Malzeme
- Kumaş tipi
- Renk

## 🌐 Desteklenen Web Siteleri

Otomatik bilgi çekme aşağıdaki sitelerden çalışır:
- ✅ Arçelik (arcelik.com.tr)
- ✅ Enza Home (enzahome.com.tr)
- ✅ Trendyol
- ✅ Hepsiburada
- ✅ N11
- ✅ MediaMarkt
- ✅ IKEA
- ✅ Bellona
- ✅ İstikbal
- ✅ Bosch
- ✅ Siemens
- ✅ Vestel
- ✅ Beko

## 🔒 Paylaşım

Replit'te projeyi çalıştırdığınızda otomatik olarak bir URL alırsınız.
Bu URL'yi eşinizle paylaşarak birlikte kullanabilirsiniz!

## 📝 Lisans

MIT License - Kişisel kullanım için ücretsizdir.

---

💕 Mutlu bir yuva dileğiyle!
