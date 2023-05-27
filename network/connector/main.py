import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
from random import uniform
import os
import pandas as pd
import ipfshttpclient as ipfs
from math import sin, cos, tan, atan2, sqrt
import multiaddr

bootstrap_ip = "192.168.98.40"
bootstrap_port = 4001

mqtt_port = 1883
m_client = None
core = None
current_x = 40.95
current_y = -7.95
core_ip = "192.168.98.20"

f = open('denm.json')
denm = json.load(f)
f.close()


def file_renaming(x):
    dest = str(x) + ".jpg"
    os.rename(src, dest)
    return dest


container_id = int(os.environ.get('CONNECTOR_ID'))

container_queue = os.environ.get('CONNECTOR_QUEUE')

daemon_ip = os.environ.get('IPFS_DAEMON_IP')
address = multiaddr.Multiaddr("/ip4/" + daemon_ip + "/tcp/4001")
client = ipfs.connect(str(address),session=True)

mqtt_ip = os.environ.get('OBU_IP')


src = 'forest.jpg'
path = file_renaming(container_id)
result = client.add(path)

cid = result['Hash']

msg_count = 0


def receive_coords(client, userdata, msg):
    message = json.loads(msg.payload.decode('utf-8'))
    current_x = message['latitude']
    current_y = message['longitude']



def detect(lat, lng):
    R = 6733
    dlon = lat-current_x
    dlat = lng-current_y
    a = (sin(dlat/2))**2 + cos(current_x) * cos(lat) * (sin(dlon/2))**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    if(distance < 5.0):
        return True
    else:
        return False


def on_message(client, userdata, msg):

    message = json.loads(msg.payload.decode('utf-8'))
    lat = message['latitude']
    lng = message['lng']
    denm['management']['actionID']['originatingStationID'] = container_id
    denm['management']['actionID']['sequenceNumber'] = cid
    m = json.dump(denm)
    if(detect(lat,lng)):
        client.publish("connector/out", m)


def on_connect(client):
    print("Sucessfully connected in mqtt")
    client.subscribe("connector/in")

def on_connect_core(client):
    print("Sucessfully connected in mqtt")
    client.subscribe("connector/core/in")


def remote_setup(mip, mport):
    m_client = mqtt.Client()
    m_client.on_connect = on_connect
    m_client.on_message = on_message
    m_client.connect(mip, mport, 60)
    core = mqtt.Client()
    core.on_connect = on_connect_core
    core.on_message = receive_coords
    core.connect(mip,mport,60)


def file_renaming(x):
    dest = str(x) + ".jpg"
    os.rename(src, dest)


file_renaming(container_id)

remote_setup(mqtt_ip,mqtt_port)

m_thread = threading.Thread(target=m_client.loop_forever)
c_thread = threading.Thread(target=core.lopp_forever)
i_thread = threading.Thread(target=client.loop_forever)
m_thread.start()
c_thread.start()


while(True):
    m = json.dump(denm)
    client.publish("connector/out", m)
    sleep(20)