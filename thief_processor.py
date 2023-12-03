import os
import time
import tools
import models
import message_center
import re
from thiefs.thiefBase import ThiefBase
from thiefs.xhs import Xhs
from datetime import datetime
from models import WeChatMessageInfo,WeChatSendInfo,MailInfo

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
    elif host == 'mr.baidu.com':
        pass
    else:
        log.warning(f"不能处理的链接：{url}")
    return thief

def thief_go(thief,from_msg):
    info= thief.go()
    if info is None:
        return
    subject=f'Re:{info.name}'
    content=info.content
    files=[]
    m1=info.__dict__.get('res_file')
    m2=info.__dict__.get('res_file_list')
    t_size = 0
    if m1 is not None:
        file_size = os.stat(m1).st_size
        t_size += file_size
        files.append({'path': m1, 'size': file_size, 'url': info.res_url})
    elif m2 is not None:
        for i in range(len(m2)):
            itm = m2[i]
            res_url = info.res_url_list[i]
            file_size = os.stat(itm).st_size
            t_size += file_size
            files.append({'path': itm, 'size': file_size, 'url': res_url})
    content += f'\r\n找到{len(files)}个文件，共计{tools.filesize_exp(t_size)}。'
    if len(files) > 0:
        for i in range(len(files)):
            content += f"\r\n{i + 1}. {files[i]['url']}"
        if t_size > 50 * 1024 * 1024:  # 50MB附件
            content += f'\r\n附件过大无法发送，请拷贝上面的URL在浏览器中打开自行下载'
        else:
            content += f'\r\n相关资源在附件中，请查收'
    send_reply(from_msg,f'{subject}\r\n{content}',files)

def send_reply(from_message,reply,fiels=None):
    if isinstance(from_message,WeChatMessageInfo):
        message_center.wechatSend(from_message.Me,from_message.Sender,reply,fiels)

def do_task(task):
    thief = None
    shared_text = None
    body=task.MessageBody
    if isinstance(body,WeChatMessageInfo):
        if body.MsgContentType=='文本':
            shared_text=body.MsgContent
        elif body.MsgContentType=='链接':
            shared_text=body.MsgContent.get('url')
    elif isinstance(body,MailInfo):
        pass

    if shared_text is not None:
        thief = thief_route(shared_text)
    if thief is not None:
        send_reply(body,'任务已收到，正在处理中，稍后返回您结果。')
        try:
            thief_go(thief,body)
        except Exception as e:
            reply=f'哎呀呀，不好意思我出问题了，需要休息一下，请您稍后再试。'
            send_reply(body,reply)
    else:
        default_reply = f'您的任务我已收到了，可是这个任务我暂时还不会哈，等我学会后再帮您解决。\r\n"{shared_text}"'
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