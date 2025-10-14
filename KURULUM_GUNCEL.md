# 🚀 Güncellenmiş Kurulum Talimatları

## ✅ Yapılan Değişiklikler

### MoviePy → FFmpeg Geçişi
- **Eski:** MoviePy (video_fps hatası veren sorunlu paket)
- **Yeni:** ffmpeg-python + opencv-python (stabil ve hızlı)

### Düzeltilen Sorunlar:
1. ✅ `video_fps` hatası çözüldü
2. ✅ Video'dan audio extraction düzeltildi
3. ✅ Avatar video generation optimize edildi
4. ✅ Daha hızlı ve stabil video işleme

---

## 🔧 KURULUM ADIMLARI

### Adım 1: Eski Paketleri Kaldır

Terminal'de uygulamayı durdurun (Ctrl+C) ve şu komutları çalıştırın:

```bash
pip uninstall moviepy pydub -y
```

### Adım 2: Yeni Paketleri Yükle

```bash
pip install -r requirements.txt
```

Veya manuel olarak:

```bash
pip install ffmpeg-python==0.2.0
pip install imageio-ffmpeg==0.4.9
pip install opencv-python==4.8.1.78
```

### Adım 3: Uygulamayı Başlat

```bash
python run.py
```

---

## 🧪 TEST ADIMLARI

### 1. Speech-to-Text (Video) Testi:

1. STT sayfasına gidin
2. **SESLİ** bir video dosyası yükleyin
3. "Start Transcription" tıklayın
4. ✅ Artık çalışacak!

**Not:** Video'nun ses track'i olmalı!

### 2. Avatar Video Testi:

1. Avatar sayfasına gidin
2. Fotoğrafınızı yükleyin (gerçek fotoğraf olarak kullanılacak)
3. Metin girin
4. "Generate Video" tıklayın
5. ✅ Video oluşacak!
6. "Download Video" ile indir

---

## 📋 Yeni Requirements.txt İçeriği

```txt
# Core Web Framework
Flask==3.0.0
Flask-CORS==4.0.0
python-dotenv==1.0.0

# OpenAI API
openai==1.7.0

# File Processing
Pillow==10.1.0
werkzeug==3.0.0

# Audio/Video Processing
ffmpeg-python==0.2.0
imageio-ffmpeg==0.4.9
opencv-python==4.8.1.78

# Utilities
requests==2.31.0
```

---

## ⚠️ ÖNEMLI NOTLAR

### FFmpeg Otomatik Kurulum:
- `imageio-ffmpeg` paketi otomatik olarak ffmpeg binary'sini indirir
- Windows, Mac, Linux desteklenir
- Manuel kurulum **GEREKMİyor**

### Video Gereksinimleri:
- **Ses track'i olmalı** (sessiz videolar çalışmaz)
- Desteklenen: MP4, AVI, MOV, MKV, WEBM
- Max boyut: 200 MB

### Avatar:
- Artık gerçek fotoğrafınız kullanılıyor
- Animasyon karakteri değil, gerçekçi
- Otomatik 1024x1024 resize

---

## 🐛 Sorun Giderme

### Hata: "FFmpeg not found"
- Uygulamayı yeniden başlatın
- `pip install imageio-ffmpeg --upgrade` çalıştırın

### Hata: "Video has no audio"
- Videonuzda ses yok
- Farklı video deneyin veya audio dosyası yükleyin

### Hata: Video download çalışmıyor
- Tarayıcıyı yenileyin
- Session temizlenmiş olabilir

---

## ✨ Avantajlar

### FFmpeg ile:
- ✅ Daha hızlı işlem
- ✅ Daha stabil
- ✅ Daha az hata
- ✅ Daha iyi performans
- ✅ Otomatik kurulum

### MoviePy ile Sorunlar (eski):
- ❌ video_fps hataları
- ❌ Yavaş işlem
- ❌ Bağımlılık sorunları
- ❌ Kararsız API

---

## 🎉 Sonuç

Artık tüm video işlemleri FFmpeg ile yapılıyor. Daha hızlı, daha stabil, daha az hata!

**SON ADIM:** 
```bash
pip install -r requirements.txt
python run.py
```

Başarılı! 🚀

