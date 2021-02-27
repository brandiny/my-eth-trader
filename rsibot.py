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
BUY_QUANTITY = 0.01
SELL_QUANTITY = 0

# Binance Websocket References are @
# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md
SOCKET = "wss://stream.binance.com:9443/ws/{}@kline_1m".format(
    TRADE_SYMBOL.lower())

closes = []
highs = []
lows = []

in_position = False            # In position = holding currency
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
        if ATR[i] is None or ATR[i] == "NaN":
            upperKeltner.append(None)
            lowerKeltner.append(None)
        else:
            upperKeltner.append(sma[i] + ATR[i]*1.5)
            lowerKeltner.append(sma[i] + ATR[i]-1.5)

    return numpy.array(upperKeltner), numpy.array(lowerKeltner)


def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        # Place order
        order_type_string = "BUY" if side == SIDE_BUY else "SELL"
        print("Sending {} order of {}{} ...".format(str(order_type_string),
                                                    str(symbol), str(quantity)))
        order = client.create_order(symbol=symbol, side=side, type=order_type,
                                    quantity=round(quantity, 5))
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
        '''
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

        order_succeeded = order(SIDE_BUY, BUY_QUANTITY, TRADE_SYMBOL)

        order_succeeded = order(SIDE_SELL, SELL_QUANTITY, TRADE_SYMBOL)
        '''


        # If there is enough data to begin drawing conclusions (minimum 27)
        if len(closes) > RSI_PERIOD and len(closes) > MACD_SLOWPERIOD + 1:
            np_closes = numpy.array(closes)

            rsi = talib.RSI(np_closes, RSI_PERIOD)
            dump_data['rsi'] = list(rsi[:])
            last_rsi = rsi[-1]
            print('RSI:  {}'.format(last_rsi))

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
            SELL_QUANTITY = round(optimum_buy2, 5)

            # Get bollingers
            upperBand, middleBand, lowerBand = talib.BBANDS(np_closes,
                                                            timeperiod=30)
            upperBand = float(upperBand[-1])
            middleBand = float(middleBand[-1])
            lowerBand = float(lowerBand[-1])
        
            # SMA =
            sma = talib.SMA(np_closes, timeperiod=10)
            
            print('UPPERBAND: ', upperBand,'LOWERBAND: ', lowerBand)
            print('rsi is overbought: ', last_rsi > RSI_OVERBOUGHT)
            print('rsi is oversold: ', last_rsi < RSI_OVERSOLD)
            print('in position: ', in_position)
            print('buy quanitity: ', BUY_QUANTITY)
            print('sell quanitity: ', SELL_QUANTITY)
            print(close > upperBand, close < lowerBand)

            buy_condition = (macd[-1] - macdsignal[-1] > 0) and (macd[-2] < macdsignal[-2]) and closes[-1] > sma[-1]
            sell_condition = (macdsignal[-1] - macd[-1] > 0) and (macd[-2] > macdsignal[-2]) and closes[-1] < sma[-1]
            
            if (sell_condition):
                if in_position:
                    print("Overbought! Sell!, sell!, sell!")
                    order_succeeded = order(SIDE_SELL, SELL_QUANTITY,
                                            TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("It is overbought. We don't own any. Nothing to do.")

            if buy_condition:
                if in_position:
                    print("It is oversold, but you already own it and there is nothing to do")
                else:
                    print("Oversold! Buy!, buy!, buy!")
                    order_succeeded = order(SIDE_BUY, BUY_QUANTITY,
                                            TRADE_SYMBOL)

                    # 10 less than buying price
                    STOP_LOSS = close - 10

                    if order_succeeded:
                        in_position = True
        print()
        with open('logs.json', 'w') as f:
            json.dump(dump_data, f)


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close,
                            on_message=on_message)
ws.run_forever()