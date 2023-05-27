import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
from random import uniform
import pandas as pd
import random

threading.Thread()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    # client.subscribe("vanetza/out/denm")
    # ...




# É chamada automaticamente sempre que recebe uma mensagem nos tópicos subscritos em cima
def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))

    # print('Topic: ' + msg.topic)
    # print('Message' + message)

    # lat = message["latitude"]
    # ...


def generate(client, lat, longt):
    f = open('in_cam.json')
    m = json.load(f)
    m["latitude"] = lat
    m["longitude"] = longt
    m = json.dumps(m)
    client.publish("connector/in", m)
    f.close()
    sleep(2)


drone_port = 1883
connector_ips = ["192.168.98.10"]#, "192.168.98.11", "192.168.98.12",
                 #"192.168.98.13", "192.168.98.14"]
clients = []
threads = []

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



filenames_ds1 = ["set1/d1.csv", "set1/d2.csv", "set1/d3.csv",
                 "set1/d4.csv", "set1/d5.csv"]

filenames_ds2 = ["set2/d1.csv", "set2/d2.csv", "set2/d3.csv",
                 "set2/d4.csv", "set2/d5.csv"]

dataset_1 = []
dataset_2 = []
dataset_final = []

for name in filenames_ds1:
    df = pd.read_csv(name)
    dataset_1.append(df)

for name in filenames_ds2:
    df = pd.read_csv(name)
    dataset_2.append(df)

dataset_final.append(dataset_1)
dataset_final.append(dataset_2)

print("Generating positions\n")

while (True):
    for i in range(350):
        k = random.randint(0, 1)
        frame = random.randint(0, len(dataset_1))
        row = random.randint(0, len(dataset_final[k][frame]))
        lat = dataset_1[frame][row].iloc[0, 0]
        lng = dataset_1[frame][row].iloc[0, 1]
        print("Generated latitude:" + str(lat) + " longitude: "+str(lng))
        for c in clients:
            c.generate(c,lat,lng)

    sleep(15)
