import paho.mqtt.client as mqtt
import json
import requests

from config import HOMESTATUS_TOPIC

state = {
    'oldState': {
        'MainWanStatus': {},
        'AltWanStatus': {}
    },
    'newState': {
        'MainWanStatus': {},
        'AltWanStatus': {}
    },
}

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe([("MainWanStatus", 0), ("AltWanStatus",0), ("test1883",0 )])

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    to_ntfy(msg)

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect("pizero.internal", 1883, 60)

def to_ntfy(msg):
    if msg.topic == "MainWanStatus" or msg.topic=="AltWanStatus":
        msg_string=str(msg.payload.decode('UTF-8'))
        msg_json = json.loads(msg_string)
        state['oldState'][msg.topic] = state['newState'][msg.topic]
        state['newState'][msg.topic] = msg_json
        internet_type = "Main Internet"
        if msg_json["weight"] == "1":
            internet_type = "Alt Internet"
        if state['oldState'][msg.topic] == {}:
            pass
        elif state['oldState'][msg.topic]['value'] == 1 and state['newState'][msg.topic]['value'] == 0:
            requests.post(f"http://ntfy.pizero.internal/{HOMESTATUS_TOPIC}", data=f"{internet_type} - {msg_json.get('isp', 'Unknown ISP')} - 🔴 Connection Loss!".encode(encoding='utf-8'))
        elif state['oldState'][msg.topic]['value'] == 0 and state['newState'][msg.topic]['value'] == 1:
            requests.post(f"http://ntfy.pizero.internal/{HOMESTATUS_TOPIC}", data=f"{internet_type} - {msg_json.get('isp', 'Unknown ISP')} - 🟢 Connection Restored!".encode(encoding='utf-8'))
    elif msg.topic == "test1883":
        requests.post("http://ntfy.pizero.internal/test1883", data=f"{str(msg.payload.decode('UTF-8'))}".encode(encoding='UTF-8'))
    # print(msg.topic+" "+str(msg.payload.decode('UTF-8')))

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
mqttc.loop_forever()
