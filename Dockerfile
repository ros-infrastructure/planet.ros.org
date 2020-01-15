FROM debian:buster

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
            planet-venus \
            xsltproc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD planet --verbose /planet /planet/planet.ini