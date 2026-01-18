# Yeni Yuva - Ev Eşyası Yönetim Sistemi

## Overview

Yeni Yuva is a smart home goods management system designed for couples preparing for marriage. It provides product tracking, budget management, and automated product information scraping from 30+ Turkish e-commerce websites. The application features a Pinterest-style responsive UI for browsing and managing home products with scenario-based cost calculations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Vue.js 3 (CDN-loaded via unpkg)
- **Styling**: Tailwind CSS (CDN-loaded)
- **Layout**: Pinterest-style masonry grid with responsive breakpoints
- **Design Pattern**: Single-page application with modal-based interactions
- **Template Location**: `templates/index.html` - monolithic Vue app embedded in Flask template

### Backend Architecture
- **Framework**: Flask 3.0 (Python)
- **Entry Point**: `app.py` - handles all routes, database operations, and API endpoints
- **Scraper Module**: `scraper.py` - intelligent web scraping with multi-strategy parsing
- **Pattern**: Monolithic architecture with modular scraping handlers

### Web Scraping System
The scraper uses a cascade/fallback approach for data extraction:
1. **Site-Specific Parsers** - Custom handlers for major platforms (Shopify, IKEA, Trendyol)
2. **JSON-LD Parser** - Structured data extraction
3. **DataLayer Parser** - Google Analytics/Tag Manager data mining
4. **Meta Tags Parser** - OpenGraph and product meta tags
5. **HTML Selectors** - Generic CSS selector fallback

**Key Features**:
- Cloudscraper integration for Cloudflare bypass
- User-Agent rotation
- Rate limiting (1.5s minimum between requests)
- 5-minute response caching
- Mobile URL normalization

### Data Storage
- **Database**: SQLite (`ev_esyalari.db`)
- **Schema**: Product-centric with dynamic category-specific fields
- **Categories**: Beyaz Eşya (appliances), Mobilya (furniture), Elektronik (electronics), etc.
- **Image Storage**: File uploads to `static/uploads/` with base64 fallback

### Category System
Products are organized by:
- **Main Category** (Beyaz Eşya, Mobilya, Elektronik, Tekstil, etc.)
- **Sub-Category** (Çamaşır Makinesi, Koltuk Takımı, Televizyon, etc.)
- **Room Assignment** (Salon, Yatak Odası, Mutfak, etc.)

Each category has specific technical fields (energy class, dimensions, capacity, etc.) defined in `KATEGORI_ALANLARI` dictionary.

## External Dependencies

### Python Packages
- **Flask 3.0.0** - Web framework
- **BeautifulSoup4 4.12.2** - HTML parsing
- **Requests 2.31.0** - HTTP client
- **Cloudscraper 1.2.71+** - Cloudflare bypass (optional but recommended)
- **Pandas 2.1.3** - Excel export functionality
- **Pillow 10.1.0** - Image processing
- **openpyxl 3.1.2** - Excel file generation

### Supported E-commerce Platforms
- **Marketplaces**: Trendyol, Hepsiburada, N11, Çiçeksepeti
- **Appliance Brands**: Arçelik, Beko, Vestel, Bosch, Samsung, LG, etc.
- **Furniture (Shopify)**: Enza Home, Normod, Vivense, Alfemo
- **Furniture (Other)**: IKEA, Bellona, İstikbal, Doğtaş
- **Home Textile**: English Home, Madame Coco, Yataş

### External APIs Used
- **Shopify Product JSON API** - `/products/{handle}.json` for Shopify stores
- **Trendyol Public API** - Product data extraction

### Environment Variables
- `SECRET_KEY` - Flask session security (required for production)
- `SCRAPER_DEBUG` - Enable verbose scraping logs (optional)