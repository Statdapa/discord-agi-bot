# 🤖 Discord Multi-Agent AI System
### 5 Bot Terpisah — Self-Correcting Pipeline

```
User kasih task
      ↓
🎯 ORCHESTRATOR  →  analisis & bagi tugas
      ↓
⚙️  WORKER        →  kerjakan task utama
      ↓
🔍 CRITIC         →  review & koreksi
      ↓ (loop sampai bagus)
✨ REFINER        →  poles jadi premium
      ↓
🔬 FACTCHECKER    →  verifikasi akurasi
      ↓
✅ HASIL FINAL → dikirim ke user
```

---

## ⚡ Setup (Step by Step)

### STEP 1 — Buat 5 Discord Bot
1. Buka [discord.com/developers/applications](https://discord.com/developers/applications)
2. Buat **5 Application** baru dengan nama:
   - `AGI-Orchestrator`
   - `AGI-Worker`
   - `AGI-Critic`
   - `AGI-Refiner`
   - `AGI-FactChecker`
3. Untuk setiap bot: Tab **Bot** → **Add Bot** → aktifkan **Message Content Intent**
4. Copy masing-masing token

### STEP 2 — Buat Groq API Key
1. Buka [console.groq.com](https://console.groq.com)
2. API Keys → Create API Key → Copy

### STEP 3 — Setup Discord Server
Buat 2 channel di server Discord:
- `#workspace` — tempat bot-bot bekerja (boleh hidden dari user biasa)
- `#hasil` — tempat hasil final dikirim ke user

Cara dapatkan Channel ID:
1. Discord Settings → Advanced → aktifkan **Developer Mode**
2. Klik kanan channel → **Copy Channel ID**

Invite semua 5 bot ke server (via OAuth2 → URL Generator di setiap app)

### STEP 4 — Konfigurasi .env
```bash
cp .env.example .env
```
Isi semua value di file `.env`

### STEP 5 — Install & Run
```bash
pip install -r requirements.txt

# Jalankan semua bot sekaligus:
python run_all.py

# Atau jalankan satu per satu (di terminal terpisah):
python bot1_orchestrator/main.py
python bot2_worker/main.py
python bot3_critic/main.py
python bot4_refiner/main.py
python bot5_factchecker/main.py
```

---

## 💬 Cara Pakai

Di channel Discord manapun, ketik:
```
!task Buatkan strategi marketing untuk startup AI saya yang targetnya developer Indonesia
```

Bot akan bekerja otomatis sampai hasilnya disetujui semua agent, lalu hasilnya muncul di `#hasil`.

---

## 🔄 Alur Pipeline Detail

```
1. User: !task [deskripsi]
2. Orchestrator: analisis → kirim brief ke #workspace
3. Worker: baca brief → kerjakan → kirim ke Critic
4. Critic: review → 
   - Jika kurang baik: kembalikan ke Worker (LOOP)
   - Jika OK: teruskan ke Refiner
5. Refiner: poles → kirim ke FactChecker
6. FactChecker: verifikasi →
   - Jika ada masalah: kembalikan ke Refiner (LOOP)
   - Jika OK: kirim FINAL_APPROVED ke #hasil
7. User menerima hasil final yang sudah disetujui semua agent ✅
```

---

## 📁 Struktur
```
discord-multi-bot/
├── bot1_orchestrator/main.py
├── bot2_worker/main.py
├── bot3_critic/main.py
├── bot4_refiner/main.py
├── bot5_factchecker/main.py
├── run_all.py          ← jalankan semua sekaligus
├── .env.example
├── .env                ← isi ini (jangan di-commit!)
└── requirements.txt
```

---

## ⚠️ Tips
- Jangan commit file `.env` ke GitHub
- Channel `#workspace` bisa di-set private (hanya bot yang bisa akses)
- Groq free tier cukup untuk personal use (~14.400 req/hari)
- Untuk production: pertimbangkan VPS agar bot nyala 24/7

---

*Dibangun untuk builder muda yang bermimpi menguasai dunia dengan AI* 🚀