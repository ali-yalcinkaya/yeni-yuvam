"""
Akıllı Ev Eşyası Yönetim Sistemi
Flask Backend - Replit Uyumlu
"""

import os
import re
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import pandas as pd
from bs4 import BeautifulSoup
import requests
from io import BytesIO

# Flask App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ev-esyasi-gizli-anahtar-2024-CHANGE-IN-PRODUCTION')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Database path
DATABASE = 'ev_esyalari.db'

# Kategori bazlı dinamik alanlar - GENİŞLETİLMİŞ
KATEGORI_ALANLARI = {
    'Beyaz Eşya': {
        'Çamaşır Makinesi': ['enerji_sinifi', 'kapasite_kg', 'devir_sayisi', 'su_tuketimi_lt', 'yillik_su_tuketimi_lt', 'gurultu_yikama_db', 'gurultu_sikma_db', 'yikama_programlari', 'garanti_suresi', 'olculer'],
        'Bulaşık Makinesi': ['enerji_sinifi', 'kapasite_kisilik', 'su_tuketimi_lt', 'yillik_su_tuketimi_lt', 'gurultu_db', 'yikama_programlari', 'kurutma_sinifi', 'garanti_suresi', 'olculer'],
        'Buzdolabı': ['enerji_sinifi', 'brut_hacim_lt', 'net_hacim_lt', 'sogutma_tipi', 'gurultu_db', 'yillik_enerji_tuketimi_kwh', 'garanti_suresi', 'olculer', 'dondurucu_hacim_lt'],
        'Fırın': ['enerji_sinifi', 'kapasite_lt', 'firin_tipi', 'pisirme_programlari', 'garanti_suresi', 'olculer'],
        'Kurutma Makinesi': ['enerji_sinifi', 'kapasite_kg', 'kurutma_tipi', 'gurultu_db', 'yillik_enerji_tuketimi_kwh', 'garanti_suresi', 'olculer'],
        'Derin Dondurucu': ['enerji_sinifi', 'brut_hacim_lt', 'net_hacim_lt', 'gurultu_db', 'garanti_suresi', 'olculer'],
        'Genel': ['enerji_sinifi', 'kapasite', 'gurultu_db', 'su_tuketimi_lt', 'garanti_suresi', 'olculer']
    },
    'Mobilya': {
        'Koltuk Takımı': ['olculer_3lu', 'olculer_2li', 'olculer_berjer', 'malzeme', 'kumas_tipi', 'renk', 'kisi_kapasitesi', 'agirlik_kg', 'garanti_suresi'],
        'Yatak': ['olculer', 'yatak_tipi', 'sertlik', 'malzeme', 'garanti_suresi'],
        'Yemek Masası': ['olculer', 'malzeme', 'kisi_kapasitesi', 'renk', 'agirlik_kg'],
        'Dolap': ['olculer', 'malzeme', 'renk', 'raf_sayisi', 'agirlik_kg'],
        'TV Ünitesi': ['olculer', 'malzeme', 'renk', 'max_tv_boyutu'],
        'Genel': ['olculer', 'malzeme', 'renk', 'agirlik_kg', 'garanti_suresi']
    },
    'Elektronik': {
        'Televizyon': ['ekran_boyutu', 'cozunurluk', 'panel_tipi', 'smart_tv', 'hdmi_sayisi', 'garanti_suresi', 'yillik_enerji_tuketimi_kwh'],
        'Klima': ['enerji_sinifi', 'sogutma_kapasitesi_btu', 'isitma_kapasitesi_btu', 'gurultu_db', 'inverter', 'garanti_suresi'],
        'Aspiratör': ['motor_gucu_w', 'ses_seviyesi_db', 'hava_debisi', 'filtre_tipi', 'olculer'],
        'Genel': ['ekran_boyutu', 'cozunurluk', 'baglanti', 'garanti_suresi', 'enerji_sinifi']
    },
    'Mutfak Gereci': {
        'Tencere Seti': ['parca_sayisi', 'malzeme', 'induksiyona_uygun', 'bulasik_makinesi_uyumu'],
        'Blender': ['motor_gucu_w', 'kapasite_lt', 'hiz_ayari', 'garanti_suresi'],
        'Kahve Makinesi': ['kahve_tipi', 'kapasite', 'basinc_bar', 'garanti_suresi'],
        'Genel': ['malzeme', 'kapasite', 'bulasik_makinesi_uyumu', 'garanti_suresi']
    },
    'Tekstil': {
        'Nevresim Takımı': ['olculer', 'malzeme', 'iplik_sayisi', 'renk', 'parca_sayisi'],
        'Perde': ['olculer', 'malzeme', 'renk', 'perde_tipi'],
        'Halı': ['olculer', 'malzeme', 'hav_yuksekligi', 'renk'],
        'Genel': ['olculer', 'malzeme', 'renk', 'yikama_talimat']
    },
    'Dekorasyon': {
        'Ayna': ['olculer', 'cerceve_malzeme', 'cerceve_renk'],
        'Tablo': ['olculer', 'cerceve_tipi', 'baski_tipi'],
        'Saksı': ['olculer', 'malzeme', 'renk', 'ic_dis_mekan'],
        'Genel': ['olculer', 'malzeme', 'renk']
    },
    'Aydınlatma': {
        'Avize': ['watt', 'renk_sicakligi_kelvin', 'lumen', 'ampul_tipi', 'ampul_sayisi', 'olculer'],
        'Abajur': ['watt', 'renk_sicakligi_kelvin', 'malzeme', 'olculer'],
        'Spot': ['watt', 'renk_sicakligi_kelvin', 'lumen', 'led_uyumlu'],
        'Genel': ['watt', 'renk_sicakligi_kelvin', 'lumen']
    },
    'Banyo': {
        'Lavabo': ['olculer', 'malzeme', 'montaj_tipi', 'tasma_deligi'],
        'Klozet': ['olculer', 'malzeme', 'su_tasarrufu', 'kapak_tipi', 'sifon_tipi'],
        'Duşakabin': ['olculer', 'cam_kalinligi_mm', 'profil_renk', 'acilma_yonu'],
        'Batarya': ['malzeme', 'akis_hizi', 'tasarruf_sistemi', 'garanti_suresi'],
        'Genel': ['malzeme', 'olculer', 'su_tasarrufu']
    },
    'Diğer': {
        'Genel': ['aciklama', 'olculer', 'malzeme']
    }
}

# Oda listesi
ODALAR = ['Salon', 'Yatak Odası', 'Mutfak', 'Banyo', 'Çocuk Odası', 'Çalışma Odası', 'Antre', 'Balkon', 'Diğer']

