from time import sleep
from flask import Flask, render_template
from flask_mqtt import Mqtt
import json
import paho.mqtt.client as mqtt
import threading

app = Flask(__name__)

core_positions = [40.83548605, -7.99394846]
rsu_ip = "192.168.98.20"
marker_positions = []
app.template_folder = 'templates'
app.static_folder = 'static'
app.config['MQTT_BROKER_URL'] = "192.168.98.20"
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_CLIENT_ID'] = 'flask_api'
app.config['MQTT_KEEPALIVE'] = 30  # Set KeepAlive time in seconds
mqtt = Mqtt(app)

obj = {
    'lat': 0.0,
    'longt':0.0,
    'id':99
}


for idx in range(0, 5):
    marker_positions.append(obj)

@mqtt.on_connect()
def on_connect(client, userdata, flags, rc):
    print("Connected sucessfully TO CORE BROKER with code" + str(rc) + "\n")
    client.subscribe("frontend/in")

@mqtt.on_message()
def on_message(client, userdata, message):
    global marker_positions
    m = json.loads(message.payload.decode('utf-8'))
    #print("Received message from core\n")
    marker_positions = m
    #print(marker_positions)

@app.route('/get_data', methods=['GET'])
def send_data():
    # Send boats coordinates to frontend
    global marker_positions
    return json.dumps(marker_positions)


@app.route('/')
def root():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host="192.168.98.101", port=5000, debug=True)
