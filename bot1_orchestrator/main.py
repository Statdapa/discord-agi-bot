"""
BOT 1 — ORCHESTRATOR v2
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq import Groq

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

SYSTEM_PROMPT = """
Kamu adalah Orchestrator — pemimpin tim AI yang terdiri dari Worker, Critic, Refiner, dan FactChecker.
Analisis task dari user dan buat brief yang sangat jelas dan spesifik untuk Worker.

Format output WAJIB seperti ini:
[TASK_TYPE]: (riset/konten/coding/analisis/strategi/lainnya)
[GOAL]: (tujuan akhir yang ingin dicapai)
[BRIEF_FOR_WORKER]: (instruksi detail dan spesifik — apa yang HARUS ada dalam hasil)
[TARGET_AUDIENCE]: (untuk siapa hasil ini dibuat)
[SUCCESS_CRITERIA]: (kriteria kapan hasil dianggap sudah bagus)
[CONSTRAINTS]: (batasan atau hal yang harus dihindari)

Gunakan Bahasa Indonesia. Maksimal 250 kata. Sangat spesifik dan actionable.
"""

def ask_groq(prompt):
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=400,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"

@bot.event
async def on_ready():
    print(f"Orchestrator online: {bot.user}")

@bot.command(name="task")
async def start_task(ctx, *, task: str):
    await ctx.send(
        f"🎯 **[ORCHESTRATOR]** Task diterima!\n"
        f"> {task}\n\n"
        f"⏳ Menganalisis dan membuat brief untuk tim..."
    )
    clear()
    brief = ask_groq(f"Task dari user: {task}")
    save("brief", f"Task asli: {task}\n\n{brief}")
    save("original_task", task)
    save("revision_count", "0")

    workspace = bot.get_channel(WORKSPACE_CHANNEL_ID)
    await workspace.send(
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **[ORCHESTRATOR → WORKER]** Pipeline dimulai!\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"**Task:** {task}\n\n"
        f"{brief}\n\n"
        f"**STATUS: MULAI_KERJA**\n"
        f"WORKER silakan kerjakan sekarang."
    )
    await ctx.send("✅ Brief sudah dikirim ke tim! Pantau **#workspace** untuk melihat debat antar bot. Hasil final di **#hasil**.")

bot.run(DISCORD_TOKEN)