# Alt kategori listesi (frontend için)
ALT_KATEGORILER = {k: list(v.keys()) for k, v in KATEGORI_ALANLARI.items()}

# Klasör kontrolü ve oluşturma
def ensure_upload_folder():
    """Upload klasörünü kontrol et ve yoksa oluştur"""
    upload_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
        print(f"✓ Upload klasörü oluşturuldu: {upload_path}")
    return upload_path

def allowed_file(filename):
    """Dosya uzantısı kontrolü"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    """SQLite bağlantısı oluştur"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Veritabanını başlat"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ana ürün tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_adi TEXT NOT NULL,
            marka TEXT,
            fiyat REAL DEFAULT 0,
            indirimli_fiyat REAL DEFAULT NULL,
            fiyat_guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            link TEXT,
            resim_url TEXT,
            kategori TEXT DEFAULT 'Diğer',
            alt_kategori TEXT DEFAULT 'Genel',
            oda TEXT DEFAULT 'Salon',
            statu TEXT DEFAULT 'Araştırılıyor',
            oncelik TEXT DEFAULT 'Normal',
            teknik_ozellikler TEXT,
            notlar TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Bütçe tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS butce (
            id INTEGER PRIMARY KEY,
            toplam_butce REAL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Varsayılan bütçe kaydı
    cursor.execute('SELECT COUNT(*) FROM butce')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO butce (id, toplam_butce) VALUES (1, 100000)')

    # Migration: Yeni sütunları ekle (eğer yoksa)
    try:
        cursor.execute("SELECT indirimli_fiyat FROM urunler LIMIT 1")
    except sqlite3.OperationalError:
        print("→ Migration: indirimli_fiyat sütunu ekleniyor...")
        cursor.execute("ALTER TABLE urunler ADD COLUMN indirimli_fiyat REAL DEFAULT NULL")

    try:
        cursor.execute("SELECT fiyat_guncelleme_tarihi FROM urunler LIMIT 1")
    except sqlite3.OperationalError:
        print("→ Migration: fiyat_guncelleme_tarihi sütunu ekleniyor...")
        cursor.execute("ALTER TABLE urunler ADD COLUMN fiyat_guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    conn.commit()
    conn.close()
    print("✓ Veritabanı başlatıldı")

# ============================================
# WEB SCRAPING - SİTEYE ÖZEL FONKSİYONLAR
# ============================================

def scrape_arcelik(url, soup):
    """Arçelik sitesi için özel scraper"""
    data = {
        'urun_adi': '',
        'marka': 'Arçelik',
        'fiyat': 0,
        'resim_url': '',
        'link': url,
        'teknik_ozellikler': {},
        'kategori_tahmini': '',
        'alt_kategori_tahmini': ''
    }
    
    # Ürün adı - Arçelik için özel selector
    title = soup.select_one('h1#pdp-product-name, h1.product-name, h1.pdp-title, .product-title h1, h1')
    if title:
        data['urun_adi'] = title.get_text(strip=True)
    
    # OG title fallback
    if not data['urun_adi']:
        og_title = soup.find('meta', property='og:title')
        if og_title:
            data['urun_adi'] = og_title.get('content', '').split('|')[0].strip()
    
    # Kategori tahmini URL ve başlıktan
    url_lower = url.lower()
    title_lower = data['urun_adi'].lower()
    
    if 'buzdolabi' in url_lower or 'buzdolabı' in title_lower:
        data['kategori_tahmini'] = 'Beyaz Eşya'
        data['alt_kategori_tahmini'] = 'Buzdolabı'
    elif 'camasir-makinesi' in url_lower or 'çamaşır makinesi' in title_lower:
        data['kategori_tahmini'] = 'Beyaz Eşya'
        data['alt_kategori_tahmini'] = 'Çamaşır Makinesi'
    elif 'bulasik-makinesi' in url_lower or 'bulaşık makinesi' in title_lower:
        data['kategori_tahmini'] = 'Beyaz Eşya'
        data['alt_kategori_tahmini'] = 'Bulaşık Makinesi'
    elif 'kurutma-makinesi' in url_lower or 'kurutma makinesi' in title_lower:
        data['kategori_tahmini'] = 'Beyaz Eşya'
        data['alt_kategori_tahmini'] = 'Kurutma Makinesi'
    elif 'firin' in url_lower or 'fırın' in title_lower:
        data['kategori_tahmini'] = 'Beyaz Eşya'
        data['alt_kategori_tahmini'] = 'Fırın'
    elif 'derin-dondurucu' in url_lower:
        data['kategori_tahmini'] = 'Beyaz Eşya'
        data['alt_kategori_tahmini'] = 'Derin Dondurucu'
    elif 'klima' in url_lower:
        data['kategori_tahmini'] = 'Elektronik'
        data['alt_kategori_tahmini'] = 'Klima'
    elif 'televizyon' in url_lower or 'tv' in url_lower:
        data['kategori_tahmini'] = 'Elektronik'
        data['alt_kategori_tahmini'] = 'Televizyon'
    
    # Fiyat - Arçelik'in çeşitli fiyat elementleri
    price_selectors = [
        '.product-price .price', '.pdp-price', '.price-box .price',
        '[data-price]', '.product-price', '.price', '.pdp-price-area span',
        '.price-value', '.product-detail-price'
    ]
    for sel in price_selectors:
        price_el = soup.select_one(sel)
        if price_el:
            price_text = price_el.get_text(strip=True)
            price_clean = re.sub(r'[^\d,.]', '', price_text)
            price_clean = price_clean.replace('.', '').replace(',', '.')
            try:
                data['fiyat'] = float(price_clean)
                if data['fiyat'] > 0:
                    break
            except:
                continue
    
    # Resim - Arçelik özel format
    img_selectors = [
        '.product-gallery img', '.pdp-gallery img',
        '.product-image img', 'img.product-img',
        '.slick-slide img', '.carousel-item img',
        '.gallery-thumbs img', '.pdp-image img',
        'img[src*="arcelik"]', 'img[data-src*="media"]'
    ]
    for sel in img_selectors:
        img = soup.select_one(sel)
        if img:
            # Arçelik resimleri için öncelik sırası: data-src > src
            src = img.get('data-src') or img.get('data-lazy') or img.get('src')
            if src and 'placeholder' not in src.lower():
                # Protokol düzeltmeleri
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.arcelik.com.tr' + src
                elif src.startswith('www.'):
                    src = 'https://' + src

                # Arçelik resim optimizasyonu - 1000x1000 boyut (SADECE webp formatı)
                if 'arcelik.com.tr/media/' in src:
                    # Eğer resize parametresi yoksa ekle
                    if '/resize/' not in src:
                        src = src.replace('/media/', '/media/resize/')
                        # Dosya uzantısını bul ve webp formatına çevir
                        if '.png' in src.lower():
                            src = src.replace('.png', '.png/1000Wx1000H/image.webp', 1)
                            src = src.replace('.PNG', '.PNG/1000Wx1000H/image.webp', 1)
                        elif '.jpg' in src.lower() or '.jpeg' in src.lower():
                            if '.jpg' in src:
                                src = src.replace('.jpg', '.jpg/1000Wx1000H/image.webp', 1)
                            elif '.JPG' in src:
                                src = src.replace('.JPG', '.JPG/1000Wx1000H/image.webp', 1)
                            elif '.jpeg' in src:
                                src = src.replace('.jpeg', '.jpeg/1000Wx1000H/image.webp', 1)
                        elif '.webp' in src.lower():
                            if '/1000Wx1000H/' not in src:
                                src = src.replace('.webp', '.webp/1000Wx1000H/image.webp', 1)

                data['resim_url'] = src
                break
    
    # OG image fallback
    if not data['resim_url']:
        og_img = soup.find('meta', property='og:image')
        if og_img:
            data['resim_url'] = og_img.get('content', '')
    
    # Teknik özellikler - Arçelik'in spec tablosu
    specs = {}
    
    # Yöntem 1: dl/dt/dd yapısı
    for dt in soup.select('dt, .spec-name, .feature-name, .property-name, .spec-label'):
        dd = dt.find_next_sibling(['dd', 'span', 'div'])
        if dd:
            key = dt.get_text(strip=True).lower()
            val = dd.get_text(strip=True)
            if key and val:
                specs[key] = val
    
    # Yöntem 2: Tablo yapısı
    for row in soup.select('tr, .spec-row, .feature-row, .product-spec-item'):
        cells = row.select('td, th, .spec-cell, span')
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True).lower()
            val = cells[1].get_text(strip=True)
            if key and val:
                specs[key] = val
    
    # Yöntem 3: li yapısı
    for li in soup.select('.product-features li, .spec-list li, .features li, .pdp-specs li'):
        text = li.get_text(strip=True)
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) == 2:
                specs[parts[0].strip().lower()] = parts[1].strip()
    
    # Yöntem 4: JSON-LD verisi
    json_ld = soup.find('script', type='application/ld+json')
    if json_ld:
        try:
            ld_data = json.loads(json_ld.string)
            if isinstance(ld_data, dict):
                if 'name' in ld_data and not data['urun_adi']:
                    data['urun_adi'] = ld_data['name']
                if 'image' in ld_data and not data['resim_url']:
                    data['resim_url'] = ld_data['image'] if isinstance(ld_data['image'], str) else ld_data['image'][0]
                if 'offers' in ld_data and not data['fiyat']:
                    offers = ld_data['offers']
                    if isinstance(offers, dict) and 'price' in offers:
                        data['fiyat'] = float(offers['price'])
        except:
            pass
    
    # Bilinen alanları eşleştir
    spec_mapping = {
        'enerji sınıfı': 'enerji_sinifi',
        'enerji': 'enerji_sinifi',
        'energy class': 'enerji_sinifi',
        'kapasite': 'kapasite_kg',
        'yıkama kapasitesi': 'kapasite_kg',
        'yükleme kapasitesi': 'kapasite_kg',
        'maksimum yükleme': 'kapasite_kg',
        'devir': 'devir_sayisi',
        'sıkma devri': 'devir_sayisi',
        'maksimum sıkma devri': 'devir_sayisi',
        'devir/dakika': 'devir_sayisi',
        'su tüketimi': 'su_tuketimi_lt',
        'yıllık su tüketimi': 'yillik_su_tuketimi_lt',
        'ortalama su tüketimi': 'su_tuketimi_lt',
        'standart su tüketimi': 'su_tuketimi_lt',
        'gürültü': 'gurultu_db',
        'ses seviyesi': 'gurultu_db',
        'yıkama gürültüsü': 'gurultu_yikama_db',
        'sıkma gürültüsü': 'gurultu_sikma_db',
        'çalışma sesi': 'gurultu_db',
        'program sayısı': 'yikama_programlari',
        'program': 'yikama_programlari',
        'yıkama programları': 'yikama_programlari',
        'garanti': 'garanti_suresi',
        'garanti süresi': 'garanti_suresi',
        'boyutlar': 'olculer',
        'ölçüler': 'olculer',
        'ebat': 'olculer',
        'genişlik': 'genislik',
        'yükseklik': 'yukseklik',
        'derinlik': 'derinlik',
        'brüt hacim': 'brut_hacim_lt',
        'net hacim': 'net_hacim_lt',
        'toplam hacim': 'brut_hacim_lt',
        'soğutma sistemi': 'sogutma_tipi',
        'no frost': 'sogutma_tipi',
        'yıllık enerji tüketimi': 'yillik_enerji_tuketimi_kwh',
        'enerji tüketimi': 'yillik_enerji_tuketimi_kwh',
        'kişilik': 'kapasite_kisilik',
        'kurutma sınıfı': 'kurutma_sinifi',
    }
    
    for spec_key, spec_val in specs.items():
        for search_term, field_name in spec_mapping.items():
            if search_term in spec_key:
                data['teknik_ozellikler'][field_name] = spec_val
                break
    
    return data

