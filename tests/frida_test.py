import frida
from datetime import datetime
import subprocess,sys

subprocess.getoutput("adb forward tcp:27042 tcp:27042")
subprocess.getoutput("adb forward tcp:27043 tcp:27043")


# 获取设备信息
rdev=frida.get_remote_device()
print(rdev)

def list_process():
    # 枚举所有的进程
    processes = rdev.enumerate_processes()
    for process in processes:
        print(process)
    print('------------------')
    print('')

def list_app():
    # 获取在前台运行的APP
    front_app = rdev.get_frontmost_application()
    print(front_app)


def attch_script():
    with open('frida_test_js.js', 'r',encoding='utf-8') as f:
        script_source = f.read()

    pid = rdev.spawn(["com.tencent.mm"])
    print(pid)
    session = rdev.attach(pid)
    try:
        # 创建并加载Frida脚本
        script = session.create_script(script_source)
        # 加载并执行脚本
        script.load()
        # 等待脚本运行或者进行其他交互（例如监听事件）

    finally:
        script.unload()
        # 关闭会话
        session.detach()



if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    list_process()
    list_app()
    attch_script()
    pass