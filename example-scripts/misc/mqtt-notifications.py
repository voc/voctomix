#!/usr/bin/env python3
import argparse
import json
import socket

import paho.mqtt.client as mqtt

parser = argparse.ArgumentParser(description='MQTT Notifications')
parser.add_argument('-H', '--host', action='store', required=True,
                    help="Hostname/IP of the MQTT message broker.")

parser.add_argument('-P', '--port', action='store', type=int, default=1883,
                    help="Port for the MQTT message broker.")

parser.add_argument('-u', '--username', action='store',
                    help="Username for the MQTT message broker.")

parser.add_argument('-p', '--password', action='store',
                    help="Username for the MQTT message broker.")

parser.add_argument('-e', '--pbx-extension', action='store', required=True,
                    help="Phone-Extension to show incoming calls for")

args = parser.parse_args()

mqtt_client = mqtt.Client()
mqtt_client.connect(args.host, port=args.port, keepalive=60, bind_address="")
if args.username and args.password:
    mqtt_client.username_pw_set(args.username, args.password)

voctomix_connection = socket.create_connection(('127.0.0.1', 9999))
voctomix_fd = voctomix_connection.makefile('rw')


def on_call(client, userdata, message):
    payload = json.loads(message.payload)
    print(payload)

    # voc/pbx/call {
    #   "callingpres": "0",
    #   "channel": "SIP/phone-case4-000000d6",
    #   "arg_2": "/voc/pbx/call",
    #   "language": "en",
    #   "enhanced": "0.0",
    #   "callingtns": "0",
    #   "callingani2": "0",
    #   "threadid": "140699026663168",
    #   "request": "/opt/asterisk-mqtt/mqtt",
    #   "callington": "0",
    #   "arg_1": "/opt/asterisk-mqtt/mqtt.cfg",
    #   "type": "SIP",
    #   "extension": "2002",
    #   "callerid": "phone-case4",
    #   "uniqueid": "1543878375.214",
    #   "dnid": "2002",
    #   "accountcode": "",
    #   "calleridname": "VOC_Office",
    #   "priority": "2",
    #   "rdnis": "unknown",
    #   "context": "t4at-context-out",
    #   "version": "13.14.1~dfsg-2+deb9u3"
    # }
    extension = str(payload['extension'])
    caller_id = str(payload['callerid'])
    caller_name = str(payload['calleridname'])
    print("received call from %s (%s) to %s" % (extension, caller_id, caller_name))

    if extension != args.pbx_extension:
        print("target extension %s did not match expected extension %s" % (extension, args.pbx_extension))
        return

    voctomix_fd.write('show_notification Incoming Call!\n')


def on_connect(client, userdata, flags, rc):
    mqtt_client.subscribe("/voc/pbx/#")


mqtt_client.on_connect = on_connect
mqtt_client.message_callback_add("/voc/pbx/call", on_call)
mqtt_client.loop_forever()
