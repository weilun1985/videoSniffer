import json
import math

import redis
import win32clipboard
import win32process
import win32gui
import win32api
import win32con
import time,os


QUEUE_THIEF_TASK='VideoSniffer:Thief_Task_Queue'
QUEUE_WECHAT_SEND='VideoSniffer:WeChat_Send_Queue'
QUEUE_MAILBOX_SEND='VideoSniffer:Mail_Send_Queue'

redis_pool=redis.ConnectionPool(host='localhost',port='6379')

def json_to_obj(json_str,obj_class):
    data = json.loads(json_str.strip('\t\r\n'))
    obj=obj_class()
    obj.__dict__=data
    return obj

def obj_to_json(obj)->str:
    json_str=json.dumps(obj.__dict__)
    return json_str

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