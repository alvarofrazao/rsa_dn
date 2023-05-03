import json
import paho.mqtt.client as mqtt
import threading
from time import sleep

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))
    print('Topic: ' + msg.topic)
    print('Message' + message)

def generate(client, topic):
    f = open('/app/in_cam.json')
    m = json.load(f)
    m["latitude"] = 0
    m["longitude"] = 0
    m = json.dumps(m)
    client.publish(topic, m)
    f.close()

clients = [
    {"name": "client1", "host": "192.168.98.10", "port": 1883, "topic": "vanetza/in/cam1"},
    {"name": "client2", "host": "192.168.98.20", "port": 1883, "topic": "vanetza/in/cam2"},
    # Add more clients here
]

threads = []

for c in clients:
    client = mqtt.Client(c["name"])
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(c["host"], c["port"], 60)
    thread = threading.Thread(target=client.loop_forever)
    thread.start()
    threads.append(thread)

while True:
    for c in clients:
        generate(client=c, topic=c["topic"])
    #print("Hello world\n")
    sleep(1)
    
