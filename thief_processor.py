import os
import threading
import time
import typing
import websockets
import tools
import models
import asyncio
import message_center
import re
from thiefs.thiefFactory import get_thief
from datetime import datetime
from models import WeChatMessageInfo,MailInfo,VideoInfo,PictureInfo,ResInfo

log=tools.get_logger()


def thief_go(thief,from_msg):
    try:
        info,from_cache= thief.go()
        if info is None:
            send_reply(from_msg,'不好意思啊，暂时没能找到您要的资源。您可以重试一下。')
            log.warning(f'未能获取到指定资源：{thief.name} {thief.target_url}')
            return
        if isinstance(info,VideoInfo):
            send_reply(from_msg,'为您找到1个视频:', None)
            log.info(f'找到1个视频: {info.id} {info.name} FromCache:{from_cache} Thief={thief.name} Url={thief.target_url}')
        elif isinstance(info,PictureInfo):
            send_reply(from_msg,f'为您找到{len(info.res_url_list)}张图片:', None)
            log.info(f'找到{len(info.res_url_list)}张图片: {info.id} {info.name} FromCache:{from_cache} Thief={thief.name} Url={thief.target_url}')
        else:
            send_reply(from_msg, '已为您找到对应资源:', None)
        # send_reply(from_msg, info.id, None)
        send_reply(from_msg,f'res:{info.id}',None)
        # wxapp_link = '#小程序://照片去水印小助手/4XbInlb8UAN27Ko'
        # content = f'请点击下面的链接打开提取小程序后，输入上面的提取码即可提取。由于小程序还在审核中，因此还需要您手工操作一下，给您带来的不便请见谅，程序员老哥正在加紧中……\r\n\r\n{wxapp_link}'
        # send_reply(from_msg,content,None)
    except Exception as e:
        log.error(e, exc_info=True)
        reply = f'哎呀呀，不好意思我出问题了，请您稍后再试。'
        send_reply(from_msg, reply)

# def cache_res_info(info):
#     message_center.setResInfoToRedis(info)

def send_reply(from_message,reply,fiels=None):
    if isinstance(from_message,WeChatMessageInfo):
        message_center.wechatSend(from_message.Me,from_message.Sender,reply,fiels)

def do_task(task):
    thief = None
    body=task.MessageBody
    sharedObj=None
    timec=None
    if isinstance(body,WeChatMessageInfo):
        sharedObj=body.MsgContent
        trigger_time=body.RecvTime
    elif isinstance(body,MailInfo):
        pass

    if sharedObj:
        needThief,thief = get_thief(sharedObj,trigger_time)
        if needThief:
            if thief is not None:
                send_reply(body, '任务已收到，正在处理中，稍后返回您结果。')
                # 新起一个线程来跑
                # thief_go(thief,body)
                thr = threading.Thread(target=thief_go, args=(thief, body))
                thr.start()
            else:
                default_reply = f'您的任务我已收到了，可是这个任务我暂时还不会哈，等我学会后再帮您解决。'
                send_reply(body, default_reply)
        else:
            pass





def run():
    log.info(f'Thief Processor Start At: {tools.simpleTimeStr(datetime.now())}')
    while True:
        try:
            task=message_center.popThiefTask()
            if task is None:
                time.sleep(1)
                continue
            if task.MessageBody is None:
                log.error(f'message body is None:{task.__dict__}')
                continue
            log.info(f'receive: {type(task.MessageBody).__name__} channel={task.ChannelType}/{task.ChannelID}/{task.From} ->{task.Receiver} time={task.Time} ')
            do_task(task)
        except Exception as e:
            log.error(e,exc_info=True)
            time.sleep(1)



if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))

    # shared_url = 'https://mr.baidu.com/r/1bGdWVtNTFe?f=cp&u=c0e8da399f8386bc'
    shared_url='http://xhslink.com/7N10cy'
    thief=get_thief(shared_url)
    info:ResInfo= thief.go()
    print(info.__dict__)
