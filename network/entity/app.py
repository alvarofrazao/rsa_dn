import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
from random import uniform
import pandas as pd
import random

threading.Thread()

gen_start = [0.0,0.0]
gen_end = [0.0,0.0]

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # client.subscribe("vanetza/out/denm")
    # ...


# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))

    # print('Topic: ' + msg.topic)
    # print('Message' + message)

    # lat = message["latitude"]
    # ...

def gen_con(client,userdata,flags,rc):
    print("Connected to generator broker with code" + str(rc))
    client.subscribe("generator/in")

def gen_msghndl(client,userdata, msg):
    global gen_start,gen_end
    m = json.loads(msg.payload.decode('utf-8'))
    gen_start = [m['start_lat'],m['start_longt']]
    gen_end = [m['far_lat'],m['far_longt']]

def generate(client,pos):
    f = open('in_cam.json')
    m = json.load(f)
    m["latitude"] = pos[0]
    m["longitude"] = pos[1]
    m = json.dumps(m)
    client.publish("connector/in", m)
    f.close()


drone_port = 1883
connector_ips = ["192.168.98.10", "192.168.98.11", "192.168.98.12",
                 "192.168.98.13", "192.168.98.14"]
core_ip = "192.168.98.20"
clients = []
threads = []

gen_client = mqtt.Client()
gen_client.on_connect = gen_con
gen_client.on_message = gen_msghndl
gen_client.connect(core_ip,drone_port,60)
thread = threading.Thread(target=gen_client.loop_forever)
thread.start()
threads.append(thread)


for d in connector_ips:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(d, drone_port, 60)
    clients.append(client)


for c in clients:
    thread = threading.Thread(target=c.loop_forever)
    thread.start()
    threads.append(thread)



print("Generating positions:\n")

while (True):
    
    pos = [round(random.uniform(gen_start[0],gen_end[0]),8),round(random.uniform(gen_start[1],gen_end[1]),8)]
    print("Activty generated at lat - " + str(pos[0]) + " longt - " + str(pos[1]))
    for c in clients:
        generate(c,pos)
    sleep(random.randint(1,4))
