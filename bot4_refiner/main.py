"""
BOT 4 — REFINER v2
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("REFINER_TOKEN")
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
bot = commands.Bot(command_prefix="!r", intents=intents)

SYSTEM_PROMPT = """
Kamu adalah Refiner Agent — editor dan polisher profesional dalam tim AI.
Tugasmu mengubah hasil yang sudah bagus menjadi LUAR BIASA.

Yang kamu lakukan:
- Sempurnakan struktur agar mengalir natural dan mudah dibaca
- Upgrade bahasa agar lebih profesional, persuasif, dan meyakinkan
- Tambahkan formatting Discord yang tepat (bold, italic, bullet)
- Hilangkan semua redundansi dan filler
- Tambahkan Executive Summary di awal jika belum ada
- Tambahkan Next Steps yang konkret di akhir
- Pastikan opening kalimat langsung menarik perhatian

Tujuan: hasil harus terasa seperti dibuat oleh konsultan profesional kelas dunia.
Gunakan Bahasa Indonesia yang excellent dan profesional.
Maksimal 700 kata. Fokus pada kualitas premium.
"""

def ask_groq(prompt):
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0.6, max_tokens=1000,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"

async def send_result(channel, header, content, footer):
    await channel.send(header)
    chunks = [content[i:i+1800] for i in range(0, len(content), 1800)]
    for i, chunk in enumerate(chunks):
        label = f"*(bagian {i+1}/{len(chunks)})*\n" if len(chunks) > 1 else ""
        await channel.send(f"{label}{chunk}")
    await channel.send(footer)

@bot.event
async def on_ready():
    print(f"Refiner online: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)
    if message.channel.id != WORKSPACE_CHANNEL_ID:
        return
    content = message.content

    if "STATUS: LANJUT_KE_REFINER" in content and "REFINER silakan poles" in content:
        await message.channel.send("✨ **[REFINER]** Hasil diterima! Memoles menjadi output premium...")
        approved = load("approved_result") or load("worker_result")

        if not approved:
            await message.channel.send("⚠️ **[REFINER]** Tidak ada hasil di state!")
            return

        refined = ask_groq(f"Poles dan jadikan output berikut jauh lebih premium:\n\n{approved}")
        save("refined_result", refined)

        await send_result(
            message.channel,
            "💎 **[REFINER → FACTCHECKER]** Hasil sudah dipoles:\n━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            refined,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n**STATUS: MINTA_FACTCHECK**\nFACTCHECKER silakan verifikasi keakuratan."
        )

bot.run(DISCORD_TOKEN)