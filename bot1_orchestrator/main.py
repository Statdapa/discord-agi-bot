"""
BOT 1 - ORCHESTRATOR v3
Mendukung input teks dan gambar dari user.
"""
import os, sys, json, base64, re
sys.stdout.reconfigure(encoding='utf-8')
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq
import requests as req

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("ORCHESTRATOR_TOKEN")
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

def clear():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

groq_client = Groq(api_key=GROQ_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

BRIEF_SYSTEM = """
Kamu adalah Orchestrator - pemimpin tim AI profesional.
Analisis task dari user dan buat brief yang sangat jelas untuk Worker.

Format output WAJIB:
[TASK_TYPE]: (riset/konten/coding/analisis/strategi/desain/lainnya)
[GOAL]: (tujuan akhir yang ingin dicapai)
[BRIEF_FOR_WORKER]: (instruksi detail dan spesifik)
[TARGET_AUDIENCE]: (untuk siapa hasil ini dibuat)
[SUCCESS_CRITERIA]: (kriteria keberhasilan)
[CONSTRAINTS]: (batasan yang harus diperhatikan)

Gunakan Bahasa Indonesia. Maksimal 250 kata. Spesifik dan actionable.
"""

IMAGE_ANALYSIS_SYSTEM = """
Kamu adalah analis gambar profesional dalam tim AI.
Analisis gambar yang diberikan secara mendalam dan ekstrak semua informasi relevan
yang bisa dijadikan dasar untuk mengerjakan task.

Deskripsikan:
- Konten utama gambar
- Detail penting yang terlihat
- Konteks dan maksud gambar
- Informasi yang bisa digunakan untuk task

Gunakan Bahasa Indonesia yang profesional. Detail dan akurat.
"""

def analyze_image(image_url: str, task_text: str) -> str:
    """Analisis gambar menggunakan Groq vision model."""
    try:
        # Download gambar dan convert ke base64
        response = req.get(image_url, timeout=15)
        image_data = base64.b64encode(response.content).decode('utf-8')

        # Deteksi format gambar
        content_type = response.headers.get('content-type', 'image/jpeg')
        if 'png' in content_type:
            media_type = 'image/png'
        elif 'gif' in content_type:
            media_type = 'image/gif'
        elif 'webp' in content_type:
            media_type = 'image/webp'
        else:
            media_type = 'image/jpeg'

        res = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Analisis gambar ini dalam konteks task berikut: {task_text}\n\n{IMAGE_ANALYSIS_SYSTEM}"
                        }
                    ]
                }
            ],
            max_tokens=800,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Gagal menganalisis gambar: {e}"

def ask_groq(prompt: str) -> str:
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": BRIEF_SYSTEM},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, max_tokens=400,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"

@bot.event
async def on_ready():
    print(f"Orchestrator online: {bot.user}")

@bot.command(name="task")
async def start_task(ctx, *, task: str = ""):
    """
    Terima task dari user.
    Bisa disertai gambar dengan cara upload gambar + ketik !task [deskripsi]
    """
    # Cek apakah ada attachment gambar
    image_analysis = ""
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                await ctx.send(f"Gambar terdeteksi. Menganalisis gambar...")
                image_analysis = analyze_image(attachment.url, task or "Analisis gambar ini secara menyeluruh")
                await ctx.send(f"Analisis gambar selesai. Memproses task...")
                break

    if not task and not image_analysis:
        await ctx.send("Mohon sertakan deskripsi task. Contoh: `!task buatkan strategi marketing`\nAtau upload gambar bersamaan dengan command.")
        return

    # Gabungkan task teks + analisis gambar
    full_task = task
    if image_analysis:
        full_task = f"{task}\n\n[ANALISIS GAMBAR]:\n{image_analysis}" if task else f"[ANALISIS GAMBAR]:\n{image_analysis}"

    await ctx.send(
        f"**[ORCHESTRATOR]** Task diterima.\n"
        f"> {task if task else 'Input berupa gambar'}\n\n"
        f"Menganalisis dan membuat brief untuk tim..."
    )

    clear()
    save("revision_count", "0")
    save("original_task", task or "Analisis berdasarkan gambar")
    if image_analysis:
        save("image_analysis", image_analysis)

    brief = ask_groq(f"Task dari user:\n{full_task}")
    save("brief", f"Task asli: {full_task}\n\n{brief}")

    workspace = bot.get_channel(WORKSPACE_CHANNEL_ID)
    await workspace.send(
        f"---\n"
        f"**[ORCHESTRATOR -> WORKER]** Pipeline dimulai.\n"
        f"---\n"
        f"**Task:** {task if task else 'Berdasarkan gambar yang diupload'}\n\n"
        f"{brief}\n\n"
        f"{'**Catatan:** Ada analisis gambar tersimpan di state untuk referensi.' if image_analysis else ''}\n\n"
        f"**STATUS: MULAI_KERJA**\n"
        f"WORKER silakan kerjakan sekarang."
    )
    await ctx.send("Brief sudah dikirim ke tim. Pantau **#workspace** untuk melihat proses. Hasil final di **#hasil**.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    await bot.process_commands(message)

bot.run(DISCORD_TOKEN)