def scrape_enzahome(url, soup):
    """Enza Home sitesi için özel scraper"""
    data = {
        'urun_adi': '',
        'marka': 'Enza Home',
        'fiyat': 0,
        'resim_url': '',
        'link': url,
        'teknik_ozellikler': {},
        'kategori_tahmini': 'Mobilya',
        'alt_kategori_tahmini': ''
    }
    
    # Ürün adı
    title = soup.select_one('h1.product-name, h1.product-title, .product-detail h1, h1')
    if title:
        data['urun_adi'] = title.get_text(strip=True)
    
    # OG title fallback
    if not data['urun_adi']:
        og_title = soup.find('meta', property='og:title')
        if og_title:
            data['urun_adi'] = og_title.get('content', '').split('|')[0].strip()
    
    # Kategori tahmini URL ve başlıktan
    url_lower = url.lower()
    title_lower = data['urun_adi'].lower()
    
    if 'koltuk' in url_lower or 'koltuk' in title_lower:
        data['alt_kategori_tahmini'] = 'Koltuk Takımı'
    elif 'yatak-odasi' in url_lower or 'yatak odası' in title_lower:
        data['alt_kategori_tahmini'] = 'Genel'
    elif 'yemek' in url_lower or 'masa' in title_lower:
        data['alt_kategori_tahmini'] = 'Yemek Masası'
    elif 'dolap' in url_lower or 'dolap' in title_lower:
        data['alt_kategori_tahmini'] = 'Dolap'
    elif 'tv-unitesi' in url_lower:
        data['alt_kategori_tahmini'] = 'TV Ünitesi'
    
    # Fiyat
    price_selectors = [
        '.product-price', '.price', '.current-price',
        '.sale-price', '[data-price]', '.product-detail-price',
        '.price-new', '.price-box span'
    ]
    for sel in price_selectors:
        price_el = soup.select_one(sel)
        if price_el:
            price_text = price_el.get_text(strip=True)
            price_clean = re.sub(r'[^\d,.]', '', price_text)
            price_clean = price_clean.replace('.', '').replace(',', '.')
            try:
                data['fiyat'] = float(price_clean)
                if data['fiyat'] > 0:
                    break
            except:
                continue
    
    # Resim
    img_selectors = [
        '.product-image img', '.gallery img', '.product-gallery img', 
        '.main-image img', '.product-detail-image img',
        '.slick-slide img', 'img.img-fluid'
    ]
    for sel in img_selectors:
        img = soup.select_one(sel)
        if img:
            src = img.get('src') or img.get('data-src')
            if src and 'placeholder' not in src.lower():
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.enzahome.com.tr' + src
                data['resim_url'] = src
                break
    
    # OG image fallback
    if not data['resim_url']:
        og_img = soup.find('meta', property='og:image')
        if og_img:
            data['resim_url'] = og_img.get('content', '')
    
    # Teknik özellikler
    specs = {}
    
    # Tablo/liste yapısı
    for row in soup.select('.product-specs tr, .specifications tr, .features li, .product-features li, .tab-content tr'):
        cells = row.select('td, th')
        if len(cells) >= 2:
            key = cells[0].get_text(strip=True).lower()
            val = cells[1].get_text(strip=True)
            if key and val:
                specs[key] = val
        else:
            text = row.get_text(strip=True)
            if ':' in text:
                parts = text.split(':', 1)
                if len(parts) == 2:
                    specs[parts[0].strip().lower()] = parts[1].strip()
    
    spec_mapping = {
        'ölçü': 'olculer',
        'boyut': 'olculer',
        'ebat': 'olculer',
        '3 lü koltuk': 'olculer_3lu',
        '3\'lü koltuk': 'olculer_3lu',
        '2 lü koltuk': 'olculer_2li',
        '2\'lü koltuk': 'olculer_2li',
        'berjer': 'olculer_berjer',
        'tekli': 'olculer_berjer',
        'malzeme': 'malzeme',
        'kumaş': 'kumas_tipi',
        'kaplama': 'kumas_tipi',
        'renk': 'renk',
        'kişilik': 'kisi_kapasitesi',
        'oturma': 'kisi_kapasitesi',
    }
    
    for spec_key, spec_val in specs.items():
        for search_term, field_name in spec_mapping.items():
            if search_term in spec_key:
                data['teknik_ozellikler'][field_name] = spec_val
                break
    
    return data

