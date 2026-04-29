# DOCKER-VERSION 1.1.0

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


# JPlag 6.2.0, last version compatible with Java 21
ENV JPLAG_VERSION=6.2.0
ENV JPLAG_JAR=/opt/jplag/jplag-${JPLAG_VERSION}-jar-with-dependencies.jar

RUN mkdir -p /opt/jplag && \
    curl -L -o "${JPLAG_JAR}" \
    "https://github.com/jplag/JPlag/releases/download/v${JPLAG_VERSION}/jplag-${JPLAG_VERSION}-jar-with-dependencies.jar"


RUN mkdir -p /jplag/input /jplag/submissions /jplag/result /jplag/basecode && \
    chmod -R 777 /jplag

# Default language for the moment; override at runtime with -e JPLAG_LANGUAGE=...
ENV JPLAG_LANGUAGE=python3
ENV JPLAG_SUBMISSIONS_ZIP=/jplag/input/submissions.zip


COPY run.py /course/run.py
COPY test_submissions.zip /jplag/input/submissions.zip
