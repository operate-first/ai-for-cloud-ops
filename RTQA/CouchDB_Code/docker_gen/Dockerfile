# syntax=docker/dockerfile:1

FROM python:3.10.5-bullseye
WORKDIR /praxi
COPY . .

RUN python -m pip install --upgrade pip
RUN pip install pip
RUN pip install safety-db PyYAML envoy tqdm watchdog numpy
CMD sleep 10000