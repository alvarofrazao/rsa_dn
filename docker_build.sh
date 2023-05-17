cd drone
docker build . -t sender:latest

cd ..
cd frontend
docker build . -t frontend:latest