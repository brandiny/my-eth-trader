import websocket, json, pprint, talib, numpy
import config  # Contains API keys
from binance.client import Client  # Primary binance API calls
from binance.enums import *  # Imports global constants used in binance

websocket._logging._logger.level = -99

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

# Change
TRADE_SYMBOL = 'ETHEUR'
BUY_QUANTITY = 0.014
SELL_QUANTITY = 0

# Binance Websocket References are @
# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md
SOCKET = "wss://stream.binance.com:9443/ws/{}@kline_1m".format(
    TRADE_SYMBOL.lower())

closes = [931.58, 933.28, 927.07, 930.59, 936.1, 935.21, 939.29, 937.21, 935.88, 932.4, 935.42, 938.73, 944.56, 953.18, 949.21, 949.39, 945.0, 946.63, 946.0, 946.83, 941.79, 942.33, 940.21, 932.0, 927.31, 927.09, 933.78, 932.69,
940.53, 944.37, 939.47, 936.99, 938.65, 933.73, 932.54, 935.27, 936.98, 936.27, 936.0, 935.07, 934.9, 939.38,
939.07, 941.15, 938.39, 936.25, 936.22, 933.19, 940.53, 942.77, 942.93, 945.47, 944.0, 941.47, 939.1, 939.05,
938.0, 935.87, 938.3, 937.96]
highs = [933.1, 934.87, 934.4, 932.64, 936.1, 936.8, 939.3, 939.82, 937.64, 936.2, 935.78, 939.68, 944.56, 955.35, 953.47, 952.64, 949.03, 949.99, 947.97, 947.89, 947.87, 946.47, 943.58, 940.01, 932.0, 930.81, 935.65, 935.31, 941.3, 944.53, 945.27, 941.19, 942.48, 939.34, 935.7, 939.19, 939.59, 937.28, 939.0, 937.72, 935.59, 940.76, 939.71, 941.49, 940.84, 937.78, 937.92, 936.34, 942.35, 943.0, 944.65, 947.35, 946.87, 944.18, 941.79, 942.09, 941.67, 938.3, 940.76, 941.66]
lows = [928.71, 930.32, 926.75, 926.66, 930.39, 932.68, 935.21, 935.9, 933.48, 932.0, 932.55, 934.9, 939.06, 944.46,
948.24, 947.66, 945.0, 945.0, 945.88, 946.0, 941.79, 941.76, 939.9, 930.0, 926.04, 926.6, 926.47, 930.75, 931.94, 940.54, 939.36, 935.6, 936.9, 933.47, 931.71, 932.12, 934.86, 934.65, 935.3, 933.36, 932.27, 934.4, 936.47, 938.83, 937.45, 935.1, 935.19, 932.8, 933.32, 939.46, 940.78, 942.64, 944.0, 941.17, 938.75, 938.68, 938.0,
935.72, 935.4, 937.96]
is_squeeze = []

in_position = False  # In position = holding currency
# macd_upwards = False        # MACD indicates upwards momentum
# macd_downwards = False      # MACD indicates downwards momentum


client = Client(config.API_KEY, config.API_SECRET)


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

'''
uB, mB, lB = talib.BBANDS(numpy.array(closes), timeperiod=20)
lKC, uKC = returnKELTNERS(numpy.array(closes), numpy.array(highs),
                          numpy.array(lows))

test = inSqueeze(uB, lB, lKC, uKC)
'''


def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        # Place order
        order_type_string = "BUY" if side == SIDE_BUY else "SELL"
        print("Sending {} order of {}{} ...".format(str(order_type_string),
                                                    str(symbol), str(quantity)))
        order = client.create_order(symbol=symbol, side=side, type=order_type,
                                    quantity=quantity)
        print("{} ORDER SUCCESSFUL".format(str(order_type_string)))
    except Exception as e:
        # In the case the order fails.
        print("An exception occured - {}".format(e))
        print("{} ORDER FAILED".format(str(order_type_string)))
        return False

    return True


def on_open(ws):
    print('Opened connection...')


def on_close(ws):
    print('Closed connection...')


