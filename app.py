from flask import Flask, render_template, request, redirect, flash, jsonify, Markup, request
from forex_python.converter import CurrencyRates
import requests
import config
from binance.client import Client
from binance.enums import *

app = Flask(__name__)
app.secret_key = b'asdfgsfghjkytrtgsfghjuerthmhngfgdtgwrtm'
client = Client(config.API_KEY, config.API_SECRET)
ETHERSCAN_API_KEY = "I4J2Y2Z4HGSZS554H9DWJXETJD4BQ5675M"
kline_dictionary = {
    '1MINUTE': Client.KLINE_INTERVAL_1MINUTE,
    '3MINUTE': Client.KLINE_INTERVAL_3MINUTE,
    '5MINUTE': Client.KLINE_INTERVAL_5MINUTE,
    '15MINUTE': Client.KLINE_INTERVAL_15MINUTE,
    '30MINUTE': Client.KLINE_INTERVAL_30MINUTE,
    '1HOUR': Client.KLINE_INTERVAL_1HOUR,
    '2HOUR': Client.KLINE_INTERVAL_2HOUR,
    '4HOUR': Client.KLINE_INTERVAL_4HOUR,
    '6HOUR': Client.KLINE_INTERVAL_6HOUR,
    '8HOUR': Client.KLINE_INTERVAL_8HOUR,
    '12HOUR': Client.KLINE_INTERVAL_12HOUR,
    '1DAY': Client.KLINE_INTERVAL_1DAY,
    '3DAY': Client.KLINE_INTERVAL_3DAY,
    '1WEEK': Client.KLINE_INTERVAL_1WEEK,
    '1MONTH': Client.KLINE_INTERVAL_1MONTH
}

@app.route('/')
def index():
    title = 'EthTracker'
    address = '0x77C05D1bBD027dfD37e601E5788A8226E5203cA8'
    forex_object = CurrencyRates()
    kline_interval = request.args.get('kline_interval', default ='4HOUR')

    # Get balance from etherscan
    apicall = requests.get("https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey=I4J2Y2Z4HGSZS554H9DWJXETJD4BQ5675M".format(address=address))
    balance = int(apicall.json()['result']) / 10**18

    # Get historical data
    candlesticks = client.get_historical_klines(
        'ETHEUR',
        kline_dictionary[kline_interval],
        "1 Dec, 2020")
    processed_candlesticks = []
    for data in candlesticks:
        candlestick = {
            "time": (int(data[0])/1000) + 13*3600, # nzt adjustment
            "open": data[1],
            "high": data[2],
            "low": data[3],
            "close": data[4]
        }
        processed_candlesticks.append(candlestick)

    # Get current price
    initial_investment = 1500.00
    current_price_euros = float(processed_candlesticks[-1]['close'])
    current_price_nzd = forex_object.convert('EUR', 'NZD', current_price_euros * balance)
    net_profit = current_price_nzd - initial_investment
    percentage_profit = (current_price_nzd / initial_investment) * 100 - 100

    return render_template('index.html',
                           title=title,
                           kline_dictionary=list(kline_dictionary.keys()),
                           kline_interval=kline_interval,
                           processed_candlesticks=Markup(processed_candlesticks),
                           address=address,
                           balance=balance,
                           current_price_nzd=round(current_price_nzd,2),
                           net_profit=round(net_profit, 2),
                           percentage_profit=round(percentage_profit, 2))


if __name__ == '__main__':
    app.run(debug=True)         # Allows for refresh on save
