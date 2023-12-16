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

# 文本平衡组
def tt(text:str,lc:str,rc:str)->str:
    m,n,d,s=0,0,0,0
    for c in text:
        if c==lc:
            m+=1
            d+=1
        elif c==rc:
            m-=1
        if d==0:
            s+=1
        n+=1
        if d>0 and m==0:
            break
    return text[s:n]


if __name__ == '__main__':
    text="""window.jsonData = {"author":{"vip":0,"name":"\u8bf8\u845b\u521b\u4e1a\u6709\u4e00\u624b\u54e6","icon":"https:\/\/gips0.baidu.com\/it\/u=1932806834,3795904896&fm=3012&app=3012&autime=1702351163&size=b200,200","third_id":"1782058845727037","authentication_content":"\u751f\u547d\u4e2d\u6ca1\u6709\u56db\u65f6\u4e0d\u53d8\u7684\u98ce\u666f\uff0c\u53ea\u8981\u5fc3\u6c38\u8fdc\u671d\u7740\u9633\u5149\uff0c\u4f60\u5c31\u4f1a\u53d1\u73b0\uff0c\u6bcf\u4e00\u675f\u9633\u5149\u90fd\u95ea\u7740\u5e0c\u671b\u7684\u5149\u8292\u3002","uk":"9uSz-fzJ9uX7HwnDe49ioA","type":"media","isFollow":"0","fansNum":5316},"favourite":{"is_favourite":"0"},"like":{"is_like":"0","count":"27788"},"playCount":"212570","curVideoMeta":{"id":"4879939042257911735","title":"\u4f60\u8fde\u6bdb\u5229\u7387\u90fd\u4e0d\u4f1a\u7b97\u7684\u8bdd\uff0c\u5c31\u4e0d\u8981\u5f00\u5e97\u4e86","thread_id":"1011000061995065","publish_time":1702089509,"duration":211,"6s_play_url":null,"playurl":"https:\/\/vd4.bdstatic.com\/mda-pm833x8j2n4bzt09\/720p_frame30\/h264_cae_acd\/1702098158625665451\/mda-pm833x8j2n4bzt09.mp4?v_from_s=bdapp-resbox-zan-hna","clarityUrl":[{"key":"sd","rank":0,"title":"\u6807\u6e05","url":"https:\/\/vd4.bdstatic.com\/mda-pm833x8j2n4bzt09\/540p\/h264_cae_acd\/1702098158388729548\/mda-pm833x8j2n4bzt09.mp4?v_from_s=bdapp-resbox-zan-hna","videoBps":1512,"vodVideoHW":"960$$540","videoSize":39,"vodMoovSize":105845},{"key":"sc","rank":2,"title":"\u8d85\u6e05","url":"https:\/\/vd4.bdstatic.com\/mda-pm833x8j2n4bzt09\/720p_frame30\/h264_cae_acd\/1702098158625665451\/mda-pm833x8j2n4bzt09.mp4?v_from_s=bdapp-resbox-zan-hna","videoBps":1918,"vodVideoHW":"1280$$720","videoSize":49.4,"vodMoovSize":105644},{"key":"1080p","rank":3,"title":"\u84dd\u5149","url":"https:\/\/vd4.bdstatic.com\/mda-pm833x8j2n4bzt09\/1080p\/h264_cae\/1702088014736793668\/mda-pm833x8j2n4bzt09.mp4?v_from_s=bdapp-resbox-zan-hna","videoBps":3906,"vodVideoHW":"1920$$1080","videoSize":100.6}]},"is_forbidden_share":0,"hidedislike":0,"header":{"title":"\u4f60\u8fde\u6bdb\u5229\u7387\u90fd\u4e0d\u4f1a\u7b97\u7684\u8bdd\uff0c\u5c31\u4e0d\u8981\u5f00\u5e97\u4e86","keywords":"\u6bdb\u5229\u7387","description":"\u4f60\u8fde\u6bdb\u5229\u7387\u90fd\u4e0d\u4f1a\u7b97\u7684\u8bdd\uff0c\u5c31\u4e0d\u8981\u5f00\u5e97\u4e86"},"cmd":"baiduboxapp:\/\/video\/invokeVideoDetail?params=%7B%22vid%22%3A%224879939042257911735%22%2C%22pd%22%3A%22feed%22%2C%22tpl%22%3A%22flowfeed%22%2C%22page%22%3A%22feed_video_landing%22%2C%22title%22%3A%22%5Cu4f60%5Cu8fde%5Cu6bdb%5Cu5229%5Cu7387%5Cu90fd%5Cu4e0d%5Cu4f1a%5Cu7b97%5Cu7684%5Cu8bdd%5Cuff0c%5Cu5c31%5Cu4e0d%5Cu8981%5Cu5f00%5Cu5e97%5Cu4e86%22%2C%22nid%22%3A%22sv_4879939042257911735%22%2C%22from%22%3A%22feed%22%2C%22extRequest%22%3A%7B%22resourceType%22%3A%22miniVideo%22%2C%22is_microvideo%22%3A1%7D%2C%22ext%22%3A%7B%22videoWidth%22%3A540%2C%22videoHeight%22%3A960%2C%22resourceType%22%3A%22miniVideo%22%7D%7D"};window.__firstPerformance = performance.now();</script><script>window.whiteScreenUgcConf = {selector: 'body',subSelector: 'video',source: '',id: '16130',page: 'videoPc',from: 'feed',type: 'exception',sample: 0.05,timeout: 3000}</script><script>function sendUbcLog(logInfo, isWhiteScren = false) {var img = new Image;var ubcParams = {cateid: "99",actiondata: {id: logInfo.id,type: "0",timestamp: window.Date.now(),content: {page: logInfo.page,type: logInfo.type,value: isWhiteScren ? 'white' : 'noWhite',source: logInfo.source,from: logInfo.from,ext: {pageUrl: window.location.href,netTime: isWhiteScren ? function () {if (!window.performance) return !1;var e = window.performance.timing;return "&dns=".concat(e.domainLookupEnd - e.domainLookupStart) + "&tcp=".concat(e.connectEnd - e.connectStart) + "&requestTime=".concat(e.responseStart - e.requestStart) + "&resoneTime=".concat(e.responseEnd - e.responseStart)}() : "",deviceInfo: isWhiteScren ? function () {var e = {},n = navigator.connection || {};return e.downlink = n.downlink, e.effectiveType = n.effectiveType, e.rtt = n.rtt, e.deviceMemory = navigator.deviceMemory || 0, e.hardwareConcurrency = navigator.hardwareConcurrency || 0, e}(): ""}}}};img.src = 'https://mbd.baidu.com/ztbox?action=zpblog&v=2.0&appname=baiduboxapp&data=' + encodeURIComponent(JSON.stringify(ubcParams));img.onload = img.onerror = function() {img = null;};}var whiteScreenUgcConf = window.whiteScreenUgcConf;Math.random() < whiteScreenUgcConf.sample && setTimeout(function () {if (function () {var el = document.querySelector(whiteScreenUgcConf.selector);var subSelector = el.querySelector(whiteScreenUgcConf.subSelector);return !el || (!subSelector) || (el.clientHeight < 2 * window.innerHeight / 3)}()) {sendUbcLog(whiteScreenUgcConf, true);} else {sendUbcLog(whiteScreenUgcConf);}}, whiteScreenUgcConf.timeout);</script><script src="https://mbdp02.bdstatic.com/static/video-pc/js/video.3d25aa18.js"></script></body></html>"""
    text2=tt(text,'{','}')
    print(text2)