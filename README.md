# Speech & Clone App

Modern Python web uygulaması - Ses/video dosyalarından metin çıkarma, metinden ses üretme, ses klonlama ve video dublaj özellikleri.

## 🚀 Özellikler

- **Speech-to-Text**: OpenAI Whisper ile çok dilli ses/video transkripsiyonu
- **Text-to-Speech**: OpenAI TTS ile metinden doğal ses üretimi
- **Voice Cloning**: MiniMax API ile ses klonlama ve özel ses kullanımı
- **Video Dubbing**: Video dublaj - çeviri ve ses değiştirme
- **Session-Based**: Tüm veriler geçici olarak session'da saklanır (veritabanı gerektirmez)
- **Modern Arayüz**: Responsive ve kullanıcı dostu web arayüzü
- **No Authentication**: Doğrudan kullanıma hazır, kayıt/giriş gerektirmez

## 📋 Gereksinimler

- Python 3.9+
- OpenAI API key (Whisper, TTS için)
- MiniMax API key (Ses klonlama için)

## 🛠️ Kurulum

### 1. Projeyi İndirin
```bash
git clone <repository-url>
cd PythonProje
```

### 2. Virtual Environment Oluşturun
```bash
python -m venv venv
```

### 3. Virtual Environment'ı Aktive Edin

**Windows:**
```bash
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Gerekli Paketleri Yükleyin
```bash
pip install -r requirements.txt
```

### 5. Environment Dosyasını Yapılandırın

Proje kök dizininde `.env` dosyası oluşturun:

```env
# Flask Configuration
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production-12345

# OpenAI API
OPENAI_API_KEY=sk-XXXXX

# File Upload Configuration
MAX_FILE_SIZE_MB=200
MAX_TEXT_LENGTH=1000
UPLOAD_FOLDER=uploads

# Application Settings
APP_NAME=Speech & Clone App
APP_URL=http://localhost:5000

# MiniMax API (Voice Cloning)
MINIMAX_API_KEY=your-minimax-api-key
MINIMAX_GROUP_ID=your-minimax-group-id
```

### 6. API Key'leri Nasıl Alınır

**OpenAI API Key:**
1. https://platform.openai.com/api-keys adresine gidin
2. Hesap oluşturun veya giriş yapın
3. "Create new secret key" butonuna tıklayın
4. API key'i kopyalayın ve `.env` dosyasına ekleyin

**MiniMax API Key:**
1. https://api.minimax.chat adresine gidin
2. Hesap oluşturun
3. API Settings bölümünden API Key oluşturun
4. API Key ve Group ID'yi `.env` dosyasına ekleyin

### 7. Gerekli Klasörleri Oluşturun
```bash
mkdir uploads
mkdir temp
```

### 8. Uygulamayı Başlatın
```bash
python run.py
```

Uygulama `http://localhost:5000` adresinde çalışacaktır.

## 📁 Proje Yapısı

```
PythonProje/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes/              # Route handlers
│   │   ├── main.py         # Ana sayfalar
│   │   ├── stt.py          # Speech-to-Text
│   │   ├── tts.py          # Text-to-Speech
│   │   ├── voice_clone.py  # Voice Cloning
│   │   └── dubbing.py      # Video Dubbing
│   ├── services/           # Business logic
│   │   ├── whisper_service.py
│   │   ├── tts_service.py
│   │   ├── voice_clone_service.py
│   │   └── dubbing_service.py
│   ├── templates/          # HTML templates
│   ├── static/            # CSS, JS, images
│   └── utils/             # Utility functions
├── uploads/               # Uploaded files
├── temp/                 # Temporary files
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
└── run.py               # Application entry point
```

## 🎯 Kullanım

### Speech-to-Text
- Ses veya video dosyası yükleyin
- Otomatik dil tespiti veya manuel dil seçimi
- Metin transkripsiyonu

### Text-to-Speech
- Metin girin
- Ses seçin (Alloy, Echo, Fable, Onyx, Nova, Shimmer)
- Ses dosyası oluşturun

### Voice Cloning
- Referans ses dosyası yükleyin
- Ses modelini eğitin
- Klonlanmış sesle konuşma üretin

### Video Dubbing
- Video dosyası yükleyin
- Kaynak ve hedef dil seçin
- Ses hızını ayarlayın (opsiyonel)
- Dublajlı video oluşturun

## 🔧 Yapılandırma

Tüm yapılandırma ayarları `.env` dosyasında tutulur:

- `OPENAI_API_KEY`: OpenAI API anahtarı (gerekli)
- `MINIMAX_API_KEY`: MiniMax API anahtarı (ses klonlama için)
- `MINIMAX_GROUP_ID`: MiniMax Group ID (opsiyonel)
- `MAX_FILE_SIZE_MB`: Maksimum dosya boyutu (varsayılan: 200MB)
- `MAX_TEXT_LENGTH`: Maksimum metin uzunluğu (varsayılan: 1000 karakter)

## 💾 Veri Saklama

- **Session Verileri**: Kullanıcı tercihleri ve geçici bilgiler Flask session'da saklanır
- **Dosya Saklama**: 
  - `uploads/` klasörü: Yüklenen ses/video dosyaları
  - `temp/` klasörü: İşlenmiş dosyalar ve geçici çıktılar
- **Hafıza**: Klonlanmış ses modelleri uygulama çalıştığı sürece hafızada kalır
- **Temizlik**: Uygulama kapatıldığında session verileri silinir, dosyalar kalır
- **Veritabanı**: Kullanılmaz - tüm veriler dosya sistemi ve session'da

## 🐛 Sorun Giderme

### Yaygın Sorunlar

**"No module named 'app'" hatası:**
```bash
# Virtual environment'ın aktif olduğundan emin olun
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

**API Key hatası:**
- `.env` dosyasında API key'lerin doğru yazıldığından emin olun
- API key'lerin geçerli olduğunu kontrol edin

**Dosya yükleme hatası:**
- `uploads` ve `temp` klasörlerinin oluşturulduğundan emin olun
- Dosya boyutunun 200MB'dan küçük olduğunu kontrol edin

## 📝 Lisans

Internal development and testing only.

## 👨‍💻 Geliştirici

Sadıkcan TULUK - sadikcantuluk@gmail.com - https://sadikcantuluk.online