import websocket, json, pprint, talib, numpy
import config  # Contains API keys
from binance.client import Client  # Primary binance API calls
from binance.enums import *  # Imports global constants used in binance

# Edit the Relative Strength Index (RSI) constants
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Edit the MACD constants
MACD_FASTPERIOD = 12
MACD_SLOWPERIOD = 26
MACD_SIGNALPERIOD = 9

# Change
TRADE_SYMBOL = 'ETHEUR'
TRADE_QUANTITY = 0.014

# Binance Websocket References are @
# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md
SOCKET = "wss://stream.binance.com:9443/ws/{}@kline_5m".format(
    TRADE_SYMBOL.lower())

closes = []
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
    global TRADE_QUANTITY
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

            # Calculate optimum trade quantity
            current_balance = float(
                [i for i in client.get_account()['balances'] if
                 i['asset'] == 'EUR'][0]['free'])
            optimum_buy = float(current_balance) / float(close)
            TRADE_QUANTITY = round(optimum_buy, 5) - 0.001

            # Detect upwards trends
            '''
            if macdsignal[-1] < 0 and macdsignal[-2] > 0:
                print('Bear market crossing from {} to {}'.format(str(macdsignal[-2]), str(macdsignal[-1])))
                macd_upwards = False
                macd_downwards = True


            if macdsignal[-1] > 0 and macdsignal[-2] < 0:
                print('Bull market crossing from {} to {}'.format(str(macdsignal[-2]), str(macdsignal[-1])))
                macd_upwards = True
                macd_downwards = False
            '''

            print('rsi is overbought: ', last_rsi > RSI_OVERBOUGHT)
            print('rsi is oversold: ', last_rsi < RSI_OVERSOLD)
            print('in position: ', in_position)
            print('trade quanitity: ', TRADE_QUANTITY)

            if (last_rsi > RSI_OVERBOUGHT + 5) or (
                    last_rsi > RSI_OVERBOUGHT and macdsignal > 4):
                if in_position:
                    print("Overbought! Sell!, sell!, sell!")
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY,
                                            TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("It is overbought. We don't own any. Nothing to do.")

            if (last_rsi < RSI_OVERSOLD - 5) or (
                    last_rsi < RSI_OVERSOLD and macdsignal < -4):
                if in_position:
                    print(
                        "It is oversold, but you already own it and there is nothing to do")
                else:
                    print("Oversold! Buy!, buy!, buy!")
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY,
                                            TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True
        print()
        with open('logs.json', 'w') as f:
            json.dump(dump_data, f)


# order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
# print(order_succeeded)
# in_position = True
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close,
                            on_message=on_message)
ws.run_forever()