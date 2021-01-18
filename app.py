from flask import Flask, render_template, request, redirect, flash, jsonify
import config
from binance.client import Client
from binance.enums import *

app = Flask(__name__)
app.secret_key = b'asdfgsfghjkytrtgsfghjuerthmhngfgdtgwrtm'
client = Client(config.API_KEY, config.API_SECRET)


@app.route('/')
def index():
    title = 'EthTrader'

    # Get balances
    info = client.get_account()
    balances = [i for i in info['balances'] if float(i['free']) > 0]

    # Get trade symbols
    exchange_info = client.get_exchange_info()
    symbols = [s['symbol'] for s in exchange_info['symbols']]
    symbols = [s for s in symbols if s[-3:] == "EUR" or s[:3] == "EUR"]

    return render_template('index.html',
                           title=title,
                           balances=balances,
                           symbols=symbols)


@app.route('/buy', methods=['POST'])
def buy():
    """BUY method which purchases a set amount of currency"""
    try:
        print(request.form['quantity'], request.form['symbol'])
        client.create_order(
            symbol=request.form['symbol'],
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=request.form['quantity'])
    except Exception as e:
        flash(str(e), 'error')

    return redirect('/')


@app.route('/sell')
def sell():
    return 'sell'


@app.route('/settings')
def settings():
    return 'settings'


@app.route('/history')
def history():
    candlesticks = client.get_historical_klines(
        'ETHEUR',
        Client.KLINE_INTERVAL_5MINUTE,
        "1 Jan, 2021")

    processed_candlesticks = []
    for data in candlesticks:
        candlestick = {
            "time":  data[0],
            "open":  data[1],
            "high":  data[2],
            "low":   data[3],
            "close": data[4]/1000
        }
        processed_candlesticks.append(candlestick)
    return jsonify(processed_candlesticks)


if __name__ == '__main__':
    app.run(debug=True)         # Allows for refresh on save
