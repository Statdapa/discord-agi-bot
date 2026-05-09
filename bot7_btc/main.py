"""
BOT 7 — MARKET BTC
Laporan otomatis BTC setiap 07.00 & 20.00 WIB
Command: !btc untuk laporan sekarang
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import discord
import requests
from discord.ext import commands, tasks
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime
import pytz

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("MARKET_BOT_TOKEN")
MARKET_CHANNEL_ID = int(os.getenv("MARKET_CHANNEL_ID"))
WIB = pytz.timezone("Asia/Jakarta")

groq_client = Groq(api_key=GROQ_API_KEY)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MARKET_SYSTEM = """
Kamu adalah analis Bitcoin berpengalaman.
Berikan analisis singkat, jelas, dan tajam berdasarkan data real-time.
Gunakan Bahasa Indonesia yang natural. Gunakan emoji untuk Discord.
Selalu ingatkan bahwa ini bukan financial advice.
Maksimal 150 kata untuk analisis.
"""

def get_btc():
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin"
        res = requests.get(url, params={"localization": "false", "tickers": "false",
                                         "community_data": "false", "developer_data": "false"}, timeout=10)
        d = res.json()["market_data"]
        return {
            "price": d["current_price"]["usd"],
            "change_1h": d["price_change_percentage_1h_in_currency"]["usd"],
            "change_24h": d["price_change_percentage_24h"],
            "change_7d": d["price_change_percentage_7d"],
            "high_24h": d["high_24h"]["usd"],
            "low_24h": d["low_24h"]["usd"],
        }
    except Exception as e:
        return {"error": str(e)}

def arrow(val):
    if val is None: return "N/A"
    return f"{'🔺' if val > 0 else '🔻'} {abs(val):.2f}%"

def market_condition(change_24h):
    if change_24h > 3: return "🟢 Bullish"
    elif change_24h < -3: return "🔴 Bearish"
    return "🟡 Sideways"

def ask_groq(prompt):
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": MARKET_SYSTEM}, {"role": "user", "content": prompt}],
            temperature=0.6, max_tokens=250,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR analisis: {e}"

def build_report(time_label="pagi"):
    data = get_btc()
    if "error" in data:
        return f"⚠️ Gagal ambil data BTC: {data['error']}"

    emoji = "🌅" if time_label == "pagi" else "🌙"
    condition = market_condition(data["change_24h"])

    analysis = ask_groq(
        f"Data BTC sekarang:\n"
        f"Harga: ${data['price']:,.0f}\n"
        f"Perubahan 1h: {data['change_1h']:.2f}%\n"
        f"Perubahan 24h: {data['change_24h']:.2f}%\n"
        f"Perubahan 7d: {data['change_7d']:.2f}%\n"
        f"High 24h: ${data['high_24h']:,.0f}\n"
        f"Low 24h: ${data['low_24h']:,.0f}\n"
        f"Kondisi: {condition}\n\n"
        f"Berikan:\n"
        f"🧠 Analisis: [2-3 kalimat analisis kondisi market]\n"
        f"💡 Saran: [Hold/Pantau/Waspada + alasan singkat 1 kalimat]"
    )

    return (
        f"{emoji} **LAPORAN BTC {time_label.upper()}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Harga: **${data['price']:,.0f}**\n"
        f"📈 Perubahan:\n"
        f"  • 1 Jam  : {arrow(data['change_1h'])}\n"
        f"  • 24 Jam : {arrow(data['change_24h'])}\n"
        f"  • 7 Hari : {arrow(data['change_7d'])}\n"
        f"🔺 High 24h: ${data['high_24h']:,.0f}\n"
        f"🔻 Low 24h : ${data['low_24h']:,.0f}\n"
        f"📊 Kondisi : {condition}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{analysis}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Bukan financial advice. DYOR!*"
    )

@bot.event
async def on_ready():
    print(f"Market Bot online: {bot.user}")
    scheduler.start()

@bot.command(name="btc")
async def btc_command(ctx):
    await ctx.send("⏳ Mengambil data BTC terbaru...")
    report = build_report("sekarang")
    await ctx.send(report)

@tasks.loop(minutes=1)
async def scheduler():
    now = datetime.now(WIB)
    if now.minute != 0:
        return
    channel = bot.get_channel(MARKET_CHANNEL_ID)
    if not channel:
        return
    if now.hour == 7:
        await channel.send(build_report("pagi"))
    elif now.hour == 20:
        await channel.send(build_report("malam"))

bot.run(DISCORD_TOKEN)