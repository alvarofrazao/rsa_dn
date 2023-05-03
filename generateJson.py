import json
import random
import threading
import time

NUM_OBJECTS = 3
MAX_INCREMENT = 50

objects = []
for i in range(NUM_OBJECTS):
    obj = {
        "id": i,
        "x": random.randint(1, 1000),
        "y": random.randint(1, 1000),
        "com": 0,
    }
    objects.append(obj)

with open("objects.json", "w") as f:
    json.dump(objects, f)

def update_positions(objects):
    current_obj = 0
    while True:
        time.sleep(0.1)

        current_obj = (current_obj + 1) % NUM_OBJECTS
        obj = objects[current_obj]

        update_x = random.choice([True, False])
        increment = random.randint(50,50)
        
        if random.choice([True, False]):
            increment *= -1

        if update_x:
            obj["x"] += increment
            if obj["x"] < 1:
                obj["x"] = 1
            elif obj["x"] > 1870:
                obj["x"] = 1870
        else:
            obj["y"] += increment
            if obj["y"] < 1:
                obj["y"] = 1
            elif obj["y"] > 850:
                obj["y"] = 850

        objects[current_obj] = obj
        
        with open("objects.json", "w") as f:
            json.dump(objects, f)

t = threading.Thread(target=update_positions, args=(objects,))
t.start()

t.join()
