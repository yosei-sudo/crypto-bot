import os
from decimal import Decimal
from dotenv import load_dotenv
from loguru import logger
import httpx
import ccxt

load_dotenv()

SYMBOL = os.getenv("SYMBOL", "BTC/USDT")
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

def fetch_last(exchange, symbol: str) -> Decimal:
    t = exchange.fetch_ticker(symbol)
    # 取引所によっては 'last' が None になることがあるので保険で bid/ask から近似
    last = t.get("last")
    if last is None:
        bid, ask = t.get("bid"), t.get("ask")
        if bid is not None and ask is not None:
            last = (Decimal(str(bid)) + Decimal(str(ask))) / 2
    return Decimal(str(last))

def send_discord(msg: str):
    if DRY_RUN or not WEBHOOK:
        logger.info(f"[DRY_RUN] {msg}")
        return
    try:
        r = httpx.post(WEBHOOK, json={"content": msg}, timeout=10)
        r.raise_for_status()
        logger.info("Sent to Discord")
    except Exception as e:
        logger.error(f"Discord notify failed: {e}")

def main():
    binance = ccxt.binance({"enableRateLimit": True})
    bybit   = ccxt.bybit({"enableRateLimit": True})
    try:
        # 対応マーケットをロード（SYMBOLが存在するか早めにチェック）
        binance.load_markets()
        bybit.load_markets()
        assert SYMBOL in binance.markets, f"Binance does not support {SYMBOL}"
        assert SYMBOL in bybit.markets,   f"Bybit does not support {SYMBOL}"

        b_last = fetch_last(binance, SYMBOL)
        y_last = fetch_last(bybit, SYMBOL)

        diff_abs = (b_last - y_last).copy_abs()
        base     = (b_last + y_last) / Decimal("2")
        diff_pct = (diff_abs / base) * Decimal("100")

        msg = (
            f"{SYMBOL}\n"
            f"Binance: {b_last}\n"
            f"Bybit  : {y_last}\n"
            f"Δ = {diff_abs} ({diff_pct.quantize(Decimal('0.0001'))}%)"
        )
        logger.info(msg)
        send_discord("**Spread Snapshot**\n" + msg)

    finally:
        # ccxtの同期版は close 不要だが将来拡張に備え try/finally を残す
        pass

if __name__ == "__main__":
    main()
