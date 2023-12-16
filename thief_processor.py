import os
import threading
import time
import typing

import tools
import models
import message_center
import re
from thiefs.thiefBase import ThiefBase
from thiefs.xhs_v2 import Xhs
from thiefs.baidu import Baidu
from datetime import datetime
from models import WeChatMessageInfo,MailInfo,VideoInfo,PictureInfo,ResInfo

log=tools.get_logger()



def thief_route(shared_text)->ThiefBase|None:
    match = re.search('(http|https)://([\w\.]+)/[\w/?=&]+', shared_text)
    if match is None:
        return
    host = match.group(2)
    url = match.group(0)
    thief: ThiefBase = None
    if host in ['xhslink.com','www.xiaohongshu.com']:
        thief = Xhs(url)
    elif host == 'v.douyin.com':
        pass
    elif host == 'mbd.baidu.com':
        thief=Baidu(url)
    else:
        log.warning(f"不能处理的链接：{url}")
    return thief

def thief_go(thief,from_msg):
    try:
        info:ResInfo= thief.go()
        if info is None:
            send_reply(from_msg,'不好意思啊，小的无能，没能找到您要的资源。我已经记录下来了，尽快学会寻找这类资源。')
            log.warning(f'未能获取到指定资源：{thief.name} {thief.target_url}')
            return
        # 编辑并发送回复信息
        content=''
        # if isinstance(info,VideoInfo):
        #     content+=f'为您找到1个视频： \r\n1. {info.res_url}'
        # elif isinstance(info,PictureInfo):
        #     content+=f'为您找到{len(info.res_url_list)}张图片：'
        #     for i in range(len(info.res_url_list)):
        #         content+=f'\r\n{i+1}. {info.res_url_list[i]}'
        # if tools.not_empty_str(info.name) or tools.not_empty_str(info.content):
        #     content+=f'\r\n\r\n同时帮您取到了更多的信息如下：'
        #     a=1
        #     if tools.not_empty_str(info.name):
        #         content += f'\r\n{a}. 标题：\r\n{info.name}'
        #         a+=1
        #     if tools.not_empty_str(info.content):
        #         content += f'\r\n{a}. 描述：\r\n{info.content}'
        #         a+=1
        # content+='\r\n\r\n由于目前系统还未完善，所以需要请您拷贝上面的资源链接粘贴到浏览器中打开后手工下载。程序哥哥正在加紧开发中，为您带来的不便请见谅。。。'
        # if isinstance(info,VideoInfo):
        #     content+=f'为您找到1个视频，提取码为：\r\n{info.id}\r\n'
        # elif isinstance(info,PictureInfo):
        #     content+=f'为您找到{len(info.res_url_list)}张图片,提取码为：\r\n{info.id}\r\n'
        # wxapp_link='#小程序://照片去水印小助手/4XbInlb8UAN27Ko'
        # content+=f'\r\n请点击下面的链接打开提取小程序后，输入上面的提取码即可提取。由于小程序还在审核中，因此还需要您手工操作一下，给您带来的不便请见谅，程序员老哥正在加紧中……\r\n\r\n{wxapp_link}'
        if isinstance(info,VideoInfo):
            send_reply(from_msg,'为您找到1个视频，提取码为：', None)
        elif isinstance(info,PictureInfo):
            send_reply(from_msg,f'为您找到{len(info.res_url_list)}张图片,提取码为：', None)
        else:
            send_reply(from_msg, '已为您找到对应资源，提取码为：', None)
        send_reply(from_msg, info.id, None)
        wxapp_link = '#小程序://照片去水印小助手/4XbInlb8UAN27Ko'
        content = f'请点击下面的链接打开提取小程序后，输入上面的提取码即可提取。由于小程序还在审核中，因此还需要您手工操作一下，给您带来的不便请见谅，程序员老哥正在加紧中……\r\n\r\n{wxapp_link}'
        send_reply(from_msg,content,None)
    except Exception as e:
        log.error(e, exc_info=True)
        reply = f'哎呀呀，不好意思我出问题了，需要休息一下，请您稍后再试。'
        send_reply(from_msg, reply)

# def cache_res_info(info):
#     message_center.setResInfoToRedis(info)

def send_reply(from_message,reply,fiels=None):
    if isinstance(from_message,WeChatMessageInfo):
        message_center.wechatSend(from_message.Me,from_message.Sender,reply,fiels)

def do_task(task):
    thief = None
    shared_text = None
    body=task.MessageBody
    if isinstance(body,WeChatMessageInfo):
        content=body.MsgContent
        if isinstance(content,str):
            shared_text=content
        elif isinstance(content,typing.Dict):
            shared_text=content.get('url')
        elif isinstance(content,typing.List):
            shared_text=' '.join(content)

    elif isinstance(body,MailInfo):
        pass

    if shared_text is not None:
        thief = thief_route(shared_text)
    if thief is not None:
        send_reply(body,'任务已收到，正在处理中，稍后返回您结果。')
        # 新起一个线程来跑
        # thief_go(thief,body)
        thr=threading.Thread(target=thief_go,args=(thief,body))
        thr.start()
    else:
        default_reply = f'您的任务我已收到了，可是这个任务我暂时还不会哈，等我学会后再帮您解决。'
        send_reply(body,default_reply)



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
    run()