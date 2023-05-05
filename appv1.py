import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
from random import randint

threading.Thread()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    # client.subscribe("vanetza/out/denm")
    # ...


# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))
    
    #print('Topic: ' + msg.topic)
    #print('Message' + message)

    # lat = message["latitude"]
    # ...


def generate(client):
    f = open('in_cam.json')
    m = json.load(f)
    m["latitude"] = randint(1,4000)
    m["longitude"] = randint(1,4000)
    print("latitude: %d",m["latitude"])
    print("longitude: %d",m["longitude"])
    m = json.dumps(m)
    client.publish("vanetza/in/cam",m)
    f.close()
    sleep(5)

drone_port = 1883
drone_ips = ["192.168.98.10","192.168.98.11","192.168.98.12","192.168.98.13","192.168.98.14"]
clients = []
threads = []

for d in drone_ips:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(d, drone_port, 60)
    clients.append(client)

for c in clients:
    thread = threading.Thread(target=c.loop_forever)
    thread.start()
    threads.append(thread)

while(True):
    for c in clients:
        generate(c)
    sleep(1)