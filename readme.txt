Reids:
1、Docker镜像-Redis
docker pull  redis:latest
docker run --name redis --restart=always -p 6378:6379 -v $PWD/redis_data:/data  -d redis:latest redis-server --appendonly yes

2、pip 依赖安装
国内镜像源：pip config set global.index-url --site https://pypi.tuna.tsinghua.edu.cn/simple
配置文件：
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
[install]
trusted-host = https://pypi.tuna.tsinghua.edu.cn

1）scanic 相关：
# pip3 install sanic
# pip3 install sanic.ext
# pip3 install sanic-jinja2
# pip3 install sanic_cors
# pip install jmespath
# pip install redis
# pip install colorlog

2）playWright相关：
# pip install playwright
# playwright install

3、运行webApp:
nohup python application.py &
tail -f nohup.out



