#!/bin/bash

docker build -t planet_ros_org .
docker run -v `pwd`:/planet planet_ros_org planet /planet --verbose /planet/planet.ini 
