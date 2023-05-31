import json
import paho.mqtt.client as mqtt
import threading
from time import sleep
from random import randint, uniform
import pandas as pd
import ipfshttpclient as ipfs
import math

import os
import multiaddr

threading.Thread()

daemon_ip = os.environ.get('IPFS_DAEMON_IP')
address = multiaddr.Multiaddr("/ip4/" + daemon_ip + "/tcp/5001")
api = ipfs.connect(str(address), session=True)
drone_number = os.environ.get('DRONE_NUMBER')

drone_port = 1883
drone_ips = ["192.168.98.10", "192.168.98.11", "192.168.98.12",
             "192.168.98.13", "192.168.98.14", "192.168.98.20"]
state = ["AtBase", "Departing", "Scanning", "Returning"]
quarter_length = 3 #in km

connector_ips = ["192.168.98.10", "192.168.98.11", "192.168.98.12",
                 "192.168.98.13", "192.168.98.14"]
# ["192.168.98.80", "192.168.98.81","192.168.98.82", "192.168.98.83", "192.168.98.84"]


threads = []
i_clients = []
det_count = []
drn_state = []
drn_pos = []
run_count = []

core_positions = (40.83548605,-7.99394846)

def generate_cells(start_lat, start_long, distance, n):

    planetary_radius = 6371.0  # in kilometers

    increment = distance/n

    directions = [(1,1),(1,-1),(-1,-1),(-1,1)] # NE,NW,SW,SE
    grid_quarters = []

    # Compute latitude variation
    delta_latitude = math.degrees(increment / planetary_radius)

    # Compute longitude variation
    delta_longitude = math.degrees(math.asin(
        math.sin(math.radians(delta_latitude)) / math.cos(math.radians(start_lat))))

    for dir in directions:
        grid = [[(0.0, 0.0) for _ in range(n)] for _ in range(n)]
        for lat_idx in range(0, n): # row iteration (latitude variation)
            for long_idx in range(0,n): #column iteration (longitude variation)
                grid[lat_idx][long_idx] = (start_lat+(dir[0]*(delta_latitude*lat_idx)),start_long+(dir[1]*(delta_longitude*long_idx)))
        grid_quarters.append(grid)
    return grid_quarters

def gen_centers(cell_grid, n):
    
    centers = []
    for a in range(0,n-2):
        for b in range(0,n-2):
            latitudes = [math.radians(lat) for lat,_ in [cell_grid[a][b],cell_grid[a+1][b],cell_grid[a][b+1],cell_grid[a+1][b+1]]]
            longitudes = [math.radians(long) for _,long in [cell_grid[a][b],cell_grid[a+1][b],cell_grid[a][b+1],cell_grid[a+1][b+1]]]

            avg_lat = math.degrees(sum(latitudes)/4)
            avg_long = math.degrees(sum(longitudes)/4)

            centers.append((avg_lat,avg_long))

    return centers

def ipfs_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("connector/out")

def onmsg_req(client, userdata, message):
    global run_count,drn_state,det_count,drn_pos
    m = json.loads(message.payload.decode('utf-8'))
    code = m['situation']['eventType']['causeCode']
    drone_id = m['management']['actionID']['originatingStationID']
    if(code == 5):
        file_hash = m['management']['actionID']['sequenceNumber']
        det_count[drone_id] += 1
        api.get(file_hash)
        print("File was requested from container" + str(drone_id))
    else:
        if(m['situation']['eventType']['causeCode'] == 2):
            run_count[drone_id] += 1
            drn_pos[drone_id] = core_positions[0]
            drn_state[drone_id] = state[0]
        else:
            drn_pos[drone_id] = (m['management']['eventPosition']['latitude'],m['management']['eventPosition']['longitude'])
            drn_state = m['situation']['eventType']['subCauseCode']

def initiate(clients,pos):
    global drn_pos,drn_state,det_count
    f = open('in_cam.json')
    m = json.load(f)
    m["latitude"] = pos[0]
    m["longitude"] = pos[1]
    m['gasPedal'] = False
    m = json.dumps(m)
    f.close()
    for c in clients:
        drn_pos.append(pos)
        drn_state.append(state[0])
        det_count.append(0)
        run_count.append(0)
        c.publish("connector/core/in", m)
    sleep(0.5)

def send_coords(client,pos):
    f = open('in_cam.json')
    m = json.load(f)
    m["latitude"] = pos[0]
    m["longitude"] = pos[1]
    m['gasPedal'] = True
    m = json.dumps(m)
    f.close()
    client.publish("connector/core/in", m)
    sleep(0.5)



for i in connector_ips:
    i_client = mqtt.Client()
    i_client.on_connect = ipfs_connect
    i_client.on_message = onmsg_req
    i_client.connect(i, drone_port, 60)
    i_clients.append(i_client)
    det_count.append(0)
    drn_state.append(state[0])

for i in i_clients:
    thread = threading.Thread(target=i.loop_forever)
    thread.start()
    threads.append(thread)

cur_quarter = 0
distance = 3
cell_grid = generate_cells(core_positions[0],core_positions[1],distance,drone_number)
centers = gen_centers(cell_grid[cur_quarter],drone_number)

center_state = [False] * (len(centers)-1)
while (True):
    initiate(i_clients,core_positions)
    for i in i_clients:
        k = 0
        for a in center_state:
            if(~a):
                center_state[k] = True
                send_coords(i,centers[k])
            else:
                k +=1
    sleep(2)

