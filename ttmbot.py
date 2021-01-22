import websocket, json, pprint, talib, numpy
import config                                   # Contains API keys
from binance.client import Client               # Primary Binance API calls
from binance.enums import *                     # Imports global constants used in binance


# Web Socket ignores exceptions by default - this setting raises them
websocket._logging._logger.level = -99

# This variable holds the Stop Loss price - initially, there is no stop loss
# The stop loss is automatically calculated upon entering a position
STOP_LOSS = -1

# Edit the Relative Strength Index (RSI) constants
RSI_PERIOD = 13
RSI_OVERBOUGHT = 75
RSI_OVERSOLD = 25

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
is_squeeze = []
in_position = False

# Binance Client Object
# API Login keys are fetched from the config file
client = Client(config.API_KEY, config.API_SECRET)


def returnKELTNERS(closes, high, low, atr_period=20):
    """
    Input:          closing price list, high price list, low price list
    Optional Input: atr_period = period over which to calculate the keltners
    Output:         upper and lower keltner channels as numpy_arrays
    """
    # Simple moving average = middle keltner channel
    sma = talib.SMA(closes, timeperiod=atr_period)

    # True Range of the highs/lows of the candlesticks
    TR = []
    for i in range(len(high)):
        TR.append(abs(high[i] - low[i]))
    TR = numpy.array(TR)

    # Average True Range of the True Ranges, calculated in a windowed average
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

    # Calculating the upper and lower Keltner channels using the formula
    # middle_channel +- average_true_range * multiplier
    KC_multiplier = 1.5
    upperKeltner = []
    lowerKeltner = []
    for i in range(len(ATR)):
        if ATR[i] is None:
            upperKeltner.append(None)
            lowerKeltner.append(None)
        else:
            upperKeltner.append(sma[i] + ATR[i] * KC_multiplier)
            lowerKeltner.append(sma[i] - ATR[i] * KC_multiplier)

    return numpy.array(upperKeltner), numpy.array(lowerKeltner)


def inSqueeze(bbands_upper, bbands_lower, keltner_upper, keltner_lower):
    """
    Input:   Bollinger Bands (upper and lower), Keltner Channels (upper and lower)
    Output:  List of booleans where True if BBands within KChannels else False
    """
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
    global is_squeeze

    # Access important trackers
    global in_position
    global client
    global BUY_QUANTITY
    global SELL_QUANTITY
    global STOP_LOSS

    # Load in the json packet received from the web socket
    json_message = json.loads(message)
    candle = json_message['k']
    is_candle_closed = candle['x']
    close = float(candle['c'])
    high = float(candle['h'])
    low = float(candle['l'])

    # This stores all of the financial data
    # It is logged to a json data in case of an outage
    dump_data = {}

    if is_candle_closed:
        print("Candle closed at {}. High is at {}. Low is at {}".format(close, high, low))

        # Store financial data
        closes.append(float(close))
        highs.append(float(high))
        lows.append(float(low))

        dump_data['closes'] = closes[:]
        dump_data['highs'] = highs[:]
        dump_data['lows'] = lows[:]

        # If there is enough data to begin drawing conclusions
        if len(closes) > 20:
            # Cast the financial data to numpy arrays for efficiency
            np_closes = numpy.array(closes)
            np_highs = numpy.array(highs)
            np_lows = numpy.array(lows)

            # Calculate RSI (Relative Strength Index)
            # RSI is a leading momentum indicator
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            dump_data['rsi'] = list(rsi[:])
            last_rsi = rsi[-1]
            print('RSI:  {}'.format(last_rsi))

            # Get MACD (Moving Average Convergence Divergence)
            # MACD is a lagging momentum indicator
            # It may not be suitable for short time frames and highly volatile markets
            macd, macdsignal, macdhist = talib.MACD(np_closes, fastperiod=MACD_FASTPERIOD, slowperiod=MACD_SLOWPERIOD, signalperiod=MACD_SIGNALPERIOD)
            dump_data['macd'] = list(macd[:])
            last_macd = macdsignal[-1]
            print("MACD: {}".format(macdsignal[-1]))

            # Calculate optimum BUY trade quantity
            #       Find the EUR balance and divide it by the CLOSING PRICE
            #       - 0.001 to prevent any rounding preventing overbuy
            current_balance = float([i for i in client.get_account()['balances'] if i['asset'] == 'EUR'][0]['free'])
            optimum_buy = float(current_balance) / float(close)
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

            # Bollinger Bands - calculate Upper/Middle/Lower
            upperBandList, middleBandList, lowerBandList = talib.BBANDS(np_closes, timeperiod=20)
            upperBand = float(upperBandList[-1])
            middleBand = float(middleBandList[-1])
            lowerBand = float(lowerBandList[-1])

            # Keltners Channels - calculate the Upper/Lower
            upperKCList, lowerKCList = returnKELTNERS(np_closes, np_highs, np_lows)
            upperKC = upperKCList[-1]
            lowerKC = lowerKCList[-1]

            # Squeeze - determine squeeze position
            is_squeeze = inSqueeze(upperBandList, lowerBandList, upperKCList,lowerKCList)

            # Momentum - determine leading momentum of the market
            momentum = talib.MOM(np_closes)

            # LOG INFORMATION FOR LIVE DEBUG
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

            # SELL CONDITION
            # For this strategy:
            #       - sell if in position and the momentum is turning
            #       - or if the trade price dips below the stop loss
            if (momentum[-1] - momentum[-2] < 0 and in_position) or (close < STOP_LOSS):
                print("Overbought! Sell!, sell!, sell!")
                order_succeeded = order(SIDE_SELL, SELL_QUANTITY,
                                        TRADE_SYMBOL)
                if order_succeeded:
                    in_position = False

            # BUY CONDITION
            # For this strategy:
            #       - buy if the market has JUST exited a squeeze
            #       - has upwards momentum
            if (is_squeeze[-1] == False) and (True in is_squeeze[-6:-3]) and (momentum[-1] > 0):
                if in_position:
                    print("BUY condition, but we are already in position. Holding")
                else:
                    print("Exiting squeeze with upwards momentum. Buy! Buy!")
                    order_succeeded = order(SIDE_BUY, BUY_QUANTITY,
                                            TRADE_SYMBOL)
                    STOP_LOSS = close - 10
                    if order_succeeded:
                        in_position = True

        # Log information to the logs.json file
        print()
        with open('logs.json', 'w') as f:
            json.dump(dump_data, f)


# Run the websocket until terminated.
ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()