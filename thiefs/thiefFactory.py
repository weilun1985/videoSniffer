import os
import importlib
import inspect
import re
import typing
from inspect import isclass
from datetime import datetime
from thiefs.thiefBase import ThiefBase
from thiefs.general import General
from thiefs.ttt import TTT

def get_classes_in_package():
    package_name='thiefs'
    classes = set()
    # 获取包的绝对路径
    package_path = os.path.dirname(importlib.import_module(package_name).__file__)
    print('package_path:',package_path)
    for root, dirs, files in os.walk(package_path):
        for file in files:
            # 只处理.py文件
            if file.endswith('.py') and not file.startswith('__init__'):
                module_name = file[:-3]  # 去掉.py后缀得到模块名

                if root != package_path:
                    module_name = os.path.relpath(root, package_path).replace(os.sep, '.') + '.' + module_name
                print('\tmodule_name:', module_name)
                try:
                    # 导入模块
                    module = importlib.import_module(module_name, package=package_name)
                    for name, obj in inspect.getmembers(module, isclass):
                        print('\t\tname:', name)
                        # 添加不是内置或内部类的类
                        if obj.__module__.startswith(module_name) and not (name.startswith('_') or hasattr(obj, '__module__',) and obj.__module__.startswith('builtins')):
                            classes.add(obj)
                except Exception as e:
                    print(f"Failed to import module {module_name}: {e}")

    return classes

def get_thief(shareObj,trigger_time):
    url,host,shared_text=ThiefBase.analyzing(shareObj)
    if not url:
        return False,None
    thief=TTT(shareObj,url,trigger_time)

    # thief= General(shareObj,url,trigger_time)
    # if host in ['xhslink.com', 'www.xiaohongshu.com']:
    #     thief = Xhs(shareObj,url,trigger_time)
    # elif host == 'v.douyin.com':
    #     pass
    # elif host == 'mbd.baidu.com':
    #     thief=Baidu(url)
    return True,thief


if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
