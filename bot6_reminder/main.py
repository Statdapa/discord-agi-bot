"""
BOT 6 — REMINDER & JADWAL HARIAN
Otomatis kirim reminder pagi 07.00 WIB dan malam 20.00 WIB
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
    "Deep Learning dengan PyTorch: buat model pertama",
    "Natural Language Processing: tokenisasi dan word embedding",
    "Transformer Architecture: cara kerja attention mechanism",
    "Fine-tuning LLM dengan dataset sendiri",
    "Multi-agent System: cara agent AI berkomunikasi",
    "Reinforcement Learning: reward, policy, dan Q-learning",
    "AI Alignment: mengapa AI yang aman itu penting",
    "Prompt Engineering: teknik terbaik berinteraksi dengan LLM",
    "Membangun REST API AI dengan FastAPI",
    "Vector Database dan RAG System: Pinecone & Chroma",
    "Computer Vision: CNN dan object detection",
    "Membangun startup AI: dari ide ke produk",
]

MORNING_SYSTEM = """
Kamu adalah mentor AI yang semangat dan supportif untuk anak muda 19-22 tahun
yang bermimpi membangun perusahaan AI sendiri.

Buat reminder pagi yang energetik, personal, dan memotivasi.
Gunakan Bahasa Indonesia yang natural dan penuh semangat.
Gunakan emoji yang pas. Format harus rapi dan mudah dibaca di Discord.
"""

EVENING_SYSTEM = """
Kamu adalah mentor AI yang bijak dan suportif untuk anak muda 19-22 tahun
yang bermimpi membangun perusahaan AI.

Buat reminder malam yang reflektif, tenang, dan memotivasi.
Gunakan Bahasa Indonesia yang hangat. Gunakan emoji yang pas.
"""

def get_topic():
    return LEARNING_TOPICS[datetime.now(WIB).timetuple().tm_yday % len(LEARNING_TOPICS)]

def ask_groq(system, prompt):
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
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

Buat reminder pagi dalam format ini:

🌅 **SELAMAT PAGI, FUTURE AI FOUNDER!** ✨
📅 {today}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 **BELAJAR HARI INI** (1-2 jam)
→ Topik: **{topic}**
→ [1 tip spesifik cara belajar topik ini]
→ Resource: [saran resource gratis untuk belajar topik ini]

💻 **PRAKTEK** (1 jam)
→ [1 tugas coding konkret yang relevan dengan topik hari ini]

🌐 **UPDATE DUNIA AI** (15 menit)
→ [saran topik/keyword untuk dicari di Google/X hari ini]

💪 **MOTIVASI HARI INI**
→ [kutipan dari tokoh AI dunia atau original, yang relevan dengan perjalanan membangun company AI]

🎯 **TARGET HARI INI:**
→ [1 target spesifik dan terukur]

Semangat terus! Setiap hari adalah investasi untuk masa depanmu! 🚀
"""
    return ask_groq(MORNING_SYSTEM, prompt)

def build_evening():
    topic = get_topic()
    today = datetime.now(WIB).strftime("%A, %d %B %Y")
    prompt = f"""
Hari ini: {today}
Topik yang seharusnya dipelajari: {topic}

Buat reminder malam dalam format ini:

🌙 **REVIEW MALAM** — Saatnya evaluasi diri!
📅 {today}
━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ **Checklist Hari Ini:**
□ Belajar: {topic}
□ Praktek coding
□ Update berita AI/tech
□ Minum air yang cukup

💭 **Refleksi Malam:**
→ [pertanyaan refleksi yang mendalam tentang progress hari ini]
→ [pertanyaan tentang langkah menuju mimpi company AI]

📈 **Insight Hari Ini:**
→ [satu insight atau pelajaran hidup tentang membangun startup AI]

🔋 **Persiapan Besok:**
→ Topik besok: [topik AI yang bisa disiapkan malam ini]
→ [1 hal konkret yang bisa disiapkan malam ini]
→ Tidur yang cukup ya! Otak yang istirahat = belajar lebih efektif

Konsistensi kecil setiap hari mengalahkan sprint besar sesekali! 💫
"""
    return ask_groq(EVENING_SYSTEM, prompt)

@bot.event
async def on_ready():
    print(f"Reminder Bot online: {bot.user}")
    scheduler.start()

@bot.command(name="reminder")
async def manual_reminder(ctx):
    """Ketik !reminder untuk dapat reminder pagi sekarang."""
    await ctx.send("📋 Menyiapkan reminder untukmu...")
    reminder = build_morning()
    channel = bot.get_channel(REMINDER_CHANNEL_ID)
    await channel.send(reminder)

@bot.command(name="malam")
async def manual_evening(ctx):
    """Ketik !malam untuk dapat review malam sekarang."""
    await ctx.send("🌙 Menyiapkan review malam...")
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
        print(f"Channel {REMINDER_CHANNEL_ID} tidak ditemukan!")
        return

    if now.hour == 7:
        print("Mengirim reminder pagi...")
        msg = build_morning()
        await channel.send(msg)

    elif now.hour == 20:
        print("Mengirim reminder malam...")
        msg = build_evening()
        await channel.send(msg)

bot.run(DISCORD_TOKEN)