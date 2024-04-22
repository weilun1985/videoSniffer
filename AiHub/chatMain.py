import os
import time
from V3_0.wechatUtils import send_wx_text_reply
from V3_0.utils import get_logger,get_config_item
from V3_0.wechatUtils import run_weichat_daemon


log=get_logger()

def start():
    run_weichat_daemon("Ai-Hub处理服务",pipline)

def pipline(msg):
    msg_type = msg["msg_type"]
    is_self_msg = msg["is_self_msg"]
    is_chat_room = msg.get('is_chatroom')
    is_at_me = msg.get('at_me')
    sender = msg.get('sender')
    msg_id = msg.get("msg_id")

    def handler(str):
        send_wx_text_reply(msg,str)

    # 自己发的消息，或者群里发的但是没有AT自己的消息，忽略
    if is_self_msg or (is_chat_room and not is_at_me):
        return
    if msg_type == 37:
        # 同意添加好友申请
        return
    if msg_type==1:
        content = msg.get('content')
        print(f'{sender}： {content}')
        from chats.sider_v2 import sync_chat
        session = 'C0ZZSM03N2R1'
        sync_chat(content,session,handler)


if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        os._exit(1)