def scrape_generic(url, soup):
    """Genel amaçlı scraper"""
    data = {
        'urun_adi': '',
        'marka': '',
        'fiyat': 0,
        'resim_url': '',
        'link': url,
        'teknik_ozellikler': {}
    }
    
    # Ürün adı
    title_selectors = [
        'h1.product-name', 'h1.product-title', 'h1[itemprop="name"]',
        '.product-name h1', '.product-title', '#productName',
        'h1.pr-new-br span', 'h1.product_name', 'h1'
    ]
    for selector in title_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            data['urun_adi'] = element.get_text(strip=True)[:200]
            break
    
    # OG title fallback
    if not data['urun_adi']:
        og_title = soup.find('meta', property='og:title')
        if og_title:
            data['urun_adi'] = og_title.get('content', '')[:200]
    
    # Fiyat
    price_selectors = [
        '.product-price', '.prc-dsc', '[data-test-id="price-current-price"]',
        '.price', '.product_price', '[itemprop="price"]',
        '.current-price', '.sale-price', '.pr-bx-pr-pc span'
    ]
    for selector in price_selectors:
        element = soup.select_one(selector)
        if element:
            price_text = element.get_text(strip=True)
            price_clean = re.sub(r'[^\d,.]', '', price_text)
            price_clean = price_clean.replace('.', '').replace(',', '.')
            try:
                data['fiyat'] = float(price_clean) if price_clean else 0
                if data['fiyat'] > 0:
                    break
            except ValueError:
                continue
    
    # Marka
    brand_selectors = [
        '[itemprop="brand"]', '.brand', '.product-brand',
        '.pr-new-br a', '.product_brand'
    ]
    for selector in brand_selectors:
        element = soup.select_one(selector)
        if element and element.get_text(strip=True):
            data['marka'] = element.get_text(strip=True)[:100]
            break
    
    # Resim
    img_selectors = [
        '.product-image img', '.gallery-image img', '[itemprop="image"]',
        '.product-img img', '#product-image', '.product-gallery img',
        '.detail-img img', 'img.product-image', '.main-image img'
    ]
    for selector in img_selectors:
        element = soup.select_one(selector)
        if element:
            img_url = element.get('src') or element.get('data-src') or element.get('data-original')
            if img_url:
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                data['resim_url'] = img_url
                break
    
    # OG image fallback
    if not data['resim_url']:
        og_image = soup.find('meta', property='og:image')
        if og_image:
            data['resim_url'] = og_image.get('content', '')
    
    return data

