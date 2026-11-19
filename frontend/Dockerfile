# 前端镜像：Node 构建 → Nginx 托管静态文件并反代后端
FROM node:20-alpine AS build

WORKDIR /app

# 用国内 npm 源，否则依赖装到一半会卡死
RUN npm config set registry https://registry.npmmirror.com

# 先只拷依赖清单，利用 Docker 层缓存：代码改了不用重装依赖
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build


FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
