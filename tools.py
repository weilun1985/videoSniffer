# pip install jmespath

import hashlib
import json
import math
import jmespath
import redis
import win32clipboard
import win32process
import win32gui
import win32api
import win32con
import time,os
import mylog
import time
from datetime import datetime
from typing import Any



QUEUE_THIEF_TASK='VideoSniffer:Thief_Task_Queue'
QUEUE_SEND_TEMPL='VideoSniffer:Send_Channel:%s'

redis_pool=redis.ConnectionPool(host='localhost',port='6379',decode_responses=True)

def get_redis():
    redis_conn = redis.Redis(connection_pool=redis_pool)
    return redis_conn

def get_logger():
    return mylog.get_logger()

class MyJsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o,datetime):
            return o.strftime('%Y%m%d%H%M%S')
        else:
            return super(MyJsonEncoder,self).default(o)


def json_to_obj(json_str,obj_class):
    data = json.loads(json_str.strip('\t\r\n'))
    obj=obj_class()
    obj.__dict__=data
    return obj

def simpleTimeStr(t:datetime):
    if t is None:
        return None
    return t.strftime('%Y%m%d%H%M%S')

def obj_to_json(obj)->str:
    if obj is None:
        return
    try:
        json_str=json.dumps(obj.__dict__)
        return json_str
    except Exception as e:
        print(obj.__dict__)
        get_logger().error(obj.__dict__)
        raise e


def filesize_exp(size:int)->str:
    file_size_mode = ['B', 'KB', 'MB', 'GB']
    file_size_str = f'{size}{file_size_mode[0]}'
    for i in range(1,len(file_size_mode)+1):
        size1=size/math.pow(1024,i)
        print(i,size1)
        if size1<1:
            break
        size1=round(size1,1)
        file_size_str=f'{size1}{file_size_mode[i]}'
    return file_size_str




def aa():
    redis=get_redis()
    redis.lpush()
    redis.rpop()

from ctypes import (
    Structure,
    c_uint,
    c_long,
    c_int,
    c_bool,
    sizeof
)
class DROPFILES(Structure):
    _fields_ = [
    ("pFiles", c_uint),
    ("x", c_long),
    ("y", c_long),
    ("fNC", c_int),
    ("fWide", c_bool),
    ]
pDropFiles = DROPFILES()
pDropFiles.pFiles = sizeof(DROPFILES)
pDropFiles.fWide = True
matedata = bytes(pDropFiles)

def setClipboardText(text):
    t0 = time.time()
    while True:
        if time.time() - t0 > 10:
            raise TimeoutError(f"设置剪贴板超时！ --> {text}")
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            break
        except:
            pass
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

def setClipboardFiles(paths):
    for file in paths:
        if not os.path.exists(file):
            raise FileNotFoundError(f"file ({file}) not exists!")
    files = ("\0".join(paths)).replace("/", "\\")
    data = files.encode("U16")[2:]+b"\0\0"
    t0 = time.time()
    while True:
        if time.time() - t0 > 10:
            raise TimeoutError(f"设置剪贴板文件超时！ --> {paths}")
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_HDROP, matedata+data)
            break
        except:
            pass
        finally:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

def md5_str(instr:str):
    data=instr.encode()
    md5 = hashlib.md5()
    md5.update(data)
    md5str=md5.hexdigest()
    return md5str

def json_select(query,data):
    result=jmespath.search(query,data)
    return result

def is_empty_str(instr:str):
    if str is None:
        return True
    instr=instr.strip()
    if len(instr)==0:
        return True
    return False

def not_empty_str(instr:str):
    return not is_empty_str(instr)