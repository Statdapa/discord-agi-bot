"""
BOT 5 - FACTCHECKER v3
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
Kamu adalah FactChecker Agent - validator akhir dalam tim AI profesional.
Ini adalah gate terakhir sebelum output dikirim ke user. Standarmu sangat tinggi.

Yang kamu verifikasi secara menyeluruh:
1. Konsistensi logika - apakah semua argumen saling mendukung dan tidak bertentangan?
2. Kelengkapan - apakah task asal sudah dijawab secara tuntas?
3. Realisme - apakah rekomendasi dan saran benar-benar bisa diimplementasikan?
4. Akurasi klaim - apakah tidak ada pernyataan yang berlebihan atau tidak berdasar?
5. Koherensi - apakah alur dan struktur output sudah optimal?
6. Nilai tambah - apakah output ini benar-benar memberikan manfaat nyata?

Format responmu WAJIB (tanpa emoji):

[FACTCHECKER REPORT]
---
VERDICT: [FINAL_APPROVED/PERLU_PERBAIKAN]

Hasil Verifikasi:
- Terverifikasi: (poin-poin yang akurat dan solid)
- Perlu klarifikasi: (jika ada, atau tulis: Tidak ada catatan tambahan)

Tingkat Kepercayaan: [Tinggi/Sedang/Rendah]

Catatan untuk User:
(pesan profesional tentang kualitas output dan hal yang perlu diperhatikan saat implementasi)

Maksimal 300 kata. Jika output sudah solid, logis, dan menjawab task dengan tuntas, langsung FINAL_APPROVED.
"""

def ask_groq(prompt: str) -> str:
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, max_tokens=500,
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
        await message.channel.send("**[FACTCHECKER]** Melakukan verifikasi akhir sebelum output dikirim ke user...")
        refined = load("refined_result")
        original_task = load("original_task")

        if not refined:
            await message.channel.send("**[FACTCHECKER]** Tidak ada hasil yang tersimpan di state.")
            return

        verdict = ask_groq(
            f"Task asal dari user:\n{original_task}\n\n"
            f"Output final yang perlu diverifikasi:\n{refined}"
        )

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
            await message.channel.send("**STATUS: FINAL_APPROVED** - Mengirim output ke #hasil...")

            await send_result(
                result_channel,
                "---\n**OUTPUT FINAL - DISETUJUI SEMUA AGENT**\n---",
                refined,
                "---\n"
                f"Task: {original_task}\n"
                "Pipeline: Orchestrator -> Worker -> Critic -> Refiner -> FactChecker\n"
                "---"
            )

bot.run(DISCORD_TOKEN)