FROM node:slim
EXPOSE 80
COPY . /nunaweb
WORKDIR /nunaweb
ENV API_URL="http://192.168.128.29/api/"
RUN npm install
RUN npm run build
RUN npm run generate
