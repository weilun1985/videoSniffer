# pip install jmespath

import hashlib
import json
import math
import jmespath
import redis
import mylog
from datetime import datetime
from typing import Any



QUEUE_THIEF_TASK='VideoSniffer:Thief_Task_Queue'
QUEUE_SEND_TEMPL='VideoSniffer:Send_Channel:{}'
SET_RES_INFO='VideoSniffer:Res_Info:{}'

redis_pool=redis.ConnectionPool(host='192.168.31.162',port='6378',decode_responses=True,socket_connect_timeout=1,socket_keepalive=5,max_connections=10)

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
        if not isinstance(obj, type) and not isinstance(obj, dict):
            json_str=json.dumps(obj)
        else:
            json_str=json.dumps(obj.__dict__)
        return json_str
    except Exception as e:
        get_logger().error(f'对象转JSON失败：{type(obj)}',exc_info=True)
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