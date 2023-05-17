from flask import Flask, jsonify, render_template
import json
import paho.mqtt.client as mqtt
import random
import threading
from time import sleep
from random import randint

threading.Thread()

#####################

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("flask/in")
    # client.subscribe("vanetza/out/denm")
    # ...

""" def generate(client, index):
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
    f.close() """




app = Flask(__name__)

NUM_DRONES = 6

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

def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))
    obj['id']= message['id']
    obj['x'] = abs(message['x'])
    obj['y'] = abs(message['y'])
    objects[message['id']] = obj
    with open("objects.json", "w") as f:
        json.dump(objects, f)



msg_src = mqtt.Client()
msg_src.on_connect = on_connect
msg_src.on_message = on_message
msg_src.connect("192.168.98.20",1883,60)

msg_thread = threading.Thread(target=msg_src.loop_forever)
msg_thread.start()

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
    flask_thread = threading.Thread(target = app.run(host = '0.0.0.0',debug=True))
    flask_thread.start()
    

#####################


