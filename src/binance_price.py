import ccxt
def main():
    binance = ccxt.binance()
    ticker = binance.fetch_ticker('BTC/USDT')
    print("symbol:",ticker['symbol'])
    print("Last Price:", ticker['last'])
    print("Bid:", ticker['last'])
    print("High:", ticker['bid'], "Ask:", ticker['ask'])
if __name__ == "__main__":
    main()

