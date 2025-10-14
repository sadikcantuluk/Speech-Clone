# 🛠️ Sorun Çözümleri

## ✅ Yapılan Düzeltmeler

### 1. Video Download Hatası Düzeltildi
- **Sorun:** Video dosyası path hatası (FileNotFoundError)
- **Çözüm:** Absolute path kullanımı eklendi
- **Dosya:** `app/services/avatar_service.py`

### 2. Avatar Kalitesi İyileştirildi
- **Sorun:** Avatar animasyon karakteri gibi oluşuyordu
- **Çözüm:** Artık orijinal fotoğraf kullanılıyor (gerçekçi)
- **Dosya:** `app/services/avatar_service.py`

### 3. Video'dan Audio Extraction Hatası Düzeltildi
- **Sorun:** `'video_fps'` hatası
- **Çözüm:** Audio track kontrolü ve codec ayarları eklendi
- **Dosya:** `app/routes/stt.py`

---

## 🚀 Yapmanız Gerekenler

### Adım 1: FFmpeg Paketini Yükleyin

Terminal'de şu komutu çalıştırın:

```bash
pip install imageio-ffmpeg==0.4.9
```

VEYA tüm paketleri güncelleyin:

```bash
pip install -r requirements.txt --upgrade
```

### Adım 2: Uygulamayı Yeniden Başlatın

```bash
python run.py
```

---

## 📝 Test Adımları

### Avatar Video Testi:
1. Avatar sayfasına gidin
2. Fotoğrafınızı yükleyin
3. Metin girin ve "Generate Video" tıklayın
4. Video oluşacak ve "Download Video" butonu çalışacak

### Speech-to-Text Video Testi:
1. STT sayfasına gidin
2. **SESLİ** bir video dosyası yükleyin (önemli!)
3. Transcribe başlayacak

---

## ⚠️ Önemli Notlar

### Video Dosyaları İçin:
- Video dosyanızın **mutlaka ses track'i olması gerekir**
- Sessiz videolar çalışmaz
- Desteklenen formatlar: MP4, AVI, MOV, MKV, WEBP

### Avatar İçin:
- Artık orijinal fotoğrafınız kullanılıyor
- Gerçek görünümlü avatar (animasyon değil)
- Fotoğraf otomatik olarak işleniyor (1024x1024)

### FFmpeg Notu:
- `imageio-ffmpeg` paketi otomatik olarak ffmpeg binary'sini indirir
- Manuel kurulum gerekmez
- Windows, Mac, Linux desteklenir

---

## 🐛 Hala Sorun mu Yaşıyorsunuz?

### Hata: "No audio track"
- Videonuzda ses olmayabilir
- Farklı bir video deneyin
- Veya direkt audio dosyası (MP3, WAV) yükleyin

### Hata: Video download çalışmıyor
- Session'ı temizleyin (tarayıcıyı yeniden başlatın)
- Uygulamayı durdurup tekrar başlatın

### Hata: Avatar oluşmuyor
- Fotoğraf boyutunu kontrol edin (max 25MB)
- Desteklenen formatlar: JPG, PNG, WEBP
- Fotoğrafın net ve düzgün olduğundan emin olun

