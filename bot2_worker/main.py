"""
BOT 2 - WORKER v3
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
Kamu adalah Worker Agent - eksekutor utama dalam tim AI profesional.
Kerjakan setiap task dengan sangat detail, terstruktur, dan actionable.

Standar kerja:
- Kerjakan PERSIS sesuai brief, tidak lebih tidak kurang
- Gunakan struktur yang jelas: judul, subjudul, poin-poin
- Setiap poin harus konkret dan bisa langsung dieksekusi
- Sertakan contoh nyata jika relevan
- Tidak ada filler atau kalimat kosong
- Tunjukkan keahlian, bukan jawaban generik
- Jika ada data analisis gambar dalam brief, gunakan sebagai referensi utama

Jika menerima revisi dari Critic:
- Baca semua feedback dengan seksama
- Perbaiki SETIAP poin yang dikritik tanpa terkecuali
- Tambahkan bagian yang dinyatakan kurang
- Tingkatkan kualitas bagian yang dinyatakan lemah
- Jangan hanya memodifikasi permukaan, perbaiki substansi

Gunakan Bahasa Indonesia yang profesional dan presisi.
Tidak ada emoji. Maksimal 700 kata.
"""

def ask_groq(prompt: str) -> str:
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, max_tokens=1000,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"

async def send_result(channel, header, result, footer):
    await channel.send(header)
    chunks = [result[i:i+1800] for i in range(0, len(result), 1800)]
    for i, chunk in enumerate(chunks):
        prefix = f"(bagian {i+1}/{len(chunks)})\n" if len(chunks) > 1 else ""
        await channel.send(f"{prefix}{chunk}")
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
        await message.channel.send("**[WORKER]** Brief diterima. Mengerjakan task...")
        brief = load("brief") or content
        image_analysis = load("image_analysis")

        prompt = f"Kerjakan task berikut dengan sangat detail:\n\n{brief}"
        if image_analysis:
            prompt += f"\n\nReferensi analisis gambar:\n{image_analysis}"

        result = ask_groq(prompt)
        save("worker_result", result)

        await send_result(
            message.channel,
            "**[WORKER -> CRITIC]** Hasil kerja pertama:\n---",
            result,
            "---\n**STATUS: MINTA_REVIEW**\nCRITIC silakan review dan berikan koreksi."
        )

    elif "STATUS: PERLU_REVISI" in content and "WORKER silakan revisi" in content:
        revision_count = load("revision_count") or "?"
        await message.channel.send(f"**[WORKER]** Menerima feedback Critic. Melakukan revisi ke-{revision_count}...")

        prev = load("worker_result")
        notes = load("critic_notes")
        brief = load("brief")
        image_analysis = load("image_analysis")

        prompt = (
            f"Revisi hasil berikut berdasarkan kritik dari Critic.\n\n"
            f"BRIEF ASAL:\n{brief}\n\n"
            f"HASIL SEBELUMNYA:\n{prev}\n\n"
            f"KRITIK DAN INSTRUKSI REVISI:\n{notes}\n\n"
            f"Perbaiki SETIAP poin yang dikritik. Jangan hanya mengubah permukaan."
        )
        if image_analysis:
            prompt += f"\n\nReferensi analisis gambar:\n{image_analysis}"

        result = ask_groq(prompt)
        save("worker_result", result)

        await send_result(
            message.channel,
            f"**[WORKER -> CRITIC]** Hasil revisi ke-{revision_count}:\n---",
            result,
            "---\n**STATUS: MINTA_REVIEW**\nCRITIC silakan review kembali."
        )

bot.run(DISCORD_TOKEN)