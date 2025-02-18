FROM nginx:latest
EXPOSE 443
COPY nginx.conf                   /etc/nginx/conf.d/default.conf
COPY nginx_nunaweb_locations.conf /etc/nginx/conf.d/nginx_nunaweb_locations.conf
WORKDIR /
