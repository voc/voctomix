#!/usr/bin/env python3

import socket

from flask import Flask, redirect, render_template, request, url_for
from lib.config import Config

app = Flask(__name__)

buttons = [
    dict(Config.items('buttons.' + name))
    for name in Config.get('buttons', 'buttons').split(',')
]
connection_params = (
    Config.get('server', 'host') or 'localhost',
    Config.get('server', 'port') or 9999,
)


@app.route('/')
def index():
    return render_template('index.html.j2', buttons=buttons)


@app.route('/run', methods=['POST'])
def run():
    send_command(request.form.get('command'))
    return redirect(url_for('index'), code=303)


def send_command(command: str) -> str:
    sock = socket.create_connection(connection_params)

    print('sending command: %s' % command)
    sock.send((command + '\r\n').encode('utf-8'))

    response = sock.recv(2048).decode('utf-8')
    print('received response: %s' % response)

    sock.close()
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
