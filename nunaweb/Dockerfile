FROM node:16
EXPOSE 8080
COPY . /nunaweb
WORKDIR /nunaweb
ENV API_URL="https://nunaweb.opencyphal.org/api/"
RUN apt-get update && apt-get install -y curl
RUN npm install
RUN npm run build
RUN npm run generate
