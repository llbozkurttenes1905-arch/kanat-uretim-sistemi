# 🏭 ERGÜNBAŞ Group — Kanat Üretim & Sipariş Portalı

Bu proje ERGÜNBAŞ fabrikası Kanat Bölümü için geliştirilmiş tam fonksiyonel üretim, sipariş ve makine takip sistemidir.

---

## 📁 Proje Dosyaları
- `app_backend.py` : FastAPI Backend sunucu ve veri mantığı
- `data_kanat.json` : Veritabanı (243 Sipariş, Üst ve Alt Tesis, Makineler)
- `users.json` : Kullanıcı hesapları veritabanı
- `requirements.txt` : Python kütüphane listesi
- `static/index.html` : Kurumsal ERGÜNBAŞ Yönetim Portalı Arayüzü
- `static/logo.png` : ERGÜNBAŞ Orijinal Logosu
- `BASLAT.bat` : Windows'ta çift tıklayıp tek komutla başlatma dosyası
- `Dockerfile` & `docker-compose.yml` : Docker sunucu kurulumu
- `Procfile` : Cloud / Render / Railway dağıtım dosyası

---

## 🚀 Canlıya Alma Seçenekleri

### 1. Kendi Sunucunuza (Linux VPS / Ubuntu Server) Kurma:
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
cd kanat-uretim-sistemi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app_backend:app --host 0.0.0.0 --port 8001
```

### 2. Docker ile Tek Komutta Başlatma:
```bash
docker-compose up -d --build
```

### 3. Buluta Yükleme (Render.com / Railway.app):
- Projeyi GitHub hesabınıza yükleyin.
- Render.com veya Railway.app üzerinde projeyi bağlayın; `Procfile` ve `requirements.txt` sayesinde otomatik olarak canlıya alınır.

### 4. Fabrika İçi Yerel Ağda (LAN) Canlı Kullanım:
- Bilgisayarınızda `BASLAT.bat` dosyasını çalıştırın.
- Fabrikadaki diğer telefon, tablet ve bilgisayarlar tarayıcıdan `http://<BILGISAYAR_IP_ADRESI>:8001` yazarak bağlanabilir.

---

## 🔑 Giriş Bilgileri:
- **Yönetici:** `admin` / `ergunbas2026`
- **Operatör:** `operator1` / `operator1`
