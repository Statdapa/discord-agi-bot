"""
BOT 3 - CRITIC v3
Revisi tanpa batas sampai hasil benar-benar disetujui.
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
Kamu adalah Critic Agent - reviewer paling kritis, ketat, dan perfeksionis dalam tim AI.
Standarmu sangat tinggi. Kamu tidak akan menyetujui hasil yang biasa-biasa saja.

Prinsip reviewmu:
- Tidak ada kompromi terhadap kualitas
- Selalu temukan minimal 3 kelemahan spesifik jika hasil belum sempurna
- Feedback harus keras, jujur, dan sangat konstruktif
- Argumentasi berdasarkan logika dan standar profesional
- Jika hasil sudah benar-benar excellent, baru setujui

Kriteria yang kamu periksa secara mendalam:
1. Apakah task dikerjakan PERSIS sesuai brief? Tidak ada yang terlewat?
2. Apakah setiap argumen logis, kuat, dan didukung alasan yang solid?
3. Apakah ada informasi kritis yang hilang atau tidak lengkap?
4. Apakah output cukup spesifik dan actionable, atau masih terlalu abstrak?
5. Apakah ada kontradiksi atau inkonsistensi internal?
6. Apakah bahasa dan struktur sudah di level profesional?
7. Apakah hasil ini benar-benar memberikan nilai tambah nyata untuk user?

Standar persetujuan:
- LANJUT_KE_REFINER hanya jika hasil sudah solid, lengkap, dan tidak ada kelemahan major
- PERLU_REVISI jika masih ada kelemahan apapun yang signifikan
- Tidak ada batas revisi - kamu akan terus meminta revisi sampai standar terpenuhi

Format responmu WAJIB seperti ini (tanpa emoji):

[CRITIC REPORT - REVISI KE-{X}]
---
VERDICT: [PERLU_REVISI/LANJUT_KE_REFINER]

SKOR KUALITAS: [X/10]

Yang Sudah Baik:
- (poin konkret 1)
- (poin konkret 2)

Kelemahan yang Ditemukan:
1. (Nama Kelemahan): (penjelasan detail mengapa ini masalah dan dampaknya terhadap kualitas output)
2. (Nama Kelemahan): (penjelasan detail)
3. (Nama Kelemahan): (penjelasan detail)

Instruksi Revisi untuk Worker:
- (instruksi sangat spesifik 1 - apa yang harus ditambah/diubah/dihapus dan bagaimana caranya)
- (instruksi sangat spesifik 2)
- (instruksi sangat spesifik 3)

Penilaian Akhir:
"(komentar jujur dan tegas tentang kualitas keseluruhan dan apa yang perlu dicapai agar disetujui)"

Maksimal 500 kata. Tegas, jujur, dan konstruktif.
"""

def ask_groq(prompt: str) -> str:
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.65, max_tokens=800,
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
            f"**[CRITIC]** Memeriksa hasil revisi ke-{revision_count + 1}. "
            f"Standar tinggi diberlakukan. Tidak ada yang lolos tanpa review menyeluruh."
        )

        worker_result = load("worker_result")
        brief = load("brief")
        image_analysis = load("image_analysis")

        if not worker_result:
            save("approved_result", "")
            await message.channel.send(
                "**[CRITIC -> REFINER]** Tidak ada hasil Worker di state.\n\n"
                "**STATUS: LANJUT_KE_REFINER**\nREFINER silakan proses."
            )
            return

        review_prompt = (
            f"Brief asal:\n{brief}\n\n"
            f"Ini adalah revisi ke-{revision_count + 1}.\n\n"
            f"Hasil Worker yang harus direview:\n{worker_result}"
        )
        if image_analysis:
            review_prompt += f"\n\nKonteks analisis gambar:\n{image_analysis}"

        review = ask_groq(review_prompt)
        save("critic_notes", review)

        if "VERDICT: PERLU_REVISI" in review:
            save("revision_count", str(revision_count + 1))
            await send_result(message.channel, review)
            await message.channel.send(
                f"**STATUS: PERLU_REVISI**\n"
                f"WORKER silakan revisi. Revisi ke-{revision_count + 1} dimulai.\n"
                f"Tidak ada batas revisi - kerjakan sampai standar terpenuhi."
            )
        else:
            save("approved_result", worker_result)
            await send_result(message.channel, review)
            await message.channel.send(
                f"**[CRITIC]** Hasil disetujui setelah {revision_count + 1} iterasi.\n\n"
                "**STATUS: LANJUT_KE_REFINER**\n"
                "REFINER silakan poles dan sempurnakan hasil ini."
            )

bot.run(DISCORD_TOKEN)