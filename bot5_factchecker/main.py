"""
BOT 5 — FACTCHECKER v2
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("FACTCHECKER_TOKEN")
WORKSPACE_CHANNEL_ID = int(os.getenv("WORKSPACE_CHANNEL_ID"))
RESULT_CHANNEL_ID = int(os.getenv("RESULT_CHANNEL_ID"))

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
bot = commands.Bot(command_prefix="!f", intents=intents)

SYSTEM_PROMPT = """
Kamu adalah FactChecker Agent — penjaga keakuratan dan konsistensi final dalam tim AI.
Ini adalah tahap TERAKHIR sebelum hasil dikirim ke user. Standarmu harus tinggi.

Yang kamu verifikasi:
1. Apakah semua argumen logis dan konsisten?
2. Apakah tidak ada kontradiksi internal?
3. Apakah saran/rekomendasi realistis dan bisa diimplementasikan?
4. Apakah tidak ada klaim berlebihan yang tidak berdasar?
5. Apakah hasil sudah menjawab task asal dengan tuntas?

Format responmu WAJIB:
🔬 **[FACTCHECKER REPORT]**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

**VERDICT: [FINAL_APPROVED/PERLU_PERBAIKAN]**

**Hasil Verifikasi:**
- Yang terverifikasi akurat: [poin-poin]
- Yang perlu diklarifikasi: [jika ada, atau tulis "Tidak ada"]

**Catatan untuk User:** [pesan singkat tentang kualitas hasil dan hal yang perlu diperhatikan]

Maksimal 250 kata. Jika hasil sudah logis dan menjawab task → langsung FINAL_APPROVED.
"""

def ask_groq(prompt):
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=400,
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
    print(f"FactChecker online: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)
    if message.channel.id != WORKSPACE_CHANNEL_ID:
        return
    content = message.content

    if "STATUS: MINTA_FACTCHECK" in content and "FACTCHECKER silakan verifikasi" in content:
        await message.channel.send("🔬 **[FACTCHECKER]** Melakukan verifikasi akhir sebelum dikirim ke user...")
        refined = load("refined_result")
        original_task = load("original_task")

        if not refined:
            await message.channel.send("⚠️ **[FACTCHECKER]** Tidak ada hasil di state!")
            return

        verdict = ask_groq(f"Task asal: {original_task}\n\nHasil yang perlu diverifikasi:\n{refined}")

        if "VERDICT: PERLU_PERBAIKAN" in verdict:
            save("factcheck_notes", verdict)
            await message.channel.send(verdict)
            await message.channel.send(
                "**STATUS: LANJUT_KE_REFINER**\n"
                "REFINER silakan perbaiki berdasarkan catatan FactChecker."
            )
        else:
            result_channel = bot.get_channel(RESULT_CHANNEL_ID)
            await message.channel.send(verdict)
            await message.channel.send("**STATUS: FINAL_APPROVED** — Mengirim ke #hasil...")

            await send_result(
                result_channel,
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "✅ **HASIL FINAL — DISETUJUI SEMUA AGENT**\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                refined,
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🤖 *Pipeline: Orchestrator → Worker ↔ Critic (debat) → Refiner → FactChecker*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )

bot.run(DISCORD_TOKEN)