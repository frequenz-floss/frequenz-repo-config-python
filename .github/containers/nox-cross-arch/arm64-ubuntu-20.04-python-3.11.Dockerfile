# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

# This Dockerfile is used to test the installation of the python package in
# multiple platforms in the CI. It is not used to build the package itself.

FROM docker.io/library/ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11 and curl to install pip later
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
        software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get install --no-install-recommends -y \
        ca-certificates \
        curl \
        git \
        python3.11 \
        python3.11-distutils \
        python3.11-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Link python3.11 to python and python3.
# This is needed because we want users of this image to use python3.11 as the
# default python version.
RUN update-alternatives --install \
        /usr/local/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install \
        /usr/local/bin/python3 python3 /usr/bin/python3.11 1 && \
    python -m pip install --upgrade --no-cache-dir pip

COPY entrypoint.bash /usr/bin/entrypoint.bash

ENTRYPOINT ["/usr/bin/entrypoint.bash"]
