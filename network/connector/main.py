import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
from random import randint
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
current = (0.0,0.0)
target = (0.0,0.0)
core_ip = "192.168.98.20"

f = open('denm.json')
denm = json.load(f)
f.close()


container_id = int(os.environ.get('CONNECTOR_ID'))

container_queue = os.environ.get('CONNECTOR_QUEUE')

daemon_ip = os.environ.get('IPFS_DAEMON_IP')
address = multiaddr.Multiaddr("/ip4/" + daemon_ip + "/tcp/5001")
client = ipfs.connect(str(address),session=True)

mqtt_ip = os.environ.get('OBU_IP')


curpath = os.path.join('/app','forest.jpg')
dest = str(container_id)+'.jpg'
path = os.path.join('/app',dest)
#os.rename(curpath,path)
result = client.add('forest.jpg')

cid = result['Hash']

msg_count = 0
state = ["AtBase", "Departing", "Scanning", "Returning"]
cur_state = ''
dest_pth = []
ret_path = []

def move(start,end, steps):
    x_displacement = round(end[0] - start[0],5)
    y_displacement = round(end[1] - start[1],5)
    # print("Moving", x_displacement, "in x axis and", y_displacement, "in y axis" )
    x_step = x_displacement/steps
    y_step = y_displacement/steps
    crds = []
    new_x = start[0]
    new_y = start[1]

    #does not include starting position coordinates
    for i in range (steps):
        new_x += x_step
        new_y += y_step
        crds.append((new_x, new_y))

    print(crds)
    return crds

def receive_coords(client, userdata, msg):
    global current
    global target
    global cur_state,dest_pth,ret_path
    message = json.loads(msg.payload.decode('utf-8'))

    if(~message['gasPedal']):
        current[0] = message['latitude']
        current[1] = message['longitude']
        cur_state = "AtBase"
    else: 
        if(message['gasPedal']):
            target[0] = message['latitude']
            target[1] = message['longitude']
            cur_state = "Departing"
            dest_pth = move(current,target,15)
            ret_path = dest_pth[::-1]
        else:
            print("unexpected error occured: message does not fulfill requirements")

def detect(lat, lng):
    global msg_count
    R = 6733
    dlon = lat-current[0]
    dlat = lng-current[1]
    a = (sin(dlat/2))**2 + cos(current[0]) * cos(lat) * (sin(dlon/2))**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    msg_count = msg_count + 1
    if(distance < 0.7):
        print("Detected object at lat: " + str(lat) + " long: " + str(lng) + "\n")
        return True
    else:
        return False


def on_message(client, userdata, msg):

    message = json.loads(msg.payload.decode('utf-8'))
    lat = message['latitude']
    lng = message['longitude']
    denm['management']['actionID']['originatingStationID'] = container_id
    denm['management']['actionID']['sequenceNumber'] = cid
    denm['management']['eventPosition']['latitude'] = current[0]
    denm['management']['eventPosition']['longitude'] = current[1]
    denm['situation']['eventType']['causeCode'] = 5
    m = json.dumps(denm)
    if(detect(lat,lng)):
        print("Sent notification to network core\n")
        client.publish("connector/out", m)

def update(client,pos,state,event):

    denm['management']['actionID']['originatingStationID'] = container_id
    denm['situation']['eventType']['causeCode'] = event
    denm['situation']['eventType']['subCauseCode'] = state
    denm['management']['eventPosition']['latitude'] = pos[0]
    denm['management']['eventPosition']['longitude'] = pos[1]
    m = json.dumps(denm)
    client.publish("connector/out",m)
    sleep(1.5)

def on_connect(client, userdata, flags, rc):
    print("Sucessfully connected in mqtt")
    client.subscribe("connector/in")

def on_connect_core(client, userdata, flags, rc):
    print("Sucessfully connected in mqtt")
    client.subscribe("connector/core/in")


m_client = mqtt.Client()
core = mqtt.Client()
m_client.on_connect = on_connect
m_client.on_message = on_message
core.on_connect = on_connect_core
core.on_message = receive_coords
m_client.connect(mqtt_ip, mqtt_port, 60)
core.connect(mqtt_ip,mqtt_port,60)


m_thread = threading.Thread(target=m_client.loop_forever)
m_thread.start()
c_thread = threading.Thread(target=core.loop_forever)
c_thread.start()

while(True):
    while(cur_state == state[0]):
        pass
    if(cur_state == state[1]):
        for pos in dest_pth:
            current = pos
            update(core,current,1,1)
        cur_state = state[2]
        update(core,current,2,1)
    if(cur_state == state[2]):
        sleep(randint(5,10)*1.5)
        cur_state = state[3]
        update(core,current,3,1)
    for pos in ret_path:
        current = pos
        update(core,current,3,1)
    update(core,current,0,2)
