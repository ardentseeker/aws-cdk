FROM public.ecr.aws/nginx/nginx:1.25.2-alpine-slim
COPY index.html /usr/share/nginx/html/index.html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
ENTRYPOINT [ "nginx", "-g", "daemon off;" ]
