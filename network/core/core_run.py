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
drone_number = int(os.environ.get('DRONE_NUMBER'))

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

core_positions = [40.83548605,-7.99394846]
core_positions_2 = [40.92291692,-7.94251441]
marker_positions = []

def update_markers():
    global gen_client
    #print("Sending message to frontend")
    for i in range(0,len(drn_pos)):
        marker_positions[i]['lat'] = drn_pos[i][0]
        marker_positions[i]['longt'] = drn_pos[i][1]
        marker_positions[i]['id'] = i

    m = json.dumps(marker_positions)

    gen_client.publish("frontend/in",m)

    sleep(0.75)

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
        grid = [[[0.0, 0.0] for _ in range(n)] for _ in range(n)]
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

            centers.append([avg_lat,avg_long])

    return centers

def drone_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("connector/out")

def drone_onmsg(client, userdata, message):
    global run_count,drn_state,det_count,drn_pos
    m = json.loads(message.payload.decode('utf-8'))
    code = m['event']
    drone_id = m['id']
    if(code == 5):
        file_hash = m['cid']
        det_count[drone_id] += 1
        api.get(file_hash)
        print("File was requested from container " + str(drone_id))
    else:
        if(m['event']== 2):
            run_count[drone_id] += 1
            drn_pos[drone_id] = [core_positions[0],core_positions[1]]
            drn_state[drone_id] = 0
        else:
            drn_pos[drone_id] = [m['pos_lat'],m['pos_lng']]
            drn_state[drone_id] = m['state']
    update_markers()

def initiate(clients,pos):
    global drn_pos,drn_state,det_count
    f = open('cm.json')
    m = json.load(f)
    m["target_lat"] = pos[0]
    m["target_lng"] = pos[1]
    m['start'] = False
    m = json.dumps(m)


    for c in clients:
        drn_pos.append(pos)
        drn_state.append(0)
        det_count.append(0)
        run_count.append(0)
        c.publish("connector/core/in", m)
    f.close()

def send_coords(client,pos):
    global drn_state

    f = open('cm.json')
    m = json.load(f)
    m["target_lat"] = pos[0]
    m["target_lng"] = pos[1]
    m['start'] = True
    drn_state[i] = 1
    m = json.dumps(m)
    f.close()
    client.publish("connector/core/in", m)
    sleep(0.5)

def gen_con(client,userdata,flags,rc):
    print("Sucessfully connected to rsu broker with code " + str(rc))

def gen_onmsg(client,userdata,message):
    m = json.loads(message.payload.decode('utf-8'))

    print("Unexpected message received on generator client\n")

def init_gen(gen_client,pos0,posN):

    obj = {
    "start_lat": pos0[0],
    "start_longt": pos0[1],
    "far_lat": posN[0],
    "far_longt": posN[1],
    }
    m = json.dumps(obj)
    gen_client.publish("generator/in",m)

gen_client = mqtt.Client()
gen_client.on_connect = gen_con
gen_client.on_message = gen_onmsg
gen_client.connect("192.168.98.20",drone_port,60)
thread = threading.Thread(target=gen_client.loop_forever)
thread.start()
threads.append(thread)



for i in connector_ips:
    i_client = mqtt.Client()
    i_client.on_connect = drone_connect
    i_client.on_message = drone_onmsg
    i_client.connect(i, drone_port, 60)
    i_clients.append(i_client)

for i in i_clients:
    thread = threading.Thread(target=i.loop_forever)
    thread.start()
    threads.append(thread)

cur_quarter = 0
distance = 3
cell_grid = generate_cells(core_positions[0],core_positions[1],distance,drone_number)
centers = gen_centers(cell_grid[cur_quarter],drone_number)

center_state = [False] * (len(centers)-1)

maintain = False

k = 0
det_total = 0
initiated = 0
sleep(20)
initiate(i_clients,core_positions)


for i in range(0,len(drn_pos)):
    obj = {
    "lat": core_positions[0],
    "longt": core_positions[1],
    "id": i,
    }
    marker_positions.append(obj)

sleep(5)
init_gen(gen_client,core_positions,cell_grid[cur_quarter][drone_number-1][drone_number-1])

while (True):
    for i in range(0,(len(i_clients))):
        
        if(drn_state[i] == 0):
            for a in range(0,len(centers)):
                if (center_state[a] == False):
                    center_state[a] = True
                    send_coords(i_clients[i],centers[a])
                    drn_state[i] = 1
                    #print("Sent to client " + str(i) + " cell center of coordinates: " + str(centers[k]) + "\n")
                    break
                else:
                    k +=1
                if(k >= len(centers)):
                    k = 0
                    cur_quarter += 1
                    if(cur_quarter >= 4):
                        cur_quarter = 0
                    centers = gen_centers(cell_grid[cur_quarter],drone_number)
                    init_gen(gen_client,core_positions,cell_grid[cur_quarter][drone_number-1][drone_number-1])
                #Should have some logic because this means that the quarter has already been processed - to do after testing
        else:
            pass
    for count in det_count:
        det_total += count
    if (det_total > drone_number):
        maintain = True
    else:
        if(cur_quarter >= 4):
            cur_quarter = 0
            det_total = 0
            #print("All cells have been scanned\n")
            #print("Total scanned objects = " + str(det_total))
    x = 0
    print("Current drone positions:")
    for pos in drn_pos:
        print("Drone ID - " + str(x) + " lat - " + str(round(pos[0],4)) + " longt - " + str(round(pos[1],4)) + "state - " + state[drn_state[x]])
        x+=1
    print("Current detection counters:")
    print(det_count)
    print("Total Number of runs per drone:")
    print(run_count)
    sleep(1)

