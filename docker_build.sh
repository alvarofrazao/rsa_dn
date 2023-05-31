cd network
cd drone
docker build . -t sender:latest 

cd ..
cd frontend
docker build . -t frontend:latest

cd ../entity
docker build . -t activent:latest 

cd ../connector
docker build . -t connector:latest 
