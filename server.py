from flask import Flask

app = Flask(__name__)
app.secret_key = b'asdfgsfghjkytrtgsfghjuerthmhngfgdtgwrtm'

@app.route('/')
def index():
    return 'app is running'


if __name__ == '__main__':
    app.run()      
