Reids:
1、Docker镜像-Redis
docker pull  redis:latest
docker run --name redis --restart=always -p 6378:6379 -v $PWD/redis_data:/data  -d redis:latest redis-server --appendonly yes

2、pip 依赖安装