def scrape_product_data(url):
    """URL'den ürün bilgilerini çek - Site bazlı akıllı scraper"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()
        
        # Encoding düzeltme
        if response.encoding == 'ISO-8859-1' or response.encoding is None:
            response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Siteye göre uygun scraper'ı seç
        if 'arcelik.com.tr' in url:
            data = scrape_arcelik(url, soup)
        elif 'enzahome.com.tr' in url:
            data = scrape_enzahome(url, soup)
        elif 'trendyol.com' in url:
            data = scrape_generic(url, soup)
            data['marka'] = data.get('marka') or 'Trendyol'
        elif 'hepsiburada.com' in url:
            data = scrape_generic(url, soup)
            data['marka'] = data.get('marka') or 'Hepsiburada'
        elif 'n11.com' in url:
            data = scrape_generic(url, soup)
        elif 'mediamarkt.com.tr' in url:
            data = scrape_generic(url, soup)
            data['marka'] = data.get('marka') or 'MediaMarkt'
        elif 'ikea.com.tr' in url:
            data = scrape_generic(url, soup)
            data['marka'] = 'IKEA'
        elif 'bellona.com.tr' in url:
            data = scrape_generic(url, soup)
            data['marka'] = 'Bellona'
        elif 'istikbal.com.tr' in url:
            data = scrape_generic(url, soup)
            data['marka'] = 'İstikbal'
        elif 'bosch-home.com.tr' in url:
            data = scrape_generic(url, soup)
            data['marka'] = 'Bosch'
        elif 'siemens-home.bsh-group.com' in url:
            data = scrape_generic(url, soup)
            data['marka'] = 'Siemens'
        elif 'vestel.com.tr' in url:
            data = scrape_generic(url, soup)
            data['marka'] = 'Vestel'
        elif 'beko.com.tr' in url:
            data = scrape_generic(url, soup)
            data['marka'] = 'Beko'
        else:
            data = scrape_generic(url, soup)
        
        return {'success': True, 'data': data}
        
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Site yanıt vermedi (timeout). Lütfen tekrar deneyin.'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Bağlantı hatası: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Beklenmeyen hata: {str(e)}'}

# ============================================
# API ROUTES
# ============================================

@app.route('/')
def index():
    """Ana sayfa"""
    # Alt kategorileri düzleştir
    flat_kategori_alanlari = {}
    for kat, alt_kats in KATEGORI_ALANLARI.items():
        flat_kategori_alanlari[kat] = {}
        for alt_kat, alanlar in alt_kats.items():
            flat_kategori_alanlari[kat][alt_kat] = alanlar
    
    return render_template('index.html', 
                         kategoriler=list(KATEGORI_ALANLARI.keys()),
                         odalar=ODALAR,
                         kategori_alanlari=flat_kategori_alanlari,
                         alt_kategoriler=ALT_KATEGORILER)

@app.route('/api/urunler', methods=['GET'])
def get_urunler():
    """Tüm ürünleri getir (filtreli)"""
    conn = get_db_connection()

    # Filtre parametreleri
    kategori = request.args.get('kategori', '')
    alt_kategori = request.args.get('alt_kategori', '')
    oda = request.args.get('oda', '')
    statu = request.args.get('statu', '')
    arama = request.args.get('arama', '')

    query = 'SELECT * FROM urunler WHERE 1=1'
    params = []

    if kategori:
        query += ' AND kategori = ?'
        params.append(kategori)
    if alt_kategori:
        query += ' AND alt_kategori = ?'
        params.append(alt_kategori)
    if oda:
        query += ' AND oda = ?'
        params.append(oda)
    if statu:
        query += ' AND statu = ?'
        params.append(statu)
    if arama:
        # Türkçe karakterlere duyarlı olmayan arama için COLLATE NOCASE
        query += ' AND (LOWER(urun_adi) LIKE LOWER(?) OR LOWER(marka) LIKE LOWER(?))'
        params.extend([f'%{arama}%', f'%{arama}%'])

    query += ' ORDER BY created_at DESC'

    urunler = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(u) for u in urunler])

@app.route('/api/urunler', methods=['POST'])
def add_urun():
    """Yeni ürün ekle"""
    try:
        data = request.form.to_dict()
        
        # Dosya upload kontrolü
        resim_url = data.get('resim_url', '')
        if 'resim_dosya' in request.files:
            file = request.files['resim_dosya']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                filepath = os.path.join(ensure_upload_folder(), filename)
                file.save(filepath)
                resim_url = f'/static/uploads/{filename}'
        
        # Teknik özellikler JSON olarak
        teknik = {}
        kategori = data.get('kategori', 'Diğer')
        alt_kategori = data.get('alt_kategori', 'Genel')
        
        if kategori in KATEGORI_ALANLARI:
            if alt_kategori in KATEGORI_ALANLARI[kategori]:
                for alan in KATEGORI_ALANLARI[kategori][alt_kategori]:
                    if alan in data and data[alan]:
                        teknik[alan] = data[alan]
        
        # Scrape'den gelen teknik özellikler
        if 'teknik_ozellikler_json' in data and data['teknik_ozellikler_json']:
            try:
                scraped_specs = json.loads(data['teknik_ozellikler_json'])
                teknik.update(scraped_specs)
            except:
                pass
        
        # İndirimli fiyat kontrolü
        fiyat = float(data.get('fiyat', 0) or 0)
        indirimli_fiyat = data.get('indirimli_fiyat', '')
        indirimli_fiyat = float(indirimli_fiyat) if indirimli_fiyat else None

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO urunler (urun_adi, marka, fiyat, indirimli_fiyat, fiyat_guncelleme_tarihi, link, resim_url, kategori, alt_kategori, oda, statu, oncelik, teknik_ozellikler, notlar)
            VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('urun_adi', 'İsimsiz Ürün'),
            data.get('marka', ''),
            fiyat,
            indirimli_fiyat,
            data.get('link', ''),
            resim_url,
            kategori,
            alt_kategori,
            data.get('oda', 'Salon'),
            data.get('statu', 'Araştırılıyor'),
            data.get('oncelik', 'Normal'),
            json.dumps(teknik, ensure_ascii=False),
            data.get('notlar', '')
        ))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'id': new_id, 'message': 'Ürün başarıyla eklendi!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/urunler/<int:id>', methods=['GET'])
def get_urun(id):
    """Tek ürün getir"""
    conn = get_db_connection()
    urun = conn.execute('SELECT * FROM urunler WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if urun:
        return jsonify(dict(urun))
    return jsonify({'error': 'Ürün bulunamadı'}), 404

@app.route('/api/urunler/<int:id>', methods=['PUT'])
def update_urun(id):
    """Ürün güncelle"""
    try:
        data = request.form.to_dict()
        
        conn = get_db_connection()
        urun = conn.execute('SELECT * FROM urunler WHERE id = ?', (id,)).fetchone()
        if not urun:
            conn.close()
            return jsonify({'error': 'Ürün bulunamadı'}), 404
        
        # Dosya upload kontrolü
        resim_url = data.get('resim_url', urun['resim_url'])
        if 'resim_dosya' in request.files:
            file = request.files['resim_dosya']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                filepath = os.path.join(ensure_upload_folder(), filename)
                file.save(filepath)
                resim_url = f'/static/uploads/{filename}'
        
        # Teknik özellikler
        teknik = {}
        kategori = data.get('kategori', urun['kategori'])
        alt_kategori = data.get('alt_kategori', 'Genel')
        
        if kategori in KATEGORI_ALANLARI:
            if alt_kategori in KATEGORI_ALANLARI[kategori]:
                for alan in KATEGORI_ALANLARI[kategori][alt_kategori]:
                    if alan in data and data[alan]:
                        teknik[alan] = data[alan]
        
        # İndirimli fiyat kontrolü
        fiyat = float(data.get('fiyat', urun['fiyat']) or 0)
        indirimli_fiyat = data.get('indirimli_fiyat', '')
        indirimli_fiyat = float(indirimli_fiyat) if indirimli_fiyat else None

        # Fiyat değiştiyse güncelleme tarihini yenile
        fiyat_guncelleme_sql = ''
        if fiyat != urun['fiyat'] or indirimli_fiyat != urun.get('indirimli_fiyat'):
            fiyat_guncelleme_sql = ", fiyat_guncelleme_tarihi = datetime('now')"

        cursor = conn.cursor()
        cursor.execute(f'''
            UPDATE urunler SET
                urun_adi = ?, marka = ?, fiyat = ?, indirimli_fiyat = ?, link = ?, resim_url = ?,
                kategori = ?, alt_kategori = ?, oda = ?, statu = ?, oncelik = ?,
                teknik_ozellikler = ?, notlar = ?, updated_at = CURRENT_TIMESTAMP
                {fiyat_guncelleme_sql}
            WHERE id = ?
        ''', (
            data.get('urun_adi', urun['urun_adi']),
            data.get('marka', urun['marka']),
            fiyat,
            indirimli_fiyat,
            data.get('link', urun['link']),
            resim_url,
            kategori,
            alt_kategori,
            data.get('oda', urun['oda']),
            data.get('statu', urun['statu']),
            data.get('oncelik', urun['oncelik']),
            json.dumps(teknik, ensure_ascii=False),
            data.get('notlar', urun['notlar']),
            id
        ))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Ürün güncellendi!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/urunler/<int:id>', methods=['DELETE'])
def delete_urun(id):
    """Ürün sil"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM urunler WHERE id = ?', (id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    
    if affected:
        return jsonify({'success': True, 'message': 'Ürün silindi!'})
    return jsonify({'error': 'Ürün bulunamadı'}), 404

