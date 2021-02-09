import websocket, json, pprint, talib, numpy
import config                                   # Contains API keys
from binance.client import Client               # Primary Binance API calls
from binance.enums import *                     # Imports global constants used in binance


# Web Socket ignores exceptions by default - this setting raises them
websocket._logging._logger.level = -99

# This prevents being whipsawed
POSITION_TURNS = 0

# This variable holds the Stop Loss price - initially, there is no stop loss
# The stop loss is automatically calculated upon entering a position
STOP_LOSS = -1

# Edit the Relative Strength Index (RSI) constants
RSI_PERIOD = 14
RSI_OVERBOUGHT = 75
RSI_OVERSOLD = 25

# Edit the EMA constants
EMA_LONG_PERIOD = 13
EMA_SHORT_PERIOD = 8

# Edit the MACD constants
MACD_FASTPERIOD = 12
MACD_SLOWPERIOD = 26
MACD_SIGNALPERIOD = 9

# Asset information
# Buy and sell quantities are automatically calculated from account balances
TRADE_SYMBOL = 'ETHEUR'
BUY_QUANTITY = 0
SELL_QUANTITY = 0

# Binance Web Socket Object
# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md
SOCKET = "wss://stream.binance.com:9443/ws/{}@kline_1m".format(TRADE_SYMBOL.lower())

# Financial information storage
# Closes        = closing candlestick price
# Highs         = upper wick of candlestick
# Lows          = closing wick of candlestick
# is_squeeze    = is the price movement in a Bollinger-Keltners squeeze
# in_position   = are we holding majority asset (automatically calculated)
closes = []
highs = []
lows = []
in_position = False

# Binance Client Object
# API Login keys are fetched from the config file
client = Client(config.API_KEY, config.API_SECRET)

# Trackers
LAST_MACD_BULL_CROSS = -1
LAST_STOCH_BULL_CROSS = -1
LAST_MACD_BEAR_CROSS = -1
LAST_STOCH_BEAR_CROSS = -1
LAST_RSI_BULL_CROSS = -1
LAST_RSI_BEAR_CROSS = -1

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    """
    This function places a spot order in the Binance market place
    side        : SIDE_SELL=sell, SIDE_BUY=buy
    quantity    : how much to buy
    symbol      : what currency are you buying
    order_type  : which market place are you trading on.... market, margin, futures

    Returns True if successful. False if order fails. Exceptions are logged.
    """
    try:
        # Ensure the quantity is cleaned and error checked
        quantity = round(float(quantity), 5)

        # Log the order as it is being sent
        order_type_string = "BUY" if side == SIDE_BUY else "SELL"
        print("Sending {} order of {}{} ...".format(str(order_type_string), str(symbol), str(quantity)))
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print("{} ORDER SUCCESSFUL".format(str(order_type_string)))
    except Exception as e:
        # If order fails, print the execeptions and return False
        print("An exception occured - {}".format(e))
        print("{} ORDER FAILED".format(str(order_type_string)))
        return False

    return True


def on_open(ws):
    print('Opened connection...')


def on_close(ws):
    print('Closed connection...')


