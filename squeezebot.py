import os, pandas, plotly
import numpy
import talib


def returnSMA(array, sma_period=20):
    sma = []
    for i in range(len(array)):
        window = array[i-sma_period:i]
        if len(window) == 0:
            sma.append(None)
            continue
        else:
            moving_average = sum(window) / sma_period
            sma.append(moving_average)
    return numpy.array(sma)


def returnSTD(array, std_period=20):
    std = []
    for i in range(len(array)):
        window = array[i - std_period:i]
        if len(window) == 0:
            std.append(None)
            continue
        else:
            std_window = numpy.std(window)
            std.append(std_window)
    return numpy.array(std)


def returnBBANDS(sma, std):        # Returns upper and lower bands as np.array
    upperBand = []
    lowerBand = []
    deviations = 2
    for i in range(len(sma)):
        if sma[i] is None or std[i] is None:
            upperBand.append(None)
            lowerBand.append(None)
            continue
        else:
            upperBand.append(sma[i] + deviations*std[i])
            lowerBand.append(sma[i] - deviations * std[i])
    return numpy.array(upperBand), numpy.array(lowerBand)


def returnKELTNERS(sma, high, low, atr_period=20):
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
            upperKeltner.append(sma[i] + ATR[i]*1.5)
            lowerKeltner.append(sma[i] + ATR[i]-1.5)

    return numpy.array(upperKeltner), numpy.array(lowerKeltner)


def inSqueeze(bbands_upper, bbands_lower, keltner_upper, keltner_lower):
    squeeze = []
    for i in range(len(bbands_upper)):
        if bbands_upper[i] is None:
            squeeze.append(False)
        else:
            squeeze.append(bbands_upper[i] < keltner_upper[i] and
                           bbands_lower[i] >
                           keltner_lower[i])

    return numpy.array(squeeze)


highs = numpy.random.random(100)
lows = numpy.random.random(100)
closes = numpy.random.random(100)

sma = returnSMA(closes)
std = returnSTD(closes)

upperB, lowerB = returnBBANDS(sma, std)

upperK, lowerK = returnKELTNERS(sma, highs, lows)

squeeze = inSqueeze(upperB, lowerB, upperK, lowerK)
