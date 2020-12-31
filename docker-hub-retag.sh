#!/bin/bash
docker pull gcr.io/core-iot-sensors/rpifocus-webapp:1.0.0
docker tag gcr.io/core-iot-sensors/rpifocus-webapp:1.0.0 lemariva/rpifocus-webapp:1.0.0

docker pull gcr.io/core-iot-sensors/rpifocus-backend:1.0.0
docker tag gcr.io/core-iot-sensors/rpifocus-backend:1.0.0 lemariva/rpifocus-backend:1.0.0

docker pull gcr.io/core-iot-sensors/rpifocus-objdetector:1.0.0
docker tag gcr.io/core-iot-sensors/rpifocus-objdetector:1.0.0 lemariva/rpifocus-objdetector:1.0.0

docker pull gcr.io/core-iot-sensors/rpifocus-photoservice:1.0.0
docker tag gcr.io/core-iot-sensors/rpifocus-photoservice:1.0.0 lemariva/rpifocus-photoservice:1.0.0

docker push lemariva/rpifocus-webapp:1.0.0 
docker push lemariva/rpifocus-backend:1.0.0 
docker push lemariva/rpifocus-objdetector:1.0.0 
docker push lemariva/rpifocus-photoservice:1.0.0