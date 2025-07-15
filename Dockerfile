FROM debian:buster

# Enable old buster snapshot
RUN grep -v deb.debian /etc/apt/sources.list | sed 's/# //' > /etc/apt/sources.list

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
            planet-venus \
            xsltproc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

CMD planet --verbose /planet /planet/planet.ini
