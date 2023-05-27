cd ipfs/node
docker build . -t regnode:latest --no-cache

cd ..
cd bootstrap
docker build . -t btnode:latest --no-cache