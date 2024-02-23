import re
import time
from datetime import datetime

import message_center
import tools
import user_center
import wechatf
from models import WeChatMessageInfo, WeChatSendInfo, ChannelType
from lxml import etree

log=tools.get_logger()
tmap = {'1':'[文本]','3':'[图片]', '43':'[视频]', '49':'[链接]'}

def parse_msg(omsg):
    wxid = omsg['wxid']
    type = omsg['type']
    if tools.is_empty_str(wxid):
        return None
    session = wechatf.get_remark_or_nick_name(wxid)
    typestr=tmap.get(type)
    content=omsg['message']
    if type=='49':
        root = etree.fromstring(content)
        title= root.xpath("//appmsg/title")[0].text
        des=root.xpath("//appmsg/des")[0].text
        url=root.xpath("//appmsg/url")[0].text
        content={'title':title,'des':des,'url':url}

    uinfo = wechatf.get_user_info()
    msg_info = WeChatMessageInfo()
    msg_info.SessionName=session
    msg_info.Me=uinfo.get('number')
    msg_info.OrgContent = omsg.get('message')
    msg_info.Sender = wxid
    msg_info.RecvTime = time.time_ns()
    msg_info.MsgContentType = typestr if typestr else type
    msg_info.MsgContent = content
    msg_info.MsgFullGet = True
    return msg_info

def checkout_newmsg():
    omsg = wechatf.get_message(False)
    if omsg:
        # print(omsg)
        wxid = omsg['wxid']
        msg,authed,uinfo=user_center.check_user_auth(wxid)
        if msg:
            send_msg(wxid,msg)
        return parse_msg(omsg)


def send_msg(wxid,msg):
    wechatf.send_message(wxid,msg)
    pass

def send(send_info:WeChatSendInfo):
    if send_info.Content is not None:
        match = re.match(r'^res:(\w{32})$', send_info.Content)
        if match:
            resId = match.group(1)
            app_url = '#小程序://照片去水印小助手/ZzNbrUhZyxxCyut'
            send_msg(send_info.To, resId)
            send_msg(send_info.To, f'请复制上面的提取码，点击下面的链接打开小程序后即可下载:{app_url}')
        else:
            send_msg(send_info.To, send_info.Content)
    pass

def run():
    log.info(f'WeChat Processor Start At: {tools.simpleTimeStr(datetime.now())}')
    while True:
        try:
            msg = checkout_newmsg()
            if msg:
                message_center.pushThiefTask(msg)
        except Exception as e:
            log.error(e, exc_info=True)

        c, d = 0, 0
        for i in range(100):
            try:
                uinfo = wechatf.get_user_info()
                me = uinfo.get('number')
                send_info = message_center.popSendTask(ChannelType.WECHAT, me)
                if send_info is None:
                    break
                c = c + 1
                send(send_info)
                d = d + 1
            except Exception as e:
                log.error(e, exc_info=True)
        if c > 0:
            log.info(f'check need sends compleate, need={c} success={d}')
        time.sleep(0.1)


if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    run()

    pass