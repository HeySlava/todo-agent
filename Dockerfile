FROM python:3.11-slim-bullseye

WORKDIR /opt

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/list/*

ENV PATH=/venv/bin:$PATH

COPY ./setup.py ./setup.cfg ./
COPY ./agent ./agent

RUN :\
    && python -m venv /venv \
    && pip install --no-cache-dir pip -U wheel setuptools . \
    && :

CMD ["run_agent"]
