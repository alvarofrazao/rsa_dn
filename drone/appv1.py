import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
from random import randint
import pandas as pd

threading.Thread()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("vanetza/out/cam")
    # client.subscribe("vanetza/out/denm")
    # ...
def con_flask(client,rc):
    print("Connected with result code "+str(rc))
    client.subscribe("flask/out")



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
    client.publish("vanetza/in/cam", m)
    f.close()
    sleep(2)


drone_port = 1883
drone_ips = ["192.168.98.10", "192.168.98.11", "192.168.98.12",
    "192.168.98.13", "192.168.98.14", "192.168.98.20"]
clients = []
threads = []

for d in drone_ips:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(d, drone_port, 60)
    clients.append(client)

flask_cl = mqtt.Client()
flask_cl.on_connect = on_connect
flask_cl.on_message = on_message
flask_cl.connect("192.168.98.20",drone_port,60)

obj = {
        "id": 0,
        "x": 0, 
        "y": 0,
        "com": 1,
        "target": 1
    }


def send2flask(flask_cl,id,lat,longt):
    obj['id'] = id
    obj['x'] = lat
    obj['y'] = longt

    m = json.dumps(obj)
    flask_cl.publish("flask/in",m)



for c in clients:
    thread = threading.Thread(target=c.loop_forever)
    thread.start()
    threads.append(thread)

filenames = ["coords/d1.csv", "coords/d2.csv", "coords/d3.csv",
    "coords/d4.csv", "coords/d5.csv", "coords/core.csv"]
dataframes = []

for name in filenames:
    df = pd.read_csv(name)
    dataframes.append(df)

r_idx = 0
while (True):
    df_idx = 0
    for c in clients:
        lat = randint[0,1200]#dataframes[df_idx].iloc[0, 0]
        longt =  randint[0,1200]#dataframes[df_idx].iloc[0, 1]
        generate(c,lat,longt)
        send2flask(flask_cl,df_idx,lat,longt)
        df_idx += 1
        sleep(2)
    
    r_idx += 1