FROM node:slim
EXPOSE 8080
COPY . /nunaweb
WORKDIR /nunaweb
ENV API_URL="https://nunaweb.uavcan.org/api/"
RUN npm install
RUN npm run build
RUN npm run generate
