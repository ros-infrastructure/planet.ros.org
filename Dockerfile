FROM debian:buster

# Enable old buster snapshot
RUN sed -i '/deb\.debian/d; s/^# //' /etc/apt/sources.list

RUN apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get install -y --no-install-recommends \
            planet-venus \
            xsltproc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD planet --verbose /planet /planet/planet.ini
