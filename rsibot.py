import websocket, json, pprint, talib, numpy
import config  # Contains API keys
from binance.client import Client  # Primary binance API calls
from binance.enums import *  # Imports global constants used in binance

# Edit the Relative Strength Index (RSI) constants
RSI_PERIOD = 14
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

closes = [1148.63, 1147.95, 1152.98, 1156.2, 1157.45, 1155.93, 1154.15, 1154.71, 1160.42, 1158.68, 1158.01, 1157.76, 1156.61, 1160.0, 1158.61, 1156.24, 1156.13, 1153.13, 1149.08, 1152.6, 1153.15, 1156.01, 1154.0, 1154.56, 1156.66, 1157.37, 1159.52, 1157.82, 1155.23, 1158.91, 1159.6, 1162.29, 1157.74, 1158.59, 1158.96, 1160.2, 1159.59, 1159.82, 1158.16, 1160.04, 1160.78, 1158.77, 1157.47, 1158.31, 1158.66, 1159.47, 1161.59, 1156.38, 1158.67, 1161.42, 1160.31, 1161.8, 1160.36, 1159.42, 1157.79, 1156.67, 1154.84, 1154.96, 1154.38, 1155.32, 1154.84, 1154.99, 1154.16, 1152.36, 1149.73, 1149.54, 1150.15, 1148.26, 1146.47, 1148.34, 1148.89, 1148.97, 1148.69, 1150.74, 1151.71, 1149.69, 1147.59, 1145.77, 1145.21, 1143.65, 1146.24, 1146.63, 1148.0, 1148.91, 1147.18, 1144.51, 1144.16, 1140.63, 1140.43, 1141.39, 1142.23, 1143.88, 1143.25, 1144.74, 1145.44, 1148.02, 1151.88, 1153.45, 1153.52, 1154.55, 1154.01, 1152.22, 1151.73, 1149.28, 1148.21, 1146.0, 1144.19, 1140.33, 1138.9, 1137.0, 1134.51, 1133.41, 1136.29, 1136.49, 1135.55, 1137.3, 1137.12, 1134.45, 1134.57, 1135.94, 1136.85, 1139.43, 1139.25, 1137.56, 1136.53, 1135.15, 1139.89, 1139.82, 1138.1, 1140.35, 1140.04, 1140.51, 1141.29, 1141.79, 1141.88, 1141.93, 1142.53, 1142.06, 1143.12, 1143.97, 1145.42, 1146.81, 1148.87, 1148.1, 1147.77, 1149.49, 1150.18, 1149.15, 1149.45, 1150.39, 1149.41, 1151.27, 1148.62, 1149.99, 1147.27, 1146.96, 1148.32, 1146.74, 1149.69, 1149.78, 1149.95, 1151.09, 1151.27, 1152.0, 1151.7, 1153.62, 1154.39, 1153.76, 1153.51, 1154.41, 1156.72, 1156.65, 1155.95, 1155.23, 1153.69, 1153.64, 1153.45, 1152.84, 1146.55, 1147.09, 1146.05, 1147.95, 1149.07, 1149.2, 1146.95, 1148.62, 1148.5, 1148.83, 1147.65, 1144.35, 1142.83, 1142.4, 1146.17, 1147.01, 1146.1, 1143.3, 1141.75, 1144.22, 1142.51, 1139.34, 1136.76, 1132.99, 1135.24, 1130.0, 1125.0, 1126.04, 1127.9, 1122.69, 1120.64, 1127.39, 1128.54, 1124.39, 1120.95, 1124.91, 1123.08, 1128.24]
in_position = True  # In position = holding currency
# macd_upwards = False        # MACD indicates upwards momentum
# macd_downwards = False      # MACD indicates downwards momentum

client = Client(config.API_KEY, config.API_SECRET)


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
    global in_position
    global client
    global BUY_QUANTITY
    global SELL_QUANTITY
    json_message = json.loads(message)

    candle = json_message['k']

    is_candle_closed = candle['x']
    close = candle['c']

    dump_data = {}

    if is_candle_closed:
        print("Candle closed at {}".format(close))
        closes.append(float(close))
        dump_data['closes'] = closes[:]

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

            # Get SMA
            # fast_sma = talib.SMA(np_closes, timeperiod=7)
            # print("SMA (7): ", fast_sma)

            print('rsi is overbought: ', last_rsi > RSI_OVERBOUGHT)
            print('rsi is oversold: ', last_rsi < RSI_OVERSOLD)
            print('in position: ', in_position)
            print('buy quanitity: ', BUY_QUANTITY)
            print('sell quanitity: ', SELL_QUANTITY)

            if (last_rsi > RSI_OVERBOUGHT):
                if in_position:
                    print("Overbought! Sell!, sell!, sell!")
                    order_succeeded = order(SIDE_SELL, SELL_QUANTITY,
                                            TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("It is overbought. We don't own any. Nothing to do.")

            if (last_rsi < RSI_OVERSOLD):
                if in_position:
                    print(
                        "It is oversold, but you already own it and there is nothing to do")
                else:
                    print("Oversold! Buy!, buy!, buy!")
                    order_succeeded = order(SIDE_BUY, BUY_QUANTITY,
                                            TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True
        print()
        with open('logs.json', 'w') as f:
            json.dump(dump_data, f)


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close,
                            on_message=on_message)
ws.run_forever()