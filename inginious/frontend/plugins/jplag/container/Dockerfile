# DOCKER-VERSION 1.1.0

#inherit from the base container, which have all the needed script to launch tasks
ARG   VERSION=latest
ARG   REGISTRY=ghcr.io
FROM  ${REGISTRY}/inginious/env-base:${VERSION}

LABEL org.opencontainers.image.source=https://github.com/INGInious/containers
LABEL org.opencontainers.image.description="Single test JPLAG job environment"

LABEL org.inginious.grading.name="jplag"


# Install Java SE 21
RUN dnf clean metadata && \
    dnf -y upgrade && \
    dnf -y install java-21-openjdk-headless


# JPLAG 6.2.0, last version compatible with java 21
ENV JPLAG_VERSION=6.2.0
ENV JPLAG_JAR=/opt/jplag/jplag-${JPLAG_VERSION}-jar-with-dependencies.jar

RUN mkdir -p /opt/jplag && \
    curl -L -o "${JPLAG_JAR}" \
    "https://github.com/jplag/JPlag/releases/download/v${JPLAG_VERSION}/jplag-${JPLAG_VERSION}-jar-with-dependencies.jar"


# Create required directories for jplag
RUN mkdir -p soumissions static/result templates


COPY run.py /course/run.py
