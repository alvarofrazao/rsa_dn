echo "Building IPFS containers"
./ipfs_build.sh
sleep 1

echo "Building unit Containers"
./docker_build.sh

