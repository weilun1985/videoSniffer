import socket
import hashlib
import os
import json
import math

import aiohttp
import jmespath
import redis
import logging
import colorlog
import requests

from datetime import datetime
from typing import Any
from urllib.parse import urlparse,parse_qs

from models import VideoInfo,PictureInfo

CONTENT_TYPE_VIDEO=["video/mp4", "video/x-flv", "video/ogg", "video/webm", "video/quicktime", "video/x-ms-wmv", "video/mpeg", "video/3gpp", "video/x-m4v", "video/vnd.apple.mpegurl", "application/x-mpegURL","audio/mp4"]
CONTENT_TYPE_IMAGE=["image/jpeg", "image/png", "image/webp", "image/tiff", "image/bmp"]

SET_RES_INFO='VideoSniffer:Res_Info:{}'
WX_MSG_TYPE_MAP = {1: '[文本]', 3: '[图片]', 43: '[视频]', 49: '[链接]', 34: '[语音]', 10000: '[系统消息]', 47: '[表情包]', 492: '[链接]', 494: '[小程序]', 493: '[文件]'}
KEY_QUEUE_WXMSG_RECV='VideoSniffer:WeChat:{}:recv_queue'
KEY_QUEUE_WXMSG_SEND='VideoSniffer:WeChat:{}:send_queue'

HOST_REDIS='192.168.1.27'
PORT_REDIS=6378

def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def is_empty_str(instr:str):
    if instr is None:
        return True
    instr=instr.strip()
    if len(instr)==0:
        return True
    return False

__redis_pool=redis.ConnectionPool(host=('localhost')if(get_host_ip()==HOST_REDIS)else HOST_REDIS,port=PORT_REDIS,decode_responses=True,socket_connect_timeout=1,socket_keepalive=5,max_connections=10)

def get_redis():
    redis_conn = redis.Redis(connection_pool=__redis_pool)
    return redis_conn

__logger=None
def get_logger(level=logging.INFO):
    global __logger
    if __logger  is not None:
        return __logger
    logger=logging.getLogger()
    logger.setLevel(level)
    console_handler=logging.StreamHandler()
    console_handler.setLevel(level)

    color_formatter=colorlog.ColoredFormatter(
        fmt='%(asctime)s [%(name)s] [%(process)d] [%(thread)d] %(levelname)s - (%(module)s.%(funcName)s) -> %(message)s',
        log_colors={
            'DEBUG':'cyan',
            'INFO':'white',
            'WARNING':'yellow',
            'ERROR':'red',
            'CRITICAL':'red,bg_white'
        }
    )
    console_handler.setFormatter(color_formatter)
    # 移除默认的handler
    for handler in logger.handlers:
        logger.removeHandler(handler)
        # 将控制台日志处理器添加到logger对象
    logger.addHandler(console_handler)
    __logger=logger
    return logger

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

def wx_msg_tostring(msg):
    if msg:
        msg_type_str=msg.get("msg_type_str")
        content=msg.get("content")
        ll=300
        if msg_type_str and len(content)>ll:
            content=content[0:ll]+'...'
        str=f'sender={msg.get("sender")} type={msg.get("type")} msg_type={msg.get("msg_type")}/{msg.get("msg_type_str")}  is_chat_room={msg.get("is_chatroom")} is_at_me={msg.get("at_me")} msg_id={msg.get("msg_id")}  is_self_msg={msg.get("is_self_msg")} wx_id={msg.get("wx_id")} self_wx_id={msg.get("self_wx_id")} \r\n{content}'
        return str

def md5_str(instr:str):
    data=instr.encode()
    md5 = hashlib.md5()
    md5.update(data)
    md5str=md5.hexdigest()
    return md5str

def get_url_query_value(url,key):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    param_arr=query_params.get(key,[])
    param_value=None
    if param_arr and len(param_arr)>0:
        param_value = param_arr[0]
    return param_value

def res_info_stringfy(res_info):
    if res_info is None:
        return
    str=f'资源ID：{res_info.id}'
    str+=f'\r\n资源类型：{type(res_info).__name__}'
    if hasattr(res_info,'name'):
        str += f'\r\n资源名称：{res_info.name}'
    if hasattr(res_info, 'content'):
        str += f'\r\n资源描述：{res_info.content}'
    str+=f'\r\n分享URL：{res_info.share_url}'
    str+=f'\r\n资源数量：{1 if isinstance(res_info,VideoInfo) else len(res_info.res_url_list)}'
    if isinstance(res_info,VideoInfo):
        str+=f'\r\n\t1. {res_info.res_url}'
    else:
        for index,url in enumerate(res_info.res_url_list):
            str+=f'\r\n\t{index}. {url}'
    return str
