"""
BOT 2 — WORKER v2
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("WORKER_TOKEN")
WORKSPACE_CHANNEL_ID = int(os.getenv("WORKSPACE_CHANNEL_ID"))

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pipeline_state.json")

def save(key, value):
    try:
        state = json.load(open(STATE_FILE, encoding="utf-8")) if os.path.exists(STATE_FILE) else {}
    except:
        state = {}
    state[key] = value
    json.dump(state, open(STATE_FILE, "w", encoding="utf-8"), ensure_ascii=False)

def load(key):
    try:
        state = json.load(open(STATE_FILE, encoding="utf-8")) if os.path.exists(STATE_FILE) else {}
        return state.get(key, "")
    except:
        return ""

groq_client = Groq(api_key=GROQ_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!w", intents=intents)

SYSTEM_PROMPT = """
Kamu adalah Worker Agent — eksekutor handal dalam tim AI.
Kerjakan setiap task dengan sangat detail, terstruktur, dan actionable.

Standar kerjamu:
- Selalu jawab PERSIS sesuai brief, jangan melenceng
- Gunakan struktur yang jelas: judul, subjudul, bullet point
- Setiap poin harus konkret dan bisa langsung dieksekusi
- Sertakan contoh nyata jika relevan
- Jangan pakai filler atau kalimat kosong
- Tunjukkan expertise — bukan jawaban generik

Jika menerima revisi dari Critic:
- Baca semua feedback dengan seksama
- Perbaiki SETIAP poin yang dikritik
- Tambahkan bagian yang dibilang missing
- Tingkatkan bagian yang dibilang lemah

Gunakan Bahasa Indonesia profesional. Maksimal 600 kata.
"""

def ask_groq(prompt):
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=900,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"

async def send_result(channel, header, result, footer):
    """Kirim hasil — jika panjang, potong jadi beberapa pesan."""
    await channel.send(header)
    chunks = [result[i:i+1800] for i in range(0, len(result), 1800)]
    for i, chunk in enumerate(chunks):
        label = f"*(bagian {i+1}/{len(chunks)})*\n" if len(chunks) > 1 else ""
        await channel.send(f"{label}{chunk}")
    await channel.send(footer)

@bot.event
async def on_ready():
    print(f"Worker online: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)
    if message.channel.id != WORKSPACE_CHANNEL_ID:
        return
    content = message.content

    if "STATUS: MULAI_KERJA" in content and "WORKER silakan kerjakan" in content:
        await message.channel.send("⚙️ **[WORKER]** Siap! Mengerjakan task dengan sepenuh kemampuan...")
        brief = load("brief") or content
        result = ask_groq(f"Kerjakan task berikut dengan sangat detail:\n\n{brief}")
        save("worker_result", result)

        await send_result(
            message.channel,
            "📝 **[WORKER → CRITIC]** Hasil kerja pertama:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            result,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n**STATUS: MINTA_REVIEW**\nCRITIC silakan review dan berikan koreksi."
        )

    elif "STATUS: PERLU_REVISI" in content and "WORKER silakan revisi" in content:
        revision_count = load("revision_count") or "?"
        await message.channel.send(f"🔄 **[WORKER]** Menerima kritik dari Critic. Melakukan revisi ke-{revision_count}...")
        prev = load("worker_result")
        notes = load("critic_notes")
        result = ask_groq(
            f"Revisi hasil berikut berdasarkan kritik dari Critic:\n\n"
            f"HASIL SEBELUMNYA:\n{prev}\n\n"
            f"KRITIK DARI CRITIC:\n{notes}\n\n"
            f"Perbaiki SEMUA poin yang dikritik."
        )
        save("worker_result", result)

        await send_result(
            message.channel,
            "📝 **[WORKER → CRITIC]** Hasil setelah direvisi:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            result,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n**STATUS: MINTA_REVIEW**\nCRITIC silakan review kembali."
        )

bot.run(DISCORD_TOKEN)