def on_message(ws, message):
    # Access financial data
    global closes
    global highs
    global lows

    # Access important trackers
    global in_position
    global client
    global BUY_QUANTITY
    global SELL_QUANTITY
    global STOP_LOSS
    global EMA_SHORT_PERIOD
    global EMA_LONG_PERIOD
    global MACD_FASTPERIOD
    global MACD_SLOWPERIOD
    global MACD_SIGNALPERIOD
    global POSITION_TURNS
    global LAST_STOCH_BEAR_CROSS
    global LAST_MACD_BEAR_CROSS
    global LAST_STOCH_BULL_CROSS
    global LAST_MACD_BULL_CROSS

    # Load in the json packet received from the web socket
    json_message = json.loads(message)
    candle = json_message['k']
    is_candle_closed = candle['x']
    close = float(candle['c'])
    low = float(candle['l'])
    high = float(candle['h'])

    # This stores all of the financial data
    # It is logged to a json data in case of an outage
    dump_data = {}

    if is_candle_closed:
        print("Candle closed at {}.".format(close))

        # Store financial data
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))
        dump_data['closes'] = closes[:]
        dump_data['highs'] = highs[:]
        dump_data['lows'] = lows[:]
        # If there is enough data to begin drawing conclusions
        if len(closes) > 27:
            # Cast the financial data to numpy arrays for efficiency
            np_closes = numpy.array(closes)
            np_highs = numpy.array(highs)
            np_lows = numpy.array(lows)

            # Calculate RSI (Relative Strength Index)
            # RSI is a leading momentum indicator
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            dump_data['rsi'] = list(rsi[:])
            print('RSI:  {}'.format(rsi[-1]))

            # Calculate optimum BUY trade quantity
            #       Find the EUR balance and divide it by the CLOSING PRICE
            #       - 0.001 to prevent any rounding preventing overbuy
            current_balance = float([i for i in client.get_account()['balances'] if i['asset'] == 'EUR'][0]['free'])
            optimum_buy = 0.15 * (float(current_balance) / float(close))
            BUY_QUANTITY = round(optimum_buy, 5) - 0.001

            # Calculate optimum SELL trade quantity
            #       Find the ETH balance and subtract 0.001 to prevent oversell
            current_balance = float([i for i in client.get_account()['balances'] if i['asset'] == 'ETH'][0]['free'])
            optimum_buy = float(current_balance)
            SELL_QUANTITY = round(optimum_buy, 5) - 0.001

            # Calculate the trade position
            #       ETH majority: in position
            #       EUR majority: not in position
            if SELL_QUANTITY > BUY_QUANTITY:
                in_position = True
            elif BUY_QUANTITY > SELL_QUANTITY:
                in_position = False

            # Calculate 10 SMA
            sma_10 = talib.SMA(np_closes, timeperiod=10)
            
            # Calculate MACD
            macd, macdsignal, macdhist = talib.MACD(np_closes, fastperiod=MACD_FASTPERIOD, slowperiod=MACD_SLOWPERIOD, signalperiod=MACD_SIGNALPERIOD)
            dump_data['macd'] = list(macd[:])

            # Stochastic
            slowk, slowd = talib.STOCHF(np_highs, np_lows, np_closes, fastk_period=5, fastd_period=3)

            # Trailing stop loss
            '''
            if closes[-1] > closes[-2]:
                STOP_LOSS = close - 5
            
            # If in position
            
            '''
            if in_position:
                POSITION_TURNS += 1

            # LOG INFORMATION FOR LIVE DEBUG
            print('In position: ', in_position)
            print('Buy quanitity: ', BUY_QUANTITY)
            print('Sell quanitity: ', SELL_QUANTITY)
            print('Stop loss: ', STOP_LOSS)
            print('SMA: ', sma_10[-1])
            print('MACD: ', macd[-1])
            print('MACD signal: ', macdsignal[-1])
            print("Position Turns: ", POSITION_TURNS)
            print('Stoch K', slowk)
            print('Stoch D', slowd)
            print("LMBULL", LAST_MACD_BULL_CROSS)
            print("LMBEAR", LAST_MACD_BEAR_CROSS)
            print("LSBULL", LAST_STOCH_BULL_CROSS)
            print("LSBEAR", LAST_STOCH_BEAR_CROSS)

            if macdhist[-1] > 0:
                LAST_MACD_BULL_CROSS = 2
            if macdhist[-1] < 0:
                LAST_MACD_BEAR_CROSS = 2

            if slowk[-1] > slowd[-1] and slowk[-2] < slowd[-2]:
                LAST_STOCH_BULL_CROSS = 2
            if slowk[-1] < slowd[-1] and slowk[-2] > slowd[-2]:
                LAST_STOCH_BEAR_CROSS = 2

            buy_condition = LAST_STOCH_BULL_CROSS >= 0 and LAST_MACD_BULL_CROSS >= 0 and \
                            closes[-1] > sma_10[-1]
            sell_condition = LAST_STOCH_BEAR_CROSS >= 0 and LAST_MACD_BEAR_CROSS >= 0 and \
                             closes[-1] < sma_10[-1]

            # SELL CONDITION
            # For this strategy:
            #       - sell if in position and the momentum is turning
            #       - or if the trade price dips below the stop loss
            if sell_condition:
                if not in_position:
                    print('SELL SIGNAL. We have nothing to sell however. Nothing is done.')
                elif POSITION_TURNS < 5:
                    print("We cannot exit a position in less than 17 time frames, to prevent whipsaws.")
                else:
                    print("SELL SIGNAL. Exiting position")
                    order_succeeded = order(SIDE_SELL, SELL_QUANTITY, TRADE_SYMBOL)

                    if order_succeeded:
                        in_position = False
                        POSITION_TURNS = 0

            # BUY CONDITION
            # For this strategy:
            #       - has upwards momentum
            if buy_condition:
                if in_position:
                    print("BUY SIGNAL. Already holding currency, so nothing is done.")
                else:
                    print("BUY SIGNAL. Bullish momentum.")
                    order_succeeded = order(SIDE_BUY, BUY_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True
                        STOP_LOSS = closes - closes*0.01
                        POSITION_TURNS = 0

        # Change trackers
        LAST_MACD_BULL_CROSS -= 1
        LAST_STOCH_BULL_CROSS -= 1
        LAST_STOCH_BEAR_CROSS -= 1
        LAST_MACD_BEAR_CROSS -= 1

        # Log information to the logs.json file
        print()
        with open('logs.json', 'w') as f:
            json.dump(dump_data, f)

# Run the websocket until terminated.
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()
