Reids:
1、Docker镜像-Redis
docker pull  redis:latest
docker run --name redis --restart=always -p 6378:6379 -v $PWD/redis_data:/data  -d redis:latest redis-server --appendonly yes

2、pip 依赖安装
1）scanic 相关：
# pip3 install sanic
# pip3 install sanic.ext
# pip3 install sanic-jinja2
# pip3 install sanic_cors

2）playWright相关：

