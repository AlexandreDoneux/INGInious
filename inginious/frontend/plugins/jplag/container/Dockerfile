# DOCKER-VERSION 1.1.0

# usage outside of INGInious :
# Create a .zip file containing one directory per student, each containing the student's submission. The .zip file should be named "submissions.zip".
# Then, run the container with the following command :
#
# docker run  -v "$(pwd)/test_submissions.zip":/jplag/input/submissions.zip -e JPLAG_LANGUAGE=python3
# --entrypoint /bin/bash  jplag:latest  -c "python3 /course/run.py"
#
# The mock is necessary to avoid import errors, as the container expects to be run in an INGInious environment.


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


COPY run.py /course/run.py
