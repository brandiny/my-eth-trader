import numpy, talib


my_data = numpy.genfromtxt('data/1_minute_candlesticks.csv', delimiter=',')
close = my_data[:,4]
print(close)

# How to change the time period of the SMA
moving_average = talib.SMA(close, timeperiod=12)
print(moving_average)

# How to change the time period of the SMA
rsi = talib.RSI(close)
print(rsi)