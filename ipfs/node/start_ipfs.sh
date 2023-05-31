address=$API_ADDRESS

echo "address" $address
echo "env var" $API_ADDRESS

ipfs init

ipfs id

ipfs daemon --migrate --api $address  && ipfs swarm connect /ip4/192.168.98.40/tcp/4001

ipfs swarm peers

