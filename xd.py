# Simulation manager. Coordinates the containers in the simulation.
from flask import Flask, send_from_directory, request, jsonify

from sys import argv
from sys import exit
from pickle import load
import os
import threading
import time
import subprocess
from datetime import datetime
import logging
import inspect

class NoStatusFilter(logging.Filter):
    def filter(self, record):
        ret = not "GET /status" in record.getMessage()
        return ret

def log(msg):
    func = inspect.currentframe().f_back.f_code
    # Dump the message + the name of this function to the log.
    logging.debug("[{:^12s}] {}".format(func.co_name,msg))

app = Flask(__name__, static_url_path='')

RUNNING = False
NODES = []
START_TIME = None
START_OFFSET = 30
ALLOWED_NODES = 200
STOP_COUNT = 0
last_ts = -1

content_metrics_fname = None
# Content distribution metrics
delta_t = 30 # seconds
aux_deliveryRate = None
delivery_rate = [] # Number of 100% nodes
cumulative_ts = -1
cumulative = [] # File progress in network
delay_e2e = {} # OBU time to 100%
aux_progRate = None
progress_rate = [] # Average file progress in network

def _basename(s):
    return os.path.basename(s)

def _runCommand(command,timeout=20,verbose=True):
    if verbose:
        log("Running '{}'".format(command))
    process = subprocess.Popen(command.split(),stdout=subprocess.PIPE)
    output, error = process.communicate(timeout)
    return output, error

# WARNING: is called inside /status, so if in the client side the polling time is too high,
# this function will not perform as expected
def contentMetrics(data):
    global delta_t, START_TIME, last_ts
    # If delta_t time has passed
    ts = round(time.time()-START_TIME)
    _count = 0
    log_metrics = False
    for d in data:
        # d.keys() = d_now<int>,d_speed<int>,d_total<int>,lat<float>,lon<float>,neighbours<list<int>>,
        # rsu<int>,ts<int>,id<int>
        if 'rsu' not in d:
            continue
        if d['rsu'] == 1:
            continue
        if not log_metrics:
            r = ts/delta_t%1
            diff = abs(round(r)-r)*delta_t
            log_metrics = diff<5 and abs(last_ts-ts)>5 # if ts in [delta_t+-5] and more than 5s apart from last write
        if log_metrics:
            _count += 1
            deliveryRate(d['d_now'],d['d_total'],ts)
            cumDist(d['d_now'],ts,last_ts)
            delayE2E(d['id'],d['d_now'],d['d_total'],ts)
            progressRate(d['id'],d['d_now'],d['d_total'],ts)

    if log_metrics:
        last_ts = ts
        writeMetrics(last_ts)
    log("ts: {}, OBUs: {}".format(ts,_count))

def writeMetrics(ts):
    global content_metrics_fname, delivery_rate, cumulative, delay_e2e, progress_rate
    with open(content_metrics_fname,'a') as f:
        fields = [str(ts),str(delivery_rate),str(cumulative),str(delay_e2e),str(progress_rate)]
        f.write(','.join(fields)+'\n')

# Delivery rate - number of OBUs that have reached 100% in each delta_t
def deliveryRate(downloadNow,downloadTotal,ts):
    global aux_deliveryRate, delivery_rate
    if aux_deliveryRate != ts:
        aux_deliveryRate = ts
        if len(delivery_rate) > 0:
            delivery_rate.append(delivery_rate[-1])
        else:
            delivery_rate.append(1)
    else:
        if downloadNow > downloadTotal*0.95:
            # node is at 95%, considered complete
            delivery_rate[-1] += 1

# Cumulative distribution - cumulative file download progress in the network, for each delta_t
def cumDist(downloadNow,ts,last_ts):
    global cumulative, cumulative_ts
    if downloadNow < 0:
        downloadNow = 0
    if ts != cumulative_ts:
        cumulative_ts = ts
        cumulative.append(downloadNow)
    else:
        cumulative[-1] += downloadNow

# End-to-end delay - time since sim_start an OBU takes to reach 100%
def delayE2E(node,downloadNow,downloadTotal,ts):
    global delay_e2e
    if node not in delay_e2e and downloadNow > downloadTotal*0.95:
        delay_e2e[node] = ts

# Progress rate - average of download progress across all OBUs, for each delta_t
def progressRate(node,downloadNow,downloadTotal,ts):
    global aux_progRate, progress_rate
    if aux_progRate != ts:
        aux_progRate = ts
        if len(progress_rate) > 0:
            avg = round(sum(progress_rate[-1])/len(progress_rate[-1]),2)
            progress_rate[-1] = avg
        progress_rate.append([downloadNow])
    else:
        progress_rate[-1].append(downloadNow)

# Returns list of nodes allowed to boot, removing the less active ones to
# fit the `max_nodes` limit, if necessary.
def allowed_nodes(path, max_nodes):
    files = [(f,-1) for f in os.listdir(path) if 'pickle' in f]
    # Temporary                                                         #OBU  #OBU  #OBU  #RSU  #RSU
    #return [x[0].split('.')[0] for x in files if x[0].split('.')[0] in ['771','832','621','997','171']]
    if max_nodes > len(files):
        return [x[0].split('.')[0] for x in files]
    i = 0
    def aux_sort(e):
        return e[1]
    while i < len(files):
        f,_ = files[i]
        files[i] = (f.split('.')[0],os.path.getsize(path+f))
        i += 1
    files.sort(key=aux_sort)
    return [f for f,_ in files[:max_nodes]]

