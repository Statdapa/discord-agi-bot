"""
BOT 6 - REMINDER v3
Jadwal harian otomatis 07.00 dan 20.00 WIB. Tanpa emoji.
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime
import pytz

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("REMINDER_BOT_TOKEN")
REMINDER_CHANNEL_ID = int(os.getenv("REMINDER_CHANNEL_ID"))
WIB = pytz.timezone("Asia/Jakarta")

groq_client = Groq(api_key=GROQ_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

LEARNING_TOPICS = [
    "Dasar Machine Learning: supervised vs unsupervised learning",
    "Neural Network: backpropagation dan gradient descent",
    "Python untuk AI: NumPy, Pandas, Matplotlib",
    "Deep Learning dengan PyTorch: membangun model pertama",
    "Natural Language Processing: tokenisasi dan word embedding",
    "Transformer Architecture: mekanisme attention",
    "Fine-tuning LLM dengan dataset sendiri",
    "Multi-agent System: koordinasi antar agent AI",
    "Reinforcement Learning: reward, policy, dan Q-learning",
    "AI Alignment: pentingnya keamanan dalam pengembangan AI",
    "Prompt Engineering: teknik optimal berinteraksi dengan LLM",
    "Membangun REST API AI dengan FastAPI",
    "Vector Database dan RAG System",
    "Computer Vision: CNN dan deteksi objek",
    "Membangun startup AI: dari konsep ke produk",
]

MORNING_SYSTEM = """
Kamu adalah mentor AI profesional untuk seorang pemuda berusia 19-22 tahun
yang sedang membangun karir di bidang AI dan bermimpi mendirikan perusahaan AI sendiri.

Buat jadwal harian pagi yang terstruktur, motivatif, dan actionable.
Gunakan Bahasa Indonesia yang profesional namun tetap hangat dan mendorong.
Tidak ada emoji. Format harus rapi dan mudah dibaca.
"""

EVENING_SYSTEM = """
Kamu adalah mentor AI profesional untuk seorang pemuda berusia 19-22 tahun
yang sedang membangun karir di bidang AI.

Buat review malam yang reflektif, evaluatif, dan memotivasi untuk hari esok.
Gunakan Bahasa Indonesia yang profesional namun tetap hangat.
Tidak ada emoji.
"""

def get_topic():
    return LEARNING_TOPICS[datetime.now(WIB).timetuple().tm_yday % len(LEARNING_TOPICS)]

def ask_groq(system, prompt):
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8, max_tokens=800,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"

def build_morning():
    topic = get_topic()
    today = datetime.now(WIB).strftime("%A, %d %B %Y")
    prompt = f"""
Hari ini: {today}
Topik belajar hari ini: {topic}

Buat jadwal harian pagi dalam format berikut:

SELAMAT PAGI
Tanggal: {today}
---

AGENDA BELAJAR (1-2 jam)
Topik: {topic}
Panduan belajar: (1 tip spesifik dan efektif untuk mempelajari topik ini)
Sumber rekomendasi: (sumber gratis yang relevan)

SESI PRAKTEK (1 jam)
Tugas: (1 tugas coding konkret yang relevan dengan topik hari ini)

UPDATE INDUSTRI (15 menit)
Fokus: (topik atau keyword spesifik yang perlu dicari hari ini di berita AI/tech)

MOTIVASI HARI INI
(kutipan atau insight dari tokoh AI dunia yang relevan dengan perjalanan membangun perusahaan AI)

TARGET HARI INI
(1 target spesifik, terukur, dan realistis untuk dicapai hari ini)

---
Setiap hari adalah investasi untuk masa depan yang sedang kamu bangun.
"""
    return ask_groq(MORNING_SYSTEM, prompt)

def build_evening():
    topic = get_topic()
    today = datetime.now(WIB).strftime("%A, %d %B %Y")
    prompt = f"""
Hari ini: {today}
Topik yang seharusnya dipelajari: {topic}

Buat review malam dalam format berikut:

REVIEW HARIAN
Tanggal: {today}
---

CHECKLIST HARI INI
[ ] Belajar: {topic}
[ ] Sesi praktek coding
[ ] Update berita AI dan teknologi

PERTANYAAN REFLEKSI
1. (pertanyaan mendalam tentang progress belajar AI hari ini)
2. (pertanyaan tentang langkah nyata menuju pendirian perusahaan AI)

INSIGHT HARI INI
(satu pelajaran atau perspektif berharga tentang membangun karir di AI)

PERSIAPAN BESOK
Topik besok: (topik AI lanjutan yang bisa disiapkan malam ini)
Tindakan: (1 hal konkret yang bisa dilakukan malam ini untuk hari esok yang lebih produktif)

---
Konsistensi harian adalah fondasi dari pencapaian luar biasa.
"""
    return ask_groq(EVENING_SYSTEM, prompt)

@bot.event
async def on_ready():
    print(f"Reminder Bot online: {bot.user}")
    scheduler.start()

@bot.command(name="reminder")
async def manual_reminder(ctx):
    await ctx.send("Menyiapkan jadwal harian...")
    reminder = build_morning()
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    await channel.send(reminder)

@bot.command(name="malam")
async def manual_evening(ctx):
    await ctx.send("Menyiapkan review malam...")
    reminder = build_evening()
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    await channel.send(reminder)

@tasks.loop(minutes=1)
async def scheduler():
    now = datetime.now(WIB)
    if now.minute != 0:
        return
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    if not channel:
        return
    if now.hour == 7:
        print("Mengirim jadwal pagi...")
        await channel.send(build_morning())
    elif now.hour == 20:
        print("Mengirim review malam...")
        await channel.send(build_evening())

bot.run(DISCORD_TOKEN)