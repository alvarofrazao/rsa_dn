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


def generate():
    f = open('in_cam.json')
    m = json.load(f)
    m["latitude"] = randint(1,20)
    m["longitude"] = randint(21,30)
    print("latitude: %d",m["latitude"])
    print("longitude: %d",m["longitude"])
    m = json.dumps(m)
    client.publish("vanetza/in/cam",m)
    f.close()
    sleep(5)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("192.168.98.10", 1883, 60)

threading.Thread(target=client.loop_forever).start()

while(True):
    generate()