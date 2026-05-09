"""
BOT 7 - MARKET BTC v3
Laporan BTC profesional tanpa emoji.
Mendukung analisis chart/gambar yang diupload user.
"""
import os, sys, base64
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
Kamu adalah analis Bitcoin dan cryptocurrency senior yang berpengalaman.
Berikan analisis yang tajam, objektif, dan berbasis data.
Gunakan Bahasa Indonesia yang profesional dan presisi.
Tidak ada emoji. Selalu ingatkan bahwa ini bukan financial advice.
Maksimal 200 kata untuk analisis.
"""

CHART_ANALYSIS_SYSTEM = """
Kamu adalah analis teknikal cryptocurrency senior.
Analisis chart atau gambar yang diberikan secara mendalam.

Identifikasi dan jelaskan:
- Pola teknikal yang terlihat (support, resistance, trend)
- Indikator teknikal jika terlihat (RSI, MACD, MA, dll)
- Kondisi pasar saat ini berdasarkan chart
- Potensi pergerakan harga ke depan
- Level kritis yang perlu diperhatikan

Gunakan Bahasa Indonesia profesional. Tidak ada emoji.
Selalu tambahkan disclaimer bahwa ini bukan financial advice.
"""

def get_btc():
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin"
        res = requests.get(url, params={
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        }, timeout=10)
        d = res.json()["market_data"]
        return {
            "price": d["current_price"]["usd"],
            "change_1h": d["price_change_percentage_1h_in_currency"]["usd"],
            "change_24h": d["price_change_percentage_24h"],
            "change_7d": d["price_change_percentage_7d"],
            "high_24h": d["high_24h"]["usd"],
            "low_24h": d["low_24h"]["usd"],
            "market_cap": d["market_cap"]["usd"],
        }
    except Exception as e:
        return {"error": str(e)}

def format_change(val):
    if val is None:
        return "N/A"
    direction = "+" if val > 0 else ""
    return f"{direction}{val:.2f}%"

def market_condition(change_24h):
    if change_24h > 3:
        return "Bullish"
    elif change_24h < -3:
        return "Bearish"
    return "Sideways / Konsolidasi"

def ask_groq(prompt, system=None):
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system or MARKET_SYSTEM},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6, max_tokens=300,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"ERROR analisis: {e}"

def analyze_chart(image_url: str, context: str = "") -> str:
    """Analisis chart/gambar menggunakan Groq vision."""
    try:
        response = requests.get(image_url, timeout=15)
        image_data = base64.b64encode(response.content).decode('utf-8')
        content_type = response.headers.get('content-type', 'image/jpeg')
        if 'png' in content_type:
            media_type = 'image/png'
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
                            "image_url": {"url": f"data:{media_type};base64,{image_data}"}
                        },
                        {
                            "type": "text",
                            "text": f"{CHART_ANALYSIS_SYSTEM}\n\n{context if context else 'Analisis chart ini secara menyeluruh.'}"
                        }
                    ]
                }
            ],
            max_tokens=600,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"Gagal menganalisis chart: {e}"

def build_report(time_label="sekarang"):
    data = get_btc()
    if "error" in data:
        return f"Gagal mengambil data BTC: {data['error']}"

    condition = market_condition(data["change_24h"])
    analysis = ask_groq(
        f"Data BTC:\n"
        f"Harga: ${data['price']:,.0f}\n"
        f"Perubahan 1h: {format_change(data['change_1h'])}\n"
        f"Perubahan 24h: {format_change(data['change_24h'])}\n"
        f"Perubahan 7d: {format_change(data['change_7d'])}\n"
        f"High 24h: ${data['high_24h']:,.0f}\n"
        f"Low 24h: ${data['low_24h']:,.0f}\n"
        f"Kondisi: {condition}\n\n"
        f"Berikan:\n"
        f"Analisis: (2-3 kalimat analisis kondisi market saat ini)\n"
        f"Saran: (Hold/Pantau/Waspada beserta alasan singkat 1 kalimat)"
    )

    label = time_label.upper()
    return (
        f"LAPORAN BTC {label}\n"
        f"---\n"
        f"Harga Saat Ini  : ${data['price']:,.0f}\n"
        f"Perubahan 1 Jam : {format_change(data['change_1h'])}\n"
        f"Perubahan 24 Jam: {format_change(data['change_24h'])}\n"
        f"Perubahan 7 Hari: {format_change(data['change_7d'])}\n"
        f"High 24 Jam     : ${data['high_24h']:,.0f}\n"
        f"Low 24 Jam      : ${data['low_24h']:,.0f}\n"
        f"Kondisi Pasar   : {condition}\n"
        f"---\n"
        f"{analysis}\n"
        f"---\n"
        f"Disclaimer: Laporan ini bukan financial advice. Lakukan riset mandiri sebelum mengambil keputusan investasi."
    )

@bot.event
async def on_ready():
    print(f"Market Bot online: {bot.user}")
    scheduler.start()

@bot.command(name="btc")
async def btc_command(ctx):
    """Laporan BTC real-time. Bisa sertakan gambar chart untuk analisis teknikal."""
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                await ctx.send("Chart terdeteksi. Menganalisis secara teknikal...")
                analysis = analyze_chart(attachment.url, "Analisis chart Bitcoin ini secara teknikal.")
                await ctx.send(
                    f"ANALISIS TEKNIKAL CHART\n"
                    f"---\n"
                    f"{analysis}\n"
                    f"---\n"
                    f"Disclaimer: Bukan financial advice. Lakukan riset mandiri."
                )
                return

    await ctx.send("Mengambil data BTC terbaru...")
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