# Discord Chat Bot 🤖

Bot Discord ringkas menggunakan Python dengan discord.py.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables
- Salin `.env.example` ke `.env`
```bash
cp .env.example .env
```
- Edit `.env` dan masukkan token Discord bot anda

### 3. Dapatkan Discord Token
1. Pergi ke [Discord Developer Portal](https://discord.com/developers/applications)
2. Klik "New Application"
3. Pergi ke "Bot" section dan klik "Add Bot"
4. Copy token anda
5. Pastikan "Message Content Intent" dan "Server Members Intent" diaktifkan di bawah "Privileged Gateway Intents"

### 4. Invite Bot ke Server
1. Di Developer Portal, pergi ke "OAuth2" → "URL Generator"
2. Centang scope: `bot`, `applications.commands`
3. Centang permissions yang diperlukan (contoh: Send Messages, Manage Messages)
4. Copy URL dan buka dalam browser untuk invite bot

### 5. Jalankan Bot
```bash
python main.py
```

## Commands yang Tersedia

| Command | Description |
|---------|-------------|
| `!ping` | Semak kelewatan bot |
| `!help` | Papar senarai perintah |
| `!info` | Maklumat tentang bot |
| `!say <teks>` | Bot akan ulang kata-kata anda |
| `!clear <bilangan>` | Padam mesej (admin sahaja) |

## Struktur Folder
```
discord-chat-bot/
├── main.py           # Fail utama bot
├── requirements.txt  # Dependencies
├── .env.example     # Contoh environment variables
└── README.md        # Dokumentasi
```

## Tips
- Jangan commit fail `.env` ke GitHub (token adalah rahsia!)
- Anda boleh menambah commands baru dengan mengikuti contoh yang sedia ada
- Gunakan `cogs` untuk mengorganisasi commands dalam fail berasingan

---
Dibuat dengan ❤️ menggunakan Python
