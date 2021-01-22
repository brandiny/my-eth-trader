import websocket, json, pprint, talib, numpy
import config  # Contains API keys
from binance.client import Client  # Primary binance API calls
from binance.enums import *  # Imports global constants used in binance

client = Client(config.API_KEY, config.API_SECRET)

closes = []
highs = []
lows = []
with open('logs.json', 'r') as f:
    data = json.load(f)
    closes = data['closes']
    highs = data['highs']
    lows = data['lows']
close = closes[-1]

def returnKELTNERS(closes, high, low, atr_period=20):
    sma = talib.SMA(closes, timeperiod=20)

    TR = []
    for i in range(len(high)):
        TR.append(abs(high[i] - low[i]))
    TR = numpy.array(TR)

    ATR = []
    for i in range(len(TR)):
        window = TR[i - atr_period:i]
        if len(window) == 0:
            ATR.append(None)
            continue
        else:
            atr_window = sum(window) / atr_period
            ATR.append(atr_window)
    ATR = numpy.array(ATR)

    upperKeltner = []
    lowerKeltner = []
    for i in range(len(ATR)):
        if ATR[i] is None:
            upperKeltner.append(None)
            lowerKeltner.append(None)
        else:
            upperKeltner.append(sma[i] + ATR[i] * 1.5)
            lowerKeltner.append(sma[i] - ATR[i] * 1.5)

    return numpy.array(upperKeltner), numpy.array(lowerKeltner)


def inSqueeze(bbands_upper, bbands_lower, keltner_upper, keltner_lower):
    squeeze = []
    for i in range(len(bbands_upper)):
        if bbands_upper[i] is None or bbands_lower[i] is None or \
                keltner_upper[i] is None or keltner_lower[i] is None:
            squeeze.append(False)
        else:
            squeeze.append(bbands_upper[i] < keltner_upper[i] and
                           bbands_lower[i] >
                           keltner_lower[i])

    return numpy.array(squeeze)


# Create the stop loss
STOP_LOSS = -1

# Edit the Relative Strength Index (RSI) constants
RSI_PERIOD = 13
RSI_OVERBOUGHT = 75
RSI_OVERSOLD = 25

# Edit the MACD constants
MACD_FASTPERIOD = 12
MACD_SLOWPERIOD = 26
MACD_SIGNALPERIOD = 9

# Edit the EMA constants
EMA_LONG_PERIOD = 21
EMA_SHORT_PERIOD = 8

# Change
TRADE_SYMBOL = 'ETHEUR'
BUY_QUANTITY = 0.014
SELL_QUANTITY = 0

"""BEGIN MAIN SHIT"""
np_closes = numpy.array(closes)
np_highs = numpy.array(highs)
np_lows = numpy.array(lows)

# Get RSI
rsi = talib.RSI(np_closes, RSI_PERIOD)
last_rsi = rsi[-1]

# Get MACD
macd, macdsignal, macdhist = talib.MACD(np_closes,
                                        fastperiod=MACD_FASTPERIOD,
                                        slowperiod=MACD_SLOWPERIOD,
                                        signalperiod=MACD_SIGNALPERIOD)
last_macd = macdsignal[-1]

# Calculate optimum BUY trade quantity
current_balance = float(
    [i for i in client.get_account()['balances'] if
     i['asset'] == 'EUR'][0]['free'])
optimum_buy = float(current_balance) / float(close)
BUY_QUANTITY = round(optimum_buy, 5) - 0.001

# Calculate optimum SELL trade quantity
current_balance2 = float(
    [i for i in client.get_account()['balances'] if
     i['asset'] == 'ETH'][0]['free'])
optimum_buy2 = float(current_balance2)
SELL_QUANTITY = round(optimum_buy2, 5)

# Calculate Exponential Moving averages
ema_long = talib.EMA(np_closes, timeperiod=EMA_LONG_PERIOD)
ema_short = talib.EMA(np_closes, timeperiod=EMA_SHORT_PERIOD)

print('RSI:  {}'.format(last_rsi))
print("MACD: {}".format(macdsignal[-1]))
print('rsi is overbought: ', last_rsi > RSI_OVERBOUGHT)
print('rsi is oversold: ', last_rsi < RSI_OVERSOLD)
print('buy quanitity: ', BUY_QUANTITY)
print('sell quanitity: ', SELL_QUANTITY)
print('stop loss: ', STOP_LOSS)
print('ema long: ', ema_long)
print('ema short: ', ema_short)
print('bull cross occurring: ', ((ema_short[-2] < ema_long[-2]) and (ema_short[-1] > ema_long[-1])))
print('bear cross occurring: ', ((ema_short[-2] > ema_long[-2]) and (ema_short[-1] < ema_long[-1])))