FROM balenalib/raspberrypi3-debian:buster
RUN [ "cross-build-start" ]

ARG MAYOR_REVISION
ARG MINOR_REVISION
ARG BUILD_ID

#labeling
LABEL org.label-schema.name="rPIFocus" \
    org.label-schema.description="Docker running object detector application for the Raspberry Pi HD Camera" \
    org.label-schema.url="https://lemariva.com" \
    org.label-schema.vcs-url="https://github.com/lemariva/rPIFocus" \
    org.label-schema.vendor="LeMaRiva|Tech info@lemariva.com" \
    org.label-schema.version="${MAYOR_REVISION}.${MINOR_REVISION}.${BUILD_ID}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget git python3-dev python3-pip python3-setuptools python3-wheel \
    python3-numpy python3-zmq libhdf5-dev libhdf5-serial-dev libhdf5-103 libqtgui4 libqtwebkit4 libqt4-test \
    python3-pyqt5 python3-pil build-essential feh pkg-config libjpeg-dev zlib1g-dev libssl-dev libffi-dev \
    libraspberrypi0 libraspberrypi-dev libraspberrypi-bin libfreetype6-dev libxml2  libopenjp2-7 libatlas-base-dev \
    libjasper-dev libopenexr-dev libilmbase23 libqtgui4 libqt4-test libavformat-dev libswscale-dev libavcodec-dev libv4l-dev
    
RUN python3 -m pip install --upgrade pip

COPY ./app/requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

RUN echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list \
    && echo "deb https://packages.cloud.google.com/apt coral-cloud-stable main" | sudo tee /etc/apt/sources.list.d/coral-cloud.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add - \
    && apt-get update \
    && apt-get install -y python3-pycoral python3-tflite-runtime

RUN mkdir /root/app 
WORKDIR /root/app

COPY ./app /root/app

#copy supervisord files
COPY "./conf/supervisord.conf" /etc/supervisor/conf.d/supervisord.conf
RUN mkdir /var/log/supervisord/

RUN apt-get autoremove \
    && rm -rf /tmp/* \
    && rm -rf /var/lib/apt/lists/*

#supervisord
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

EXPOSE 8010

STOPSIGNAL SIGTERM

RUN [ "cross-build-end" ]