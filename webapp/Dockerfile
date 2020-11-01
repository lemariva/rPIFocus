FROM balenalib/raspberrypi3-debian:buster
RUN [ "cross-build-start" ]

ARG MAYOR_REVISION
ARG MINOR_REVISION
ARG BUILD_ID

#labeling
LABEL org.label-schema.name="rPIFocus" \
    org.label-schema.description="Docker running Webservice application to control Raspberry Pi HD Camera" \
    org.label-schema.url="https://lemariva.com" \
    org.label-schema.vcs-url="https://github.com/lemariva/rPIFocus" \
    org.label-schema.vendor="LeMaRiva|Tech info@lemariva.com" \
    org.label-schema.version="${MAYOR_REVISION}.${MINOR_REVISION}.${BUILD_ID}"

RUN curl -sL https://deb.nodesource.com/setup_12.x | sudo bash - \
    && apt-get update \
    && apt install nodejs

RUN mkdir -p /root/webapp/
WORKDIR /root/webapp

COPY ./app /root/webapp
RUN npm install

RUN ln -s /root/webapp/node_modules/.bin/ng /usr/bin/ng
RUN ng build

CMD [ "ng", "serve", "--host", "0.0.0.0" ]

EXPOSE 4200

#set stop signal
STOPSIGNAL SIGTERM

RUN [ "cross-build-end" ]

