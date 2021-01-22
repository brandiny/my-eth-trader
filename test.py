import websocket, json, pprint, talib, numpy
import config  # Contains API keys
from binance.client import Client  # Primary binance API calls
from binance.enums import *  # Imports global constants used in binance

client = Client(config.API_KEY, config.API_SECRET)
with open('logs.json', 'r') as f:
    data = json.load(f)
    print(data['closes'])
    print(data['highs'])
    print(data['lows'])