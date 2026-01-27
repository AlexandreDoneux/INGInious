# DOCKER-VERSION 1.1.0

#inherit from the base container, which have all the needed script to launch tasks
ARG   VERSION=latest
ARG   REGISTRY=ghcr.io
FROM  ${REGISTRY}/inginious/env-base:${VERSION}

LABEL org.opencontainers.image.source=https://github.com/INGInious/containers
LABEL org.opencontainers.image.description="Single test JPLAG job environment"

LABEL org.inginious.grading.name="jplag"

#RUN /bin/sh -c pip3.8 install debugpy pydevd-pycharm~=253.30387.127 # does not work ...
#RUN python3 -m pip install debugpy pydevd-pycharm~=253.30387.127

# Force stdin, stdout and stderr to be totally unbuffered
ENV PYTHONUNBUFFERED=1

COPY run /course/run
RUN chmod +x /course/run