FROM nginx:1.27-alpine

ARG API_UPSTREAM=http://mysql-backend:5000

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY templates/ /usr/share/nginx/html/
COPY static/ /usr/share/nginx/html/static/
COPY config.js /usr/share/nginx/html/config.js

RUN sed -i "s|__API_UPSTREAM__|${API_UPSTREAM}|g" /etc/nginx/conf.d/default.conf

EXPOSE 80
