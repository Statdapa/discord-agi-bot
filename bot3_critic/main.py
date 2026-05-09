"""
BOT 3 — CRITIC v2 (SANGAT KRITIS & GALAK)
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("CRITIC_TOKEN")
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
bot = commands.Bot(command_prefix="!c", intents=intents)

SYSTEM_PROMPT = """
Kamu adalah Critic Agent — reviewer paling kritis dan perfeksionis dalam tim AI.
Kamu adalah "devil's advocate" sejati. Standarmu SANGAT TINGGI.

Karaktermu:
- Tidak pernah puas dengan hasil yang biasa-biasa saja
- Selalu temukan minimal 3 kelemahan spesifik
- Feedback kamu keras tapi konstruktif
- Kamu berdebat berdasarkan logika dan fakta
- Jika hasil bagus, kamu akui — tapi tetap cari area perbaikan

Yang kamu periksa:
1. Apakah task dikerjakan PERSIS sesuai brief? Tidak kurang tidak lebih?
2. Apakah ada celah logika atau argumen lemah?
3. Apakah ada informasi penting yang HILANG?
4. Apakah cukup SPESIFIK atau masih terlalu generik?
5. Apakah benar-benar ACTIONABLE atau hanya teori kosong?
6. Apakah ada asumsi yang tidak berdasar?
7. Apakah bahasa dan struktur sudah optimal?

Format responmu WAJIB seperti ini:
🔍 **[CRITIC REPORT — REVISI KE-X]**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚖️ **VERDICT: [PERLU_REVISI/LANJUT_KE_REFINER]**

✅ **Yang Sudah Bagus:**
- [poin konkret 1]
- [poin konkret 2]

❌ **Kelemahan yang Ditemukan:**
1. **[nama kelemahan]**: [penjelasan detail mengapa ini masalah dan dampaknya]
2. **[nama kelemahan]**: [penjelasan detail mengapa ini masalah dan dampaknya]
3. **[nama kelemahan]**: [penjelasan detail mengapa ini masalah dan dampaknya]

🔧 **Instruksi Revisi untuk Worker:**
- [instruksi spesifik 1 — apa yang harus ditambah/diubah/dihapus]
- [instruksi spesifik 2]
- [instruksi spesifik 3]

💬 **Catatan Critic:** "[komentar jujur dan tegas tentang kualitas hasil secara keseluruhan]"

Maksimal 450 kata. Tegas, jujur, dan konstruktif.
"""

def ask_groq(prompt):
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0.65,
            max_tokens=700,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"

async def send_result(channel, content):
    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
    for chunk in chunks:
        await channel.send(chunk)

@bot.event
async def on_ready():
    print(f"Critic online: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)
    if message.channel.id != WORKSPACE_CHANNEL_ID:
        return
    content = message.content

    if "STATUS: MINTA_REVIEW" in content and "CRITIC silakan review" in content:
        revision_count = int(load("revision_count") or 0)
        await message.channel.send(
            f"🔍 **[CRITIC]** Memeriksa hasil revisi ke-{revision_count + 1}... "
            f"Tidak ada yang lolos tanpa review ketat dari saya!"
        )

        worker_result = load("worker_result")
        brief = load("brief")

        if not worker_result:
            save("approved_result", "")
            await message.channel.send(
                "🟢 **[CRITIC → REFINER]**\nTidak ada hasil baru di state.\n\n"
                "**STATUS: LANJUT_KE_REFINER**\nREFINER silakan poles hasil ini."
            )
            return

        review = ask_groq(
            f"Brief asal:\n{brief}\n\n"
            f"Revisi ke-{revision_count + 1}.\n"
            f"Hasil Worker:\n{worker_result}"
        )
        save("critic_notes", review)

        # Maksimal 2x revisi
        if "VERDICT: PERLU_REVISI" in review and revision_count < 2:
            save("revision_count", str(revision_count + 1))
            await send_result(message.channel, review)
            await message.channel.send(
                f"**STATUS: PERLU_REVISI**\n"
                f"WORKER silakan revisi! Ini revisi ke-{revision_count + 1} dari maksimal 2."
            )
        else:
            if revision_count >= 2:
                await message.channel.send(
                    "⚠️ **[CRITIC]** Sudah mencapai batas maksimal revisi (2x). "
                    "Melanjutkan ke Refiner dengan hasil terbaik yang ada."
                )
            save("approved_result", worker_result)
            await send_result(message.channel, review)
            await message.channel.send(
                "**STATUS: LANJUT_KE_REFINER**\n"
                "REFINER silakan poles dan sempurnakan hasil ini."
            )

bot.run(DISCORD_TOKEN)