@app.route('/')
def home():
    return send_from_directory('', 'index.html')

@app.route('/js/<path>')
def serveJS(path):
    return send_from_directory('js',path)

@app.route('/img/<path>')
def serveIMG(path):
    return send_from_directory('img',path)

@app.route('/start')
def simStart():
    global RUNNING, NODES, START_TIME, START_OFFSET, ALLOWED_NODES
    if not RUNNING:
        path = "../docker/src/sim_files/"
        startingThreads = []
        # Launching nodes
        nodes = allowed_nodes(path,ALLOWED_NODES)
        for node in nodes:
            startingThreads.append(threading.Thread(target=_runCommand,args=["../docker/start.sh -id {}".format(node),60]))
            startingThreads[-1].start()
            NODES.append(node)

        # Wait for all containers to boot
        log("Booting containers...")
        for t in startingThreads:
            t.join()
        log("Containers booted!")

        # Wait untill all nodes are ready
        ready = 0
        for n in NODES:
            host = "localhost:6{}".format(n.zfill(3))
            out, _ = (b"",None)
            timeout_base = 0
            timeout_counter = timeout_base
            while len(out) == 0:
                if timeout_counter < 3:
                    try:
                        out, _ = _runCommand('curl -s {}/status'.format(host))
                        if len(out) == 0:
                            #timeout_counter += 1
                            time.sleep(5)
                    except Exception:
                        timeout_counter += 1
                        time.sleep(1)
                else:
                    # Too many timeouts. Shutdown container and bring it back.
                    _runCommand('docker stop node_{}'.format(n))
                    _runCommand('docker rm node_{}'.format(n))
                    _runCommand('../docker/start.sh -id {}'.format(n))
                    log("Restarted container {}".format(n))
                    timeout_counter = timeout_base-3
            ready += 1
            log("{} containers remaining".format(len(NODES)-ready))
        log("All containers ready!")

        RUNNING = True
        START_TIME = round(time.time())+START_OFFSET

        # Create file with content distribution metrics
        global content_metrics_fname
        content_metrics_fname = "contentMetrics_{0:%Y-%m-%d_%H:%M:%S}".format(datetime.now())
        with open(content_metrics_fname,'a') as f:
            # fields = [str(ts),str(delivery_rate),str(cumulative),str(delay_e2e),str(progress_rate)]
            f.write("timestamp,delivery_rate,cumulative,delay_e2e,progress_rate\n")

        for n in NODES:
            #host = "172.20.{}.{}:5000".format(n.zfill(3)[0],n.zfill(3)[1:])
            host = "localhost:6{}".format(n.zfill(3))
            out,_ = _runCommand('curl -s {}/start?time={}'.format(host,START_TIME))
            while b'starting' not in out:
                out,_ = _runCommand('curl -s {}/start?time={}'.format(host,START_TIME))
                time.sleep(1)
            log(out.decode('utf-8'))
        return "Current time:{}\nSimulation starting at {}.\nNodes:{}".format(round(time.time()),START_TIME,NODES)
    else:
        return "Simulation already running."

@app.route('/stop')
def simStop():
    global RUNNING, NODES
    if not RUNNING:
        return "Simulation is not running. Nothing to be stopped."
    else:
        log("Stopping simulation.")
        _runCommand("../docker/rm.sh")
        RUNNING = False
        NODES = []
        exit(0)
        return "Simulation stopped."

@app.route('/stop_count')
def simStopCount():
    global STOP_COUNT, NODES
    STOP_COUNT += 1
    if STOP_COUNT >= len(NODES): #End if 100% of nodes are done
        log("All nodes finished.")
        STOP_COUNT = -20000
        simStop()
    return "Stop+1"

@app.route('/status')
def simStatus():
    global NODES, RUNNING, START_TIME
    if RUNNING:
        if time.time() < START_TIME:
            return "Simulation is set to start in {} seconds.".format(START_TIME-int(time.time()))
        else:
            ret = []
            ts = 0
            for n in NODES:
                #host = "172.20.{}.{}:5000".format(n.zfill(3)[0],n.zfill(3)[1:])
                host = "localhost:6{}".format(n.zfill(3))
                out, _ = _runCommand('curl -s {}/status'.format(host),verbose=False)
                d = {}
                try:
                    d = eval(out.decode('utf-8'))
                except:
                    continue
                d['id'] = n
                if int(d['ts']) > ts:
                    ts = int(d['ts'])
                ret.append(d)
            ret.append({'timestamp':ts})
            #threading.Thread(target=contentMetrics,args=[ret,]).start()
            contentMetrics(ret)
            return jsonify(ret)
    else:
        return "Simulation is not running."

def main():
    logFormatter = logging.Formatter("[%(asctime)s] %(message)s")
    rootLogger = logging.getLogger()

    fileHandler = logging.FileHandler("app.log")
    fileHandler.setFormatter(logFormatter)
    fileHandler.addFilter(NoStatusFilter())
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.addFilter(NoStatusFilter())
    rootLogger.addHandler(consoleHandler)

    rootLogger.setLevel(logging.DEBUG)
    app.run(host='0.0.0.0', port=5050)
    print("\n###\nDon't press CTRL-C again. Shutting down containers...\n###\n".upper())
    _runCommand("../docker/rm.sh")

if __name__ == '__main__':
    main()