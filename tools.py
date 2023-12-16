# pip install jmespath

import hashlib
import os
import json
import math

import aiohttp
import jmespath
import redis
import requests

import mylog
import socket
from datetime import datetime
from typing import Any


def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


QUEUE_THIEF_TASK='VideoSniffer:Thief_Task_Queue'
QUEUE_SEND_TEMPL='VideoSniffer:Send_Channel:{}'
SET_RES_INFO='VideoSniffer:Res_Info:{}'


HOST_REDIS='192.168.31.162'
PORT_REDIS=6378
HOST_IP=get_host_ip()

redis_pool=redis.ConnectionPool(host=('localhost')if(get_host_ip()==HOST_REDIS)else HOST_REDIS,port=PORT_REDIS,decode_responses=True,socket_connect_timeout=1,socket_keepalive=5,max_connections=10)

def get_redis():
    redis_conn = redis.Redis(connection_pool=redis_pool)
    return redis_conn

def get_logger():
    return mylog.get_logger()

def get_current_workdir():
    return os.getcwd()

class MyJsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o,datetime):
            return o.strftime('%Y%m%d%H%M%S')
        else:
            return super(MyJsonEncoder,self).default(o)


def json_to_obj(json_str,obj_class=None):
    data = json.loads(json_str.strip('\t\r\n'))
    if obj_class is None:
        return data
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
        if hasattr(obj,'__dict__'):
            json_str = json.dumps(obj.__dict__)
        else:
            json_str = json.dumps(obj)
        return json_str
    except Exception as e:
        get_logger().error(f'对象转JSON失败：{type(obj)}',exc_info=True)
        raise e


def filesize_exp(size:int)->str:
    file_size_mode = ['B', 'KB', 'MB', 'GB']
    file_size_str = f'{size}{file_size_mode[0]}'
    for i in range(1,len(file_size_mode)+1):
        size1=size/math.pow(1024,i)
        # print(i,size1)
        if size1<1:
            break
        size1=round(size1,1)
        file_size_str=f'{size1}{file_size_mode[i]}'
    return file_size_str


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

async def async_remote_file_info(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as resp:
            if resp.status in [200,206,304]:
                return {'content_type':resp.content_type,
                        'content_length':resp.content_length,
                        'content_disposition':resp.content_disposition,
                        'charset':resp.charset
                }
def remote_file_info(url):
    try:
        with requests.head(url) as resp:
            if resp.status_code in [200, 206, 304]:
                return {'Content-Type': resp.headers.get("Content-Type"),
                        'Content-Length': resp.headers.get("Content-Length"),
                        'Content-Disposition': resp.headers.get("Content-Disposition"),
                        'Charset': resp.headers.get("Charset")
                        }
    except Exception as e:
        get_logger().error(e,exc_info=True)



if __name__ == '__main__':
    print(get_host_ip())
    print(get_redis().info())