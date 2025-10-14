# Speech-to-Text & Text-to-Speech Web Application with Avatar Integration

Modern Python web uygulaması - Ses/video dosyalarından metin çıkarma, metinden ses üretme ve avatar entegrasyonu.

## 🚀 Özellikler

- **Speech-to-Text**: OpenAI Whisper ile çok dilli ses/video transkripsiyonu
- **Text-to-Speech**: Metinden doğal ses üretimi
- **AI Avatar Creation**: DALL-E ile kullanıcı fotoğrafından profesyonel avatar oluşturma
- **Realistic Lip-Sync**: Replicate Wav2Lip ile gerçekçi ağız hareketli avatar videoları
- **🎤 Voice Cloning**: ElevenLabs ile ses klonlama ve özel ses kullanımı
- **Session-Based**: Tüm veriler geçici olarak session'da saklanır (veritabanı gerektirmez)
- **Modern Arayüz**: Responsive ve kullanıcı dostu web arayüzü
- **No Authentication**: Doğrudan kullanıma hazır, kayıt/giriş gerektirmez

## 📋 Gereksinimler

- Python 3.9+
- OpenAI API key (DALL-E, Whisper, TTS için)
- Replicate API key (AI Lip-sync için) - İlk $5 ücretsiz
- MiniMax API key (Ses klonlama için)

## 🛠️ Kurulum

1. **Proje dizinine gidin:**
```bash
cd C:\PythonProje
```

2. **Virtual environment oluşturun:**
```bash
python -m venv venv
```

3. **Virtual environment'ı aktive edin:**
```bash
.\venv\Scripts\activate
```

4. **Gerekli paketleri yükleyin:**
```bash
pip install -r requirements.txt
```

5. **Environment dosyasını yapılandırın:**
`.env` dosyasını düzenleyerek API anahtarlarınızı ekleyin:
- `OPENAI_API_KEY` - OpenAI API anahtarınız (gerekli)
- `REPLICATE_API_KEY` - Replicate API anahtarınız (AI lip-sync için)
- `MINIMAX_API_KEY` - MiniMax API anahtarınız (ses klonlama için)
- `MINIMAX_GROUP_ID` - MiniMax Group ID (opsiyonel)

**API Key'leri nasıl alınır:**

**OpenAI:**
1. https://platform.openai.com/api-keys
2. API key oluştur ve kopyala

**Replicate:**
1. https://replicate.com/signin
2. GitHub ile giriş yap
3. Profil > API tokens > token kopyala

**MiniMax:**
1. https://minimax.io veya https://api.minimax.chat
2. Kayıt ol
3. API Settings > API Key oluştur
4. API Key ve Group ID'yi kopyala (varsa)

6. **Uploads klasörünü oluşturun:**
```bash
mkdir uploads
mkdir temp
```

7. **Uygulamayı başlatın:**
```bash
python run.py
```

Uygulama `http://localhost:5000` adresinde çalışacaktır.

## 📁 Proje Yapısı

```
PythonProje/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── static/
├── uploads/
├── .env
├── requirements.txt
└── run.py
```

## 🔧 Yapılandırma

Tüm yapılandırma ayarları `.env` dosyasında tutulur. Sadece OpenAI API anahtarı gereklidir.

## 💾 Veri Saklama

- Tüm veriler Flask session'da geçici olarak saklanır
- Avatar bilgileri uygulama çalıştığı sürece hafızada kalır
- Uygulama kapatıldığında tüm veriler silinir
- Veritabanı kullanılmaz

## 📝 Lisans

Internal development and testing only.

