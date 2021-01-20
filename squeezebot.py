import os, pandas, plotly
import numpy
import talib

close = numpy.random.random(100)
upperBB, middleBB, lowerBB = talib.BBANDS(close, timeperiod=20)
