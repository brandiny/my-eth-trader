import websocket, json, pprint, talib, numpy
import config  # Contains API keys
from binance.client import Client  # Primary binance API calls
from binance.enums import *  # Imports global constants used in binance

client = Client(config.API_KEY, config.API_SECRET)
close = 1148
current_balance = float(
                [i for i in client.get_account()['balances'] if
                 i['asset'] == 'ETH'][0]['free'])
optimum_buy = float(current_balance) / float(close)
SELL_QUANTITY = round(optimum_buy, 5) - 0.0001
print(current_balance)
print(optimum_buy)
print(SELL_QUANTITY)