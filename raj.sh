#!/bin/bash

# Stop all running containers
echo "Stopping all running containers..."
docker stop $(docker ps -q)

# Remove all containers (stopped or running)
echo "Removing all containers..."
docker rm $(docker ps -aq)

# Remove all images
echo "Removing all images..."
docker rmi $(docker images -q) -f

# Remove all volumes
echo "Removing all volumes..."
docker volume rm $(docker volume ls -q) -f

# Remove all networks
echo "Removing all networks..."
docker network rm $(docker network ls -q) -f

echo "Docker cleanup completed."