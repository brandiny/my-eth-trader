import websocket, json, pprint, talib, numpy
import config                                   # Contains API keys
from binance.client import Client               # Primary Binance API calls
from binance.enums import *                     # Imports global constants used in binance

# Edit the MACD constants
MACD_FASTPERIOD = 12
MACD_SLOWPERIOD = 26
MACD_SIGNALPERIOD = 9


# Binance Client Object
# API Login keys are fetched from the config file
client = Client(config.API_KEY, config.API_SECRET)

klines = client.get_historical_klines("ETHEUR", Client.KLINE_INTERVAL_1MINUTE, "1 Feb, 2021 ")
highs = [float(k[2]) for k in klines]
lows = [float(k[3]) for k in klines]
closes = [float(k[4]) for k in klines]
#closes = [0.25 * (float(k[4]) + float(k[3]) + float(k[2]) + float(k[1])) for k in klines]

np_closes = numpy.array(closes)
np_highs = numpy.array(highs)
np_lows = numpy.array(lows)
rsi = talib.RSI(np_closes, timeperiod=5)


sar = talib.SAR(np_highs, np_lows, acceleration=0.02, maximum=0.2)
upperband, middleband, lowerband = talib.BBANDS(np_closes, timeperiod=17, nbdevup=2, nbdevdn=2, matype=0)
ema_10 = talib.EMA(np_closes, timeperiod=10)

macd, macdsignal, macdhist = talib.MACD(np_closes, fastperiod=MACD_FASTPERIOD, slowperiod=MACD_SLOWPERIOD, signalperiod=MACD_SIGNALPERIOD)
slowk, slowd = talib.STOCHF(np_highs, np_lows, np_closes, fastk_period=5, fastd_period=3)
sma = talib.SMA(np_closes, timeperiod=10)
IN_POSITION = False
COUNT_DOWN_TRADE = 0
COUNT_UP_TRADE = 0

CAPITAL_LAST = 100
CAPITAL_EUR = 100
CAPITAL_ETH = 0

STOP_LOSS = -1

LAST_MACD_BULL_CROSS = -1
LAST_STOCH_BULL_CROSS = -1
LAST_MACD_BEAR_CROSS = -1
LAST_STOCH_BEAR_CROSS = -1
LAST_RSI_BULL_CROSS = -1
LAST_RSI_BEAR_CROSS = -1
POSITION_TURNS = 0

print(closes[0], closes[-1], CAPITAL_EUR)
BUY_HOLD_PROFIT = (CAPITAL_EUR / closes[0]) * closes[-1]
for i in range(100, len(closes)):
    if macdhist[i] > 0:
        LAST_MACD_BULL_CROSS = 2
    if macdhist[i] < 0:
        LAST_MACD_BEAR_CROSS = 2

    if slowk[i] > slowd[i] and slowk[i-1] < slowd[i-1]:
        LAST_STOCH_BULL_CROSS = 2
    if slowk[i] < slowd[i] and slowk[i-1] > slowd[i-1]:
        LAST_STOCH_BEAR_CROSS = 2

    if rsi[i] > 50:
        LAST_RSI_BULL_CROSS = 2
    if rsi[i] < 50:
        LAST_RSI_BEAR_CROSS = 2

    buy_condition = (macd[i] - macdsignal[i] > 0) and (macd[i-1] < macdsignal[i-1])  and closes[i] > sma[i]
    sell_condition = (macdsignal[i] - macd[i] > 0) and (macd[i-1] > macdsignal[i-1]) and closes[i] < sma[i]

    # buy_condition = LAST_MACD_BULL_CROSS == 2
    # sell_condition = LAST_MACD_BEAR_CROSS == 2

    if IN_POSITION:
        POSITION_TURNS += 1

    if buy_condition:
        if not IN_POSITION:
            print('BUY eth price', closes[i], 'last capital', CAPITAL_LAST)
            CAPITAL_ETH = CAPITAL_EUR / closes[i]
            CAPITAL_EUR = 0
            IN_POSITION = True
    if sell_condition:
        if IN_POSITION and POSITION_TURNS > 10:
            POSITION_TURNS = 0
            print('SELL eth price', closes[i], 'last capital', CAPITAL_LAST)
            CAPITAL_EUR = CAPITAL_ETH * closes[i]
            CAPITAL_ETH = 0
            if CAPITAL_EUR > CAPITAL_LAST:
                COUNT_UP_TRADE += 1
            else:
                COUNT_DOWN_TRADE += 1
            CAPITAL_LAST = CAPITAL_EUR
            IN_POSITION = False

    LAST_MACD_BULL_CROSS -= 1
    LAST_STOCH_BULL_CROSS -= 1
    LAST_STOCH_BEAR_CROSS -= 1
    LAST_MACD_BEAR_CROSS -= 1
    LAST_RSI_BEAR_CROSS -= 1
    LAST_RSI_BULL_CROSS -= 1

print('Profit: ', COUNT_UP_TRADE)
print('Loss: ', COUNT_DOWN_TRADE)
print('Win rate: ', COUNT_UP_TRADE/(COUNT_DOWN_TRADE+COUNT_UP_TRADE))
print('Final trading capital:', CAPITAL_LAST)
print('Final buy hold capital:', BUY_HOLD_PROFIT)
print('Final trading growth:', str(CAPITAL_LAST/100)+'X')
print('Final buy hold growth:', str(BUY_HOLD_PROFIT/100)+'X')



