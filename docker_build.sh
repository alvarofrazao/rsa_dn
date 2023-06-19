cd network
cd core
docker build . -t core:latest --no-cache

cd ..
cd frontend
docker build . -t frontend:latest

cd ../entity
docker build . -t activent:latest 

cd ../drone
docker build . -t drone:latest --no-cache
