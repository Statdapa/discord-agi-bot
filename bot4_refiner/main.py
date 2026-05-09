"""
BOT 4 - REFINER v3
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
Kamu adalah Refiner Agent - editor senior dan content strategist dalam tim AI.
Tugasmu mengubah hasil yang sudah diapprove Critic menjadi output berkualitas premium.

Yang kamu lakukan:
- Sempurnakan struktur agar mengalir natural, logis, dan mudah dipahami
- Tingkatkan bahasa agar lebih profesional, persuasif, dan berwibawa
- Optimalkan formatting untuk keterbacaan maksimal
- Eliminasi semua redundansi, filler, dan informasi tidak relevan
- Tambahkan Executive Summary yang kuat di bagian awal jika belum ada
- Pastikan setiap section memiliki transisi yang mulus
- Tambahkan rekomendasi Next Steps yang konkret dan terukur di akhir
- Pastikan kalimat pembuka langsung menarik perhatian dan relevan

Standar output: hasil harus terasa seperti laporan konsultan profesional kelas dunia.
Tidak ada emoji. Gunakan Bahasa Indonesia yang presisi dan berwibawa.
Maksimal 800 kata.
"""

def ask_groq(prompt: str) -> str:
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6, max_tokens=1100,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"

async def send_result(channel, header, content, footer):
    await channel.send(header)
    chunks = [content[i:i+1800] for i in range(0, len(content), 1800)]
    for i, chunk in enumerate(chunks):
        prefix = f"(bagian {i+1}/{len(chunks)})\n" if len(chunks) > 1 else ""
        await channel.send(f"{prefix}{chunk}")
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
        await message.channel.send("**[REFINER]** Hasil approved diterima. Memproses menjadi output premium...")
        approved = load("approved_result") or load("worker_result")

        if not approved:
            await message.channel.send("**[REFINER]** Tidak ada hasil yang tersimpan di state.")
            return

        refined = ask_groq(
            f"Poles dan tingkatkan kualitas output berikut menjadi standar profesional premium:\n\n{approved}"
        )
        save("refined_result", refined)

        await send_result(
            message.channel,
            "**[REFINER -> FACTCHECKER]** Hasil setelah proses refinement:\n---",
            refined,
            "---\n**STATUS: MINTA_FACTCHECK**\nFACTCHECKER silakan verifikasi keakuratan dan konsistensi."
        )

bot.run(DISCORD_TOKEN)