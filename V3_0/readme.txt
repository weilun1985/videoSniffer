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
单次：pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

1）scanic 相关：
# pip3 install sanic
# pip3 install sanic.ext
# pip3 install sanic-jinja2
# pip3 install sanic_cors
# pip install jmespath
# pip install redis
# pip install colorlog
# pip install aioredis -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip install aiofiles -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip install aiohttp -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip install charset_normalizer
# pip install urllib3
# pip install certifi
# pip install sanic websockets
# pip install websockets -i https://pypi.tuna.tsinghua.edu.cn/simple


2）playWright相关：
# pip install playwright  -i https://pypi.tuna.tsinghua.edu.cn/simple
# playwright install

3) RPA相关
# pip install pyautogui  -i https://pypi.tuna.tsinghua.edu.cn/simple
# pip install PyOfficeRobot  -i https://pypi.tuna.tsinghua.edu.cn/simple

4) frida
https://github.com/frida/frida/releases

pip install frida -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install frida-tools -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install objection -i https://pypi.tuna.tsinghua.edu.cn/simple

adb connect 127.0.0.1:16480
adb shell getprop ro.product.cpu.abi
https://github.com/frida/frida/releases?q=16.1.10-and&expanded=true 下载 frida-server-16.1.10-android-x86_64.xz

adb shell
SM-S9080:/ $ su
SM-S9080:/ # su
SM-S9080:/ # cd /data/local/tmp
SM-S9080:/data/local/tmp # ls
fridas16_1_10
SM-S9080:/data/local/tmp # ./fridas16_1_10

adb forward tcp:27042 tcp:27042
adb forward tcp:27043 tcp:27043

HOOK微信：
objection -g com.tencent.mm explore

5) 修改ro.debuggable用于调试安卓应用
查看当前是否可以调试：adb shell getprop ro.debuggable
下载该模块MagiskHide Props Config
在Magisk的模块中选择本地安装,找到该安装包,安装后重启手机即可
adb shell运行props
   选择3-Edit MagiskHide props




3、运行webApp:
nohup python webServer.py &
tail -f nohup.out
查进程： ps -ef | grep python
杀进程：

自媒体人的素材好助手，去水印视频/图片下载工具，支持各大主流媒体平台无水印素材获取：小红书/快手/抖音/视频号/百度/微博……具体使用方法请查看我的朋友圈。



