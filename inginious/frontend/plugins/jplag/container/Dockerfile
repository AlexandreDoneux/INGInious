# DOCKER-VERSION 1.1.0

# Environment variables for the JPLAG environment
# JPLAG_LANGUAGE (required) : The programming language to be used for the plagiarism detection. Supported values are available at https://github.com/jplag/JPlag. Be aware of the version used.
# SIM_THRESHOLD : The similarity threshold for the plagiarism detection. Default is 0 (0% similarity).


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
COPY test_submissions.zip /jplag/input/submissions.zip
