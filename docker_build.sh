cd drone
docker build . -t sender:latest --no-cache

cd ..
cd frontend
docker build . -t frontend:latest --no-cache