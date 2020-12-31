# Autofocus for the 16mm telephoto lens mounted on a Raspberry Pi HQ Camera.
As you may have already noticed, the Raspberry Pi HQ Camera lenses don't have any autofocus functionality. This project includes the hardware design, firmware and software to add autofocus functionality to those lenses. In this case, I use the 16mm telephoto lens.
The project is divided into two repositories. This repository includes the code of the Microservice application, whereas [lemariva/uPyFocus](https://github.com/lemariva/uPyFocus) includes the firmware for the M5Stack that controls the motors to rotate the Lens focus and aperture.

A detailed article about the application can be found on [Raspberry Pi HQ Camera: Autofocus for the Telephoto Lens (JiJi)](https://lemariva.com/blog/2020/12/raspberry-pi-hq-camera-autofocus-telephoto-lens).

## Video
[![Autofocus for the Raspberry HQ Camera](https://img.youtube.com/vi/PrbyPmq_Z7Q/0.jpg)](https://www.youtube.com/watch?v=PrbyPmq_Z7Q)

## Photo examples
|          |          |          |          |
|:--------:|:--------:|:--------:|:--------:|
|<img src="https://lemariva.com/storage/app/uploads/public/5fe/c63/443/5fec63443a76c981023585.jpg" alt="Focus Type: Box - Background focused" width="300px">|<img src="https://lemariva.com/storage/app/uploads/public/5fe/c63/392/5fec6339224b0320000410.jpg" alt="Focus Type: Box - Nanoblock bird focused" width="300px">|<img src="https://lemariva.com/storage/app/uploads/public/5fe/c63/4ab/5fec634ab3092068212455.jpg" alt="Focus Type: Box - Nanoblock bird focused. Diff. illum & cam. aperture" width="300px">|<img src="https://lemariva.com/storage/app/uploads/public/5fe/c63/3cd/5fec633cda6af591369087.jpg" alt="Focus Type: Object detector - Teddy bear focused" width="300px">|
|Focus Type: Box <br/> Background focused (<a href="https://lemariva.com/storage/app/media/blog_imgs/hqcamera/hq_camera_background_focused.jpg">download</a>)|Focus Type: Box <br/>Nanoblock bird focused (<a href="https://lemariva.com/storage/app/media/blog_imgs/hqcamera/hq_camera_nanoblock_bird_focused.jpg">download</a>)|Focus Type: Box <br/>Nanoblock bird focused. <br/> Diff. illum & cam. aperture (<a href="https://lemariva.com/storage/app/media/blog_imgs/hqcamera/hq_camera_nanoblock_bird_focused_2.jpg">download</a>)|Focus Type: Object detector  <br/>Teddy bear focused (<a href="https://lemariva.com/storage/app/media/blog_imgs/hqcamera/hq_camera_teddy_bear_focused.jpg">download</a>)|

## Simple PCB schematic
Inside the folder `pcb`, you'll find the board design and schematic files (Eagle), to order the PCB. I added also the Gerber files that I used by <a rel="noopener noreferrer" href="https://jlcpcb.com/">jlcpcb</a>.

|          |
|:--------:|
|<img src="https://lemariva.com/storage/temp/public/625/29e/b52/5feca3f70da50778861950__899.jpg" alt="Simple PCB schematic." width="400px">|
|Simple PCB schematic.|

## Start the Microservices Application
The application that runs on the Raspberry Pi is a Microservices application. That means different services are orchestrated to offer an application. The orchestration is performed by docker-compose and the services are containerized using Docker.

To install Docker and `docker-compose` on the Raspberry Pi, type the following on a Terminal:
```
# Docker
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker pi

# docker-compose
sudo pip3 -v install docker-compose

# usually you need these dependencies
sudo apt-get install -y libffi-dev libssl-dev
sudo apt-get install -y python3 python3-pip
sudo apt-get remove python-configparser
```

The services of the microservices application are the following:
* **webapp**: it provides the frontend application (webserver). It is programmed in Angular.
* **backend**: it communicates with the frontend via a RestAPI (Flask server), controls the camera, sends the signals to the M5Stack to control the motors, sends the signals and data to the other services to identify objects and take photos. Basically, it is the core service. It is programmed in Python.
* **obj-detector**: it receives an image over UDP and identifies the object on it and returns a JSON message. It is programmed in Python. It uses TensorFlow and connects to the Coral USB Accelerator to process the data in real-time.
* **photo-service**: it receives a signal via RestAPI (Flask server) to take photos and it processes them to create HDR photos. It is programmed in Python and it uses Celery for multitasking/non-blocking response to the RestAPI.
* **redis**: Celery uses this service to schedule the tasks.

To start the Microservices application, follow these steps:
1. Download the `docker-compose.yml` file or just clone the complete [lemariva/rPIFocus](https://github.com/lemariva/rPIFocus) repository:
    ```sh
    git clone https://github.com/lemariva/rPIFocus.git
    ```
2. Open the `docker-compose.yml` file and change the `HOST_M5STACK=<ip-address>` with the IP of your M5Stack.
3. Start the application by typing inside the `rPiFocus` folder:
    ```sh
    docker-compose up -d
    ```
4. Open a browser and visit the URL address: `http://<ip-raspberrypi>:4200`, you'll see an interface like in the figure below. ( shhh... I've just noticed that I wrote Raspberry HD camera and not HQ camera... :( )
5. To stop the application, type:
    ```sh
    docker-compose down
    ```

|           |
|:---------:|
|<img src="https://lemariva.com/storage/app/uploads/public/5fe/c60/ad0/5fec60ad052fc228241834.jpg" alt="Webservice Microservices Application">|
|Webservice Microservices Application|


## Build containers
The Docker images can be built by typing e.g.:
```sh
docker build -t <your-docker-hub-name>/rpifocus-webapp:1.0.0 webapp
```
Then, if you are logged in into Docker Hub, you can push the image by typing:
```sh
docker push <your-docker-hub-name>/webapp
# read this tutorial: https://docs.docker.com/docker-hub/access-tokens/#create-an-access-token for login
```

Then, you need to edit the image names inside the `docker-compose.yml` and start the microservices application again (`docker-compose down` and then `docker-compose up -d`).

Additionally, I included a `cloudbuild.yaml` file inside each folder. This can be used to build those images using Google Cloud Build. In this article: [M5Stack: Fresh air checker can help you to stay safe from #COVID-19](https://lemariva.com/blog/2020/11/m5stack-fresh-air-helps-stay-safe-from-covid-19), you can find an example of how to do that!

## License
* GNU General Public License v3.0