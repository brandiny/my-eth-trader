import config
import csv
from binance.client import Client

client = Client(config.API_KEY, config.API_SECRET)

candles = client.get_klines(
    symbol='ETHEUR',
    interval=Client.KLINE_INTERVAL_1MINUTE
)

with open('data/1_minute_candlesticks.csv', 'w', newline='') as csvfile:
    candlestick_writer = csv.writer(csvfile, delimiter=',')
    for c in candles:
        candlestick_writer.writerow(c)

candles_historical_5minutes = client.get_historical_klines(
    'ETHEUR',
    Client.KLINE_INTERVAL_5MINUTE,
    "1 Jan, 2018"
)

with open('data/5_minute_candlesticks.csv', 'w', newline='') as csvfile:
    candlestick_writer = csv.writer(csvfile, delimiter=',')
    for c in candles_historical_5minutes:
        print(c)
        candlestick_writer.writerow(c)
