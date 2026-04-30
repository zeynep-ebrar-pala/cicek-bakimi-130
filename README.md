# Botanica AI

**Akıllı bitki tanıma, hastalık teşhisi ve bakım yönetimi için hibrit yapay zeka platformu.**

Botanica AI; görselden bitki tanıma, semptom analizi, günlük bakım takibi ve proaktif önerileri tek panelde sunan bir Streamlit uygulamasıdır.  
Gemini tabanlı görsel analiz ile yerel botanik veri tabanını birlikte kullanarak hem kütüphane içi hem kütüphane dışı bitkilerde sonuç üretir.

---

## Neden Güçlü?

- **Hibrit Teşhis Motoru:** AI + yerel veri tabanı yaklaşımıyla daha dayanıklı sonuç.
- **Kütüphane Dışı Bitki Desteği:** Eşleşme bulunamazsa dinamik profil üretimi.
- **Doktor Modu:** Görsel + semptom + kullanıcı notu ile zengin teşhis akışı.
- **Bahçe Operasyonları:** Sulama, gübreleme, sağlık durumu ve günlük kayıtları.
- **Yönetim Asistanı:** Raporlama, anomali taraması ve bakım optimizasyon önerileri.

---

## Özellikler

### 1) Bitki Rehberi
- Fotoğraftan tür tespiti
- Bitki detay sayfası (ışık, su, toprak, gübre önerileri)
- Kendi bahçene tek tıkla ekleme

### 2) Bitki Doktorum
- Sorunlu yaprak/gövde fotoğrafı ile analiz
- Semptom bazlı destek teşhisi
- AI destekli neden ve tedavi önerileri

### 3) Yeşil Köşem
- Kişisel bitki envanteri
- Sulama/gübreleme tarihçesi
- Hızlı bakım aksiyonları

### 4) Yönetim Merkezi
- Genel bahçe raporu
- Proaktif anomali kontrolü
- Sulama stratejisi optimizasyonu

---

## Teknoloji Mimarisi

| Katman | Teknoloji |
| :--- | :--- |
| Uygulama | Python 3.x |
| Arayüz | Streamlit |
| AI Görsel Analiz | Google Gemini 1.5 Flash |
| Yardımcı AI / Hibrit Kanal | Groq API (opsiyonel) |
| Veri Tabanı | SQLite (`garden.db`) |
| Stil | Custom CSS (`frontend/style.css`) |

---

## Proje Yapısı

```text
cicek-bakimi-130/
├── app.py                      # Streamlit Cloud entrypoint
├── frontend/
│   ├── app.py                  # Ana UI ve kullanıcı akışları
│   ├── style.css               # UI tema ve animasyonlar
│   └── decorations.py          # Görsel dekor bileşenleri
├── backend/
│   ├── data.py                 # Bitki/hastalık bilgi tabanı
│   ├── database.py             # SQLite veri erişim katmanı
│   ├── agent.py                # Yönetim asistanı mantığı
│   ├── utils.py                # Yardımcı fonksiyonlar
│   └── dev_layer.py            # Geliştirme yardımcı katmanı
├── assets/                     # Görsel varlıklar
├── requirements.txt
├── .env.example
└── README.md
```

---

## Kurulum (Lokal)

### 1) Bağımlılıklar
```bash
pip install -r requirements.txt
```

### 2) Ortam Değişkenleri
`.env` dosyası oluştur:

```env
GOOGLE_API_KEY=your_google_key
GROQ_API_KEY=your_groq_key
```

> `GROQ_API_KEY` zorunlu değildir, hibrit panelin tam kullanımında önerilir.

### 3) Çalıştırma
```bash
streamlit run app.py
```

Alternatif:
```bash
streamlit run frontend/app.py
```

---

## Streamlit Cloud Deploy

1. Projeyi GitHub’a gönder.
2. Streamlit Cloud’da yeni app oluştur.
3. **App file** olarak `app.py` seç.
4. **Secrets** alanına API anahtarlarını ekle:
   - `GOOGLE_API_KEY`
   - `GROQ_API_KEY` (opsiyonel)
5. Deploy et.

---

## Sorun Giderme

- **Uygulama açılıyor ama AI çalışmıyor:** API anahtarlarını kontrol et.
- **Fotoğraf yüklendi ama tür bulunamadı:** Kütüphane dışı tür olabilir; dinamik profil akışı devreye girer.
- **Görseller görünmüyor:** `assets/` yol yapısını ve dosya isimlerini kontrol et.
- **Veri tabanı hatası:** `garden.db` yazma izni olan dizinde çalıştır.

---

## Yol Haritası

- Dinamik tespit edilen türleri tek tıkla kalıcı kütüphaneye ekleme
- Çoklu dil desteği (TR/EN UI toggle)
- Gelişmiş bakım takvimi ve bildirim otomasyonu
- Teşhis çıktıları için yapılandırılmış JSON rapor ekranı

---

## Katkı

Öneri, hata bildirimi ve iyileştirme fikirleri için issue/PR açabilirsiniz.  
Kod standartlarını korumak için küçük ve odaklı değişikliklerle ilerlenmesi önerilir.

---

## Lisans ve İletişim

Bu proje eğitim ve ürün geliştirme amaçlıdır.  
Geliştirici: **Zeynep Ebrar PALA**  
© 2026 Botanica AI
