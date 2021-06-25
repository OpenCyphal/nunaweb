FROM python:3.9.1-slim
EXPOSE 8080
COPY / /nunaserver/
WORKDIR /nunaserver
RUN apt update
RUN apt install -y curl
RUN pip3 install -r requirements.txt