@app.route('/api/scrape', methods=['POST'])
def scrape_url():
    """URL'den ürün bilgisi çek - Akıllı Scraper"""
    from scraper import scrape_product
    
    data = request.get_json()
    url = data.get('url', '')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL gerekli'}), 400
    
    result = scrape_product(url)
    
    if result['success']:
        # Veriyi frontend formatına dönüştür
        scraped = result['data']
        return jsonify({
            'success': True,
            'data': {
                'urun_adi': scraped.get('title', ''),
                'marka': scraped.get('brand', ''),
                'fiyat': scraped.get('price', 0),
                'resim_url': scraped.get('image_url', ''),
                'link': scraped.get('link', url),
                'kategori_tahmini': scraped.get('kategori_tahmini', ''),
                'alt_kategori_tahmini': scraped.get('alt_kategori_tahmini', ''),
                'oda_tahmini': scraped.get('oda_tahmini', ''),
                'teknik_ozellikler': scraped.get('specs', {})
            }
        })
    else:
        return jsonify(result)

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Dashboard istatistikleri"""
    conn = get_db_connection()
    
    # Toplam bütçe
    butce = conn.execute('SELECT toplam_butce FROM butce WHERE id = 1').fetchone()
    toplam_butce = butce['toplam_butce'] if butce else 0
    
    # Harcanan (Alındı statüsündekiler)
    harcanan = conn.execute('SELECT COALESCE(SUM(fiyat), 0) as toplam FROM urunler WHERE statu = "Alındı"').fetchone()
    harcanan_tutar = harcanan['toplam']
    
    # Planlanan (Araştırılıyor)
    planlanan = conn.execute('SELECT COALESCE(SUM(fiyat), 0) as toplam FROM urunler WHERE statu = "Araştırılıyor"').fetchone()
    planlanan_tutar = planlanan['toplam']
    
    # Ürün sayıları
    toplam_urun = conn.execute('SELECT COUNT(*) as sayi FROM urunler').fetchone()['sayi']
    alinan_urun = conn.execute('SELECT COUNT(*) as sayi FROM urunler WHERE statu = "Alındı"').fetchone()['sayi']
    
    # Kategorilere göre dağılım
    kategori_dagilim = conn.execute('''
        SELECT kategori, COUNT(*) as sayi, COALESCE(SUM(fiyat), 0) as toplam 
        FROM urunler GROUP BY kategori
    ''').fetchall()
    
    # Odalara göre dağılım
    oda_dagilim = conn.execute('''
        SELECT oda, COUNT(*) as sayi, COALESCE(SUM(fiyat), 0) as toplam 
        FROM urunler GROUP BY oda
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'toplam_butce': toplam_butce,
        'harcanan_tutar': harcanan_tutar,
        'planlanan_tutar': planlanan_tutar,
        'kalan_butce': toplam_butce - harcanan_tutar,
        'toplam_urun': toplam_urun,
        'alinan_urun': alinan_urun,
        'kategori_dagilim': [dict(k) for k in kategori_dagilim],
        'oda_dagilim': [dict(o) for o in oda_dagilim]
    })

@app.route('/api/butce', methods=['PUT'])
def update_butce():
    """Bütçe güncelle"""
    data = request.get_json()
    yeni_butce = float(data.get('toplam_butce', 0))
    
    conn = get_db_connection()
    conn.execute('UPDATE butce SET toplam_butce = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1', (yeni_butce,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Bütçe güncellendi!'})

@app.route('/api/export/excel', methods=['GET'])
def export_excel():
    """Excel olarak dışa aktar - Tüm Ürünler"""
    conn = get_db_connection()
    urunler = conn.execute('SELECT * FROM urunler ORDER BY kategori, oda').fetchall()
    conn.close()

    # Tüm teknik özellikleri topla (hangi alanların kullanıldığını öğrenmek için)
    all_spec_keys = set()
    for u in urunler:
        if u['teknik_ozellikler']:
            teknik = json.loads(u['teknik_ozellikler'])
            all_spec_keys.update(teknik.keys())

    # Ortak teknik alanlar için güzel isimler
    spec_name_mapping = {
        'enerji_sinifi': 'Enerji Sınıfı',
        'kapasite_kg': 'Kapasite (kg)',
        'devir_sayisi': 'Devir/dk',
        'su_tuketimi_lt': 'Su Tüketimi (lt)',
        'yillik_su_tuketimi_lt': 'Yıllık Su Tüketimi (lt)',
        'gurultu_db': 'Gürültü (dB)',
        'gurultu_yikama_db': 'Yıkama Gürültüsü (dB)',
        'gurultu_sikma_db': 'Sıkma Gürültüsü (dB)',
        'yikama_programlari': 'Program Sayısı',
        'garanti_suresi': 'Garanti Süresi',
        'olculer': 'Ölçüler',
        'kapasite_kisilik': 'Kapasite (kişilik)',
        'kurutma_sinifi': 'Kurutma Sınıfı',
        'brut_hacim_lt': 'Brüt Hacim (lt)',
        'net_hacim_lt': 'Net Hacim (lt)',
        'sogutma_tipi': 'Soğutma Tipi',
        'dondurucu_hacim_lt': 'Dondurucu Hacim (lt)',
        'yillik_enerji_tuketimi_kwh': 'Yıllık Enerji Tük. (kWh)',
        'malzeme': 'Malzeme',
        'kumas_tipi': 'Kumaş Tipi',
        'renk': 'Renk',
        'kisi_kapasitesi': 'Kişi Kapasitesi',
        'agirlik_kg': 'Ağırlık (kg)',
        'olculer_3lu': '3\'lü Koltuk Ölçüleri',
        'olculer_2li': '2\'li Koltuk Ölçüleri',
        'olculer_berjer': 'Berjer Ölçüleri',
        'ekran_boyutu': 'Ekran Boyutu',
        'cozunurluk': 'Çözünürlük'
    }

    # DataFrame oluştur
    data = []
    for u in urunler:
        teknik = json.loads(u['teknik_ozellikler']) if u['teknik_ozellikler'] else {}

        # Önce temel bilgiler (kullanıcı için okunabilir sütunlar)
        row = {
            'ID': u['id'],
            'Ürün Adı': u['urun_adi'],
            'Marka': u['marka'],
            'Fiyat (TL)': u['fiyat'],
            'Statü': u['statu'],
            'Kategori': u['kategori'],
            'Alt Kategori': u['alt_kategori'] if 'alt_kategori' in u.keys() else '',
            'Oda': u['oda'],
            'Öncelik': u['oncelik'],
            'Notlar': u['notlar'],
        }

        # Sonra teknik özellikler (her biri ayrı sütun)
        for spec_key in sorted(all_spec_keys):
            nice_name = spec_name_mapping.get(spec_key, spec_key.replace('_', ' ').title())
            row[nice_name] = teknik.get(spec_key, '')

        # En sona link ve resim URL
        row['Link'] = u['link']
        row['Resim URL'] = u['resim_url']
        row['Eklenme Tarihi'] = u['created_at']

        data.append(row)

    df = pd.DataFrame(data)

    # Excel dosyası oluştur
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Tüm Ürünler', index=False)

        # Sütun genişliklerini ayarla
        worksheet = writer.sheets['Tüm Ürünler']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
            # Excel sütun harfi hesapla
            if idx < 26:
                col_letter = chr(65 + idx)
            else:
                col_letter = chr(64 + idx // 26) + chr(65 + idx % 26)
            worksheet.column_dimensions[col_letter].width = min(max_length, 50)

    output.seek(0)

    filename = f'ev_esyalari_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/export/excel/alinanlar', methods=['GET'])
def export_excel_alinanlar():
    """Excel olarak dışa aktar - Sadece Alınan Ürünler"""
    conn = get_db_connection()
    urunler = conn.execute('SELECT * FROM urunler WHERE statu = "Alındı" ORDER BY kategori, oda').fetchall()
    conn.close()

    if len(urunler) == 0:
        return jsonify({'success': False, 'error': 'Henüz alınan ürün bulunmuyor'}), 404

    # Toplam harcama hesapla
    toplam_harcama = sum([u['fiyat'] or 0 for u in urunler])

    # Tüm teknik özellikleri topla
    all_spec_keys = set()
    for u in urunler:
        if u['teknik_ozellikler']:
            teknik = json.loads(u['teknik_ozellikler'])
            all_spec_keys.update(teknik.keys())

    # Ortak teknik alanlar için güzel isimler
    spec_name_mapping = {
        'enerji_sinifi': 'Enerji Sınıfı',
        'kapasite_kg': 'Kapasite (kg)',
        'devir_sayisi': 'Devir/dk',
        'su_tuketimi_lt': 'Su Tüketimi (lt)',
        'yillik_su_tuketimi_lt': 'Yıllık Su Tüketimi (lt)',
        'gurultu_db': 'Gürültü (dB)',
        'gurultu_yikama_db': 'Yıkama Gürültüsü (dB)',
        'gurultu_sikma_db': 'Sıkma Gürültüsü (dB)',
        'yikama_programlari': 'Program Sayısı',
        'garanti_suresi': 'Garanti Süresi',
        'olculer': 'Ölçüler',
        'kapasite_kisilik': 'Kapasite (kişilik)',
        'kurutma_sinifi': 'Kurutma Sınıfı',
        'brut_hacim_lt': 'Brüt Hacim (lt)',
        'net_hacim_lt': 'Net Hacim (lt)',
        'sogutma_tipi': 'Soğutma Tipi',
        'dondurucu_hacim_lt': 'Dondurucu Hacim (lt)',
        'yillik_enerji_tuketimi_kwh': 'Yıllık Enerji Tük. (kWh)',
        'malzeme': 'Malzeme',
        'kumas_tipi': 'Kumaş Tipi',
        'renk': 'Renk',
        'kisi_kapasitesi': 'Kişi Kapasitesi',
        'agirlik_kg': 'Ağırlık (kg)',
        'olculer_3lu': '3\'lü Koltuk Ölçüleri',
        'olculer_2li': '2\'li Koltuk Ölçüleri',
        'olculer_berjer': 'Berjer Ölçüleri',
        'ekran_boyutu': 'Ekran Boyutu',
        'cozunurluk': 'Çözünürlük'
    }

    # DataFrame oluştur
    data = []
    for u in urunler:
        teknik = json.loads(u['teknik_ozellikler']) if u['teknik_ozellikler'] else {}

        row = {
            'ID': u['id'],
            'Ürün Adı': u['urun_adi'],
            'Marka': u['marka'],
            'Fiyat (TL)': u['fiyat'],
            'Kategori': u['kategori'],
            'Alt Kategori': u['alt_kategori'] if 'alt_kategori' in u.keys() else '',
            'Oda': u['oda'],
            'Öncelik': u['oncelik'],
            'Notlar': u['notlar'],
        }

        # Teknik özellikler
        for spec_key in sorted(all_spec_keys):
            nice_name = spec_name_mapping.get(spec_key, spec_key.replace('_', ' ').title())
            row[nice_name] = teknik.get(spec_key, '')

        # Link ve resim URL
        row['Link'] = u['link']
        row['Resim URL'] = u['resim_url']
        row['Eklenme Tarihi'] = u['created_at']

        data.append(row)

    df = pd.DataFrame(data)

    # Excel dosyası oluştur
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Alınan ürünler sheet
        df.to_excel(writer, sheet_name='Alınan Ürünler', index=False)

        # Özet sheet
        ozet_data = {
            'Bilgi': ['Toplam Ürün Sayısı', 'Toplam Harcama (TL)', 'Ortalama Ürün Fiyatı (TL)'],
            'Değer': [len(urunler), toplam_harcama, toplam_harcama / len(urunler) if len(urunler) > 0 else 0]
        }
        df_ozet = pd.DataFrame(ozet_data)
        df_ozet.to_excel(writer, sheet_name='Özet', index=False)

        # Sütun genişliklerini ayarla - Alınan Ürünler
        worksheet = writer.sheets['Alınan Ürünler']
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
            if idx < 26:
                col_letter = chr(65 + idx)
            else:
                col_letter = chr(64 + idx // 26) + chr(65 + idx % 26)
            worksheet.column_dimensions[col_letter].width = min(max_length, 50)

        # Sütun genişliklerini ayarla - Özet
        worksheet_ozet = writer.sheets['Özet']
        worksheet_ozet.column_dimensions['A'].width = 30
        worksheet_ozet.column_dimensions['B'].width = 20

    output.seek(0)

    filename = f'alinan_urunler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/statu/<int:id>', methods=['PATCH'])
def toggle_statu(id):
    """Statü hızlı değiştir"""
    data = request.get_json()
    yeni_statu = data.get('statu', 'Araştırılıyor')
    
    conn = get_db_connection()
    conn.execute('UPDATE urunler SET statu = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (yeni_statu, id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/kategori-alanlari', methods=['GET'])
def get_kategori_alanlari():
    """Kategori alanlarını döndür"""
    return jsonify(KATEGORI_ALANLARI)

@app.route('/api/backup/json', methods=['GET'])
def backup_json():
    """Tüm veritabanını JSON olarak yedekle"""
    try:
        conn = get_db_connection()

        # Ürünleri çek
        urunler = conn.execute('SELECT * FROM urunler ORDER BY id').fetchall()
        urunler_list = [dict(row) for row in urunler]

        # Bütçeyi çek
        butce = conn.execute('SELECT * FROM butce WHERE id = 1').fetchone()
        butce_dict = dict(butce) if butce else {'toplam_butce': 0}

        conn.close()

        # JSON yapısı oluştur
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'version': '1.0',
            'butce': butce_dict,
            'urunler': urunler_list
        }

        # JSON dosyası oluştur
        filename = f'yeni_yuva_yedek_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        return jsonify({
            'success': True,
            'data': backup_data,
            'filename': filename
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/restore/json', methods=['POST'])
def restore_json():
    """JSON yedeğinden veritabanını geri yükle"""
    try:
        data = request.get_json()
        backup_data = data.get('backup_data')

        if not backup_data:
            return jsonify({'success': False, 'error': 'Yedek verisi bulunamadı'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Mevcut verileri temizle (OPSIYONEL - kullanıcıya sorulabilir)
        replace_existing = data.get('replace_existing', False)
        if replace_existing:
            cursor.execute('DELETE FROM urunler')

        # Bütçeyi geri yükle
        if 'butce' in backup_data:
            butce = backup_data['butce']
            cursor.execute('''
                UPDATE butce
                SET toplam_butce = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
            ''', (butce.get('toplam_butce', 0),))

        # Ürünleri geri yükle
        if 'urunler' in backup_data:
            for urun in backup_data['urunler']:
                # ID'yi yedeğe bırak veya yeni oluştur
                if replace_existing and 'id' in urun:
                    # ID'yi koruyarak ekle
                    cursor.execute('''
                        INSERT INTO urunler (
                            id, urun_adi, marka, fiyat, indirimli_fiyat, fiyat_guncelleme_tarihi,
                            link, resim_url, kategori, alt_kategori, oda, statu, oncelik,
                            teknik_ozellikler, notlar, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        urun.get('id'),
                        urun.get('urun_adi'),
                        urun.get('marka'),
                        urun.get('fiyat', 0),
                        urun.get('indirimli_fiyat'),
                        urun.get('fiyat_guncelleme_tarihi'),
                        urun.get('link'),
                        urun.get('resim_url'),
                        urun.get('kategori', 'Diğer'),
                        urun.get('alt_kategori', 'Genel'),
                        urun.get('oda', 'Salon'),
                        urun.get('statu', 'Araştırılıyor'),
                        urun.get('oncelik', 'Normal'),
                        urun.get('teknik_ozellikler'),
                        urun.get('notlar'),
                        urun.get('created_at'),
                        urun.get('updated_at')
                    ))
                else:
                    # Yeni ID ile ekle
                    cursor.execute('''
                        INSERT INTO urunler (
                            urun_adi, marka, fiyat, indirimli_fiyat, fiyat_guncelleme_tarihi,
                            link, resim_url, kategori, alt_kategori, oda, statu, oncelik,
                            teknik_ozellikler, notlar, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        urun.get('urun_adi'),
                        urun.get('marka'),
                        urun.get('fiyat', 0),
                        urun.get('indirimli_fiyat'),
                        urun.get('fiyat_guncelleme_tarihi'),
                        urun.get('link'),
                        urun.get('resim_url'),
                        urun.get('kategori', 'Diğer'),
                        urun.get('alt_kategori', 'Genel'),
                        urun.get('oda', 'Salon'),
                        urun.get('statu', 'Araştırılıyor'),
                        urun.get('oncelik', 'Normal'),
                        urun.get('teknik_ozellikler'),
                        urun.get('notlar'),
                        urun.get('created_at'),
                        urun.get('updated_at')
                    ))

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f'{len(backup_data.get("urunler", []))} ürün geri yüklendi'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Startup
if __name__ == '__main__':
    ensure_upload_folder()
    init_db()
    print("\n" + "="*50)
    print("🏠 Akıllı Ev Eşyası Yönetim Sistemi")
    print("="*50)
    
    # Replit veya local ortam tespiti
    port = int(os.environ.get('PORT', 5000))
    
    print(f"📍 http://0.0.0.0:{port} adresinde çalışıyor")
    print("="*50 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)
