import socket
from lib.config import Config
from flask import Flask, render_template, request
app = Flask(__name__)

buttons = [dict(Config.items('buttons.'+name)) for name in Config.get('buttons','buttons').split(',')]
connection_params = (Config.get('server', 'host') or 'localhost', Config.get('server', 'port') or 9999)

@app.route("/")
def index():
    return render_template("index.html.j2", buttons=buttons)

@app.route("/run")
def run():
    return send_command(request.args.get("command"))


def send_command(command: str) -> str:
    sock = socket.create_connection(connection_params)

    print("sending command: %s" % command)
    sock.send( (command + '\r\n').encode('utf-8') )

    response = sock.recv(2048).decode('utf-8')
    print("received response: %s" % response)

    sock.close()
    return response