def on_message(ws, message):
    global closes
    global highs
    global lows
    global is_squeeze

    global in_position
    global client
    global BUY_QUANTITY
    global SELL_QUANTITY
    global STOP_LOSS

    json_message = json.loads(message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = float(candle['c'])
    high = float(candle['h'])
    low = float(candle['l'])

    dump_data = {}

    if is_candle_closed:
        print("Candle closed at {}. High is at {}. Low is at {}".format(
            close, high, low))
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))

        dump_data['closes'] = closes[:]
        dump_data['highs'] = highs[:]
        dump_data['lows'] = lows[:]

        # If there is enough data to begin drawing conclusions (minimum 27)
        if len(closes) > 20:
            np_closes = numpy.array(closes)
            np_highs = numpy.array(highs)
            np_lows = numpy.array(lows)

            # Get RSI
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            dump_data['rsi'] = list(rsi[:])
            last_rsi = rsi[-1]
            print('RSI:  {}'.format(last_rsi))

            # Get MACD
            macd, macdsignal, macdhist = talib.MACD(np_closes,
                                                    fastperiod=MACD_FASTPERIOD,
                                                    slowperiod=MACD_SLOWPERIOD,
                                                    signalperiod=MACD_SIGNALPERIOD)

            dump_data['macd'] = list(macd[:])
            last_macd = macdsignal[-1]
            print("MACD: {}".format(macdsignal[-1]))


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
            SELL_QUANTITY = round(optimum_buy2, 5) - 0.001

            if SELL_QUANTITY > BUY_QUANTITY:
                in_position = True
            elif BUY_QUANTITY > SELL_QUANTITY:
                in_position = False

            # Get bollingers
            upperBandList, middleBandList, lowerBandList = talib.BBANDS(np_closes, timeperiod=20)

            upperBand = float(upperBandList[-1])
            middleBand = float(middleBandList[-1])
            lowerBand = float(lowerBandList[-1])


            # Get Keltners
            upperKCList, lowerKCList = returnKELTNERS(np_closes, np_highs, np_lows)
            upperKC = upperKCList[-1]
            lowerKC = lowerKCList[-1]

            # Do the squeeze
            is_squeeze = inSqueeze(upperBandList, lowerBandList, upperKCList,lowerKCList)

            # Get Momentum
            momentum = talib.MOM(np_closes)

            print("UPPERKC: ", upperKC, "LOWERKC: ", lowerKC)
            print('UPPERBAND: ', upperBand, 'LOWERBAND: ', lowerBand)
            print('SQUEEZE: ', is_squeeze[-1])
            print("MOMENTUM: ", momentum[-1])
            print('rsi is overbought: ', last_rsi > RSI_OVERBOUGHT)
            print('rsi is oversold: ', last_rsi < RSI_OVERSOLD)
            print('in position: ', in_position)
            print('buy quanitity: ', BUY_QUANTITY)
            print('sell quanitity: ', SELL_QUANTITY)
            print('stop loss: ', STOP_LOSS)
            print('exiting squeeze? ', (is_squeeze[-1] == False) and (True in is_squeeze[-6:-3]))
            print('upwards momentum? ', (momentum[-1] > 0))
            # If exiting a squeeze
            if (momentum[-1] < 0 and in_position) or (close < STOP_LOSS):
                print("Overbought! Sell!, sell!, sell!")
                order_succeeded = order(SIDE_SELL, SELL_QUANTITY,
                                        TRADE_SYMBOL)
                if order_succeeded:
                    in_position = False

            if (is_squeeze[-1] == False) and (True in is_squeeze[-6:-3]) and (momentum[-1] > 0):
                if in_position:
                    print("BUY condition, but we are already in position. Holding")
                else:
                    print("Exiting squeeze with upwards momentum. Buy! Buy!")
                    order_succeeded = order(SIDE_BUY, BUY_QUANTITY,
                                            TRADE_SYMBOL)

                    # set a stop loss 10 less than buying price
                    STOP_LOSS = close - 10

                    if order_succeeded:
                        in_position = True

        print()
        with open('logs.json', 'w') as f:
            json.dump(dump_data, f)


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close,
                            on_message=on_message)
ws.run_forever()