# RSA - Drone Network for Data Gathering

## Contents
- /ipfs folder contains all files related to the IPFS network used in the project
- /network contains all files related to the drone/core units referred in the report
- /vanetza contains docker compose file needed to run the MQTT brokers used in the project

## How to run

Preliminary steps (first time execution only):

- Install Docker if it's not already present on your system

- Update Vanetza images:
```bash
docker pull code.nap.av.it.pt:5050/mobility-networks/vanetza:latest
``` 
- Create the docker network used by the drones:
```bash
docker network create vanetzalan0 --subnet 192.168.98.0/24
``` 

- Build unit and IPFS containers using the build_all.sh file

Running the project:

Open 3 terminal windows;

In each of them, run the docker-compose file present in the /vanetza, /ipfs and /network folders

To stop the running of the project, simply run the cleanup.sh script
