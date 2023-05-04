from flask import Flask, jsonify, render_template
import json
import paho.mqtt.client as mqtt
import random
import threading
from time import sleep
from random import randint

threading.Thread()

#####################

app = Flask(__name__)

NUM_DRONES = 3

objects = []
for i in range(NUM_DRONES):
    obj = {
        "id": i,
        "x": 0, 
        "y": 0,
        "com": 1,
        "target": 1
    }
    objects.append(obj)

with open("objects.json", "w") as f:
    json.dump(objects, f)

# Define route to return object data as JSON
@app.route('/objects.json')
def get_objects():
    with open('objects.json', 'r') as f:
        objects = json.load(f)
    return jsonify(objects)

# Define route to serve index.html template
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)

#####################

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


def generate(client, index):
    f = open('in_cam.json')
    m = json.load(f)

    #####################
    
    latitude = randint(1,1870) # 1870 so para andarem mais pela pagina
    m["latitude"] = latitude
    longitude = randint(1,850)
    m["longitude"] = longitude

    obj = objects[index]
    obj["x"] = latitude
    obj["y"] = longitude
    objects[index] = obj

    with open("objects.json", "w") as f:
            json.dump(objects, f)

    #####################

    m = json.dumps(m)
    client.publish("vanetza/in/cam",m)
    f.close()

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
    i = 0
    for c in clients:
        generate(c, i)
        i = i + 1
    sleep(1)