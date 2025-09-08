import os
import io
import asyncio
from datetime import datetime

from pycoingecko import CoinGeckoAPI
import matplotlib
matplotlib.use("Agg")  # ✅ Fix for headless Render servers
import matplotlib.pyplot as plt

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load Bot Token from environment (Render → Environment Variables)
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN not set — please add it in Render Environment Variables")

# API clients
cg = CoinGeckoAPI()

# ----------------- Helpers -----------------
async def find_coin_id(symbol: str) -> str | None:
    symbol = symbol.lower()
    coins = await asyncio.to_thread(cg.get_coins_list)
    for c in coins:
        if c.get("symbol", "").lower() == symbol:
            return c.get("id")
    return None

async def fetch_price_usd(coin_id: str) -> float | None:
    res = await asyncio.to_thread(cg.get_price, ids=coin_id, vs_currencies="usd")
    return res.get(coin_id, {}).get("usd")

async def fetch_market_chart(coin_id: str, days: int = 7):
    return await asyncio.to_thread(cg.get_coin_market_chart_by_id, coin_id, "usd", days)

def plot_prices_to_bytes(prices, symbol: str):
    times = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
    vals = [p[1] for p in prices]
    plt.figure(figsize=(8, 4))
    plt.plot(times, vals, color="blue")
    plt.title(f"{symbol.upper()} Price (USD)")
    plt.xlabel("Time")
    plt.ylabel("Price (USD)")
    plt.grid(True)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf

# ----------------- Handlers -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm PriceBot.\n\nCommands:\n"
        "/price <SYMBOL>  — Get price (e.g., /price BTC)\n"
        "/chart <SYMBOL> [days] — Price chart (default 7 days)"
    )

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /price <SYMBOL>\nExample: /price BTC")

    symbol = context.args[0]
    msg = await update.message.reply_text("Looking up coin id...")

    coin_id = await find_coin_id(symbol)
    if not coin_id:
        return await msg.edit_text(f"❌ Could not find coin with symbol '{symbol}'.")

    await msg.edit_text(f"Fetching price for {coin_id}...")
    price = await fetch_price_usd(coin
