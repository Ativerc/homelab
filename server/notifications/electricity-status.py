from subprocess import DEVNULL, call
import json 
import time
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import paho.mqtt.publish as publish


from config import ELEC_HOSTNAME, ELEC_TOPIC, RPI_IP, RPI_HOSTNAME

state = {
    "oldState": {
        "value": 0,
        "timestamp": "" 
    },
    "newState": {
        "value": 0,
        "timestamp": ""
    }
}



def ntfy_post(msg):
    try:
        retry = Retry(
            total=10,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry)

        session = requests.Session()
        session.mount('http://', adapter)
        r = session.post('http://ntfy.pizero.internal/homestatus', data=msg.encode(encoding='utf-8'), timeout=180)
        print(r.status_code)
    except Exception as e:
        print(e)


def mqtt_publish(value, timestamp):
    data = {
        "value": 1 - value,
        "timestamp": timestamp
    }
    payload = json.dumps(data)
    publish.single(ELEC_TOPIC, payload=payload, hostname=RPI_HOSTNAME, retain=True)


while 1:
    response = call(['ping', '-c', '1', '-W', '1', ELEC_HOSTNAME], stderr=DEVNULL, stdout=DEVNULL)
    # response = os.system(f"ping -c 1 -W 1 {HOSTNAME} &> /dev/null") # 0 = OK else NOK
    # print(f"{response} | OS: {state['oldState']['value']} | NS: {state['newState']['value']}")
    # Copy newState values to oldState
    state['oldState'] = {
        'value': state['newState']['value'],
        'timestamp': state['newState']['timestamp']
    }
    # print(f"latestState {response} | newState {state['newState']['value']}-> oldState {state['oldState']['value']}")

    # Copy current values to newState
    state['newState']['value'] = response
    state['newState']['timestamp'] = datetime.now().isoformat()
    # print(f"latestState {response}-> newState {state['newState']['value']}-> oldState {state['oldState']['value']}")

    if response == 0:
        # print(f"latestState {response}-> newState {state['newState']['value']}-> oldState {state['oldState']['value']}")
        if state['oldState']['value'] != 0 and state['newState']['value'] == 0:
            print(f"Power Restored!| Latest {response} | newState val: {state['newState']['value']} | oldState val: {state['oldState']['value']} ")
            msg="⚡ - 🟢 Electric Power Restored!"
            ntfy_post(msg)
            try:
                mqtt_publish(value=state['newState']['value'], timestamp=state['newState']['timestamp'])
            except Exception as e:
                print(e)
    else: # ping fail
        # print(f"latestState {response}-> newState {state['newState']['value']}-> oldState {state['oldState']['value']}")
        if state['oldState']['value'] == 0 and state['newState']['value'] != 0:
            print(f"Power Loss! | Latest: {response} | newState val: {state['newState']['value']} | oldState val: {state['oldState']['value']}")
            msg="⚡ - 🔴 Electric Power Loss!"
            ntfy_post(msg)
            try:
                mqtt_publish(value=state['newState']['value'], timestamp=state['newState']['timestamp'])
            except Exception as e:
                print(e)


    time.sleep(3)