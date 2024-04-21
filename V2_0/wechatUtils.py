import redis
import utils

WX_MSG_TYPE_MAP = {1: '[文本]', 3: '[图片]', 43: '[视频]', 49: '[链接]', 34: '[语音]', 10000: '[系统消息]', 47: '[表情包]', 492: '[链接]', 494: '[小程序]', 493: '[文件]'}
KEY_QUEUE_WXMSG_RECV='VideoSniffer:WeChat:{}:recv_queue'
KEY_QUEUE_WXMSG_SEND='VideoSniffer:WeChat:{}:send_queue'



log=utils.get_logger()
def wx_msg_tostring(msg):
    if msg:
        msg_type_str=msg.get("msg_type_str")
        content=msg.get("content")
        ll=300
        if msg_type_str and len(content)>ll:
            content=content[0:ll]+'...'
        str=f'sender={msg.get("sender")} type={msg.get("type")} msg_type={msg.get("msg_type")}/{msg.get("msg_type_str")}  is_chat_room={msg.get("is_chatroom")} is_at_me={msg.get("at_me")} msg_id={msg.get("msg_id")}  is_self_msg={msg.get("is_self_msg")} wx_id={msg.get("wx_id")} self_wx_id={msg.get("self_wx_id")} \r\n{content}'
        return str

def msg_recv_inqueue(msg):
    try:
        my_wx_id = msg['self_wx_id']
        key=KEY_QUEUE_WXMSG_RECV.format(my_wx_id)
        redis = utils.get_redis()
        jstr = utils.obj_to_json(msg)
        redis.lpush(key, jstr)
        log.info(f'wechat-recv-msg-inqueue [{my_wx_id}]-> {wx_msg_tostring(msg)}')
    except Exception as e:
        log.error(e,exc_info=True)


def msg_recv_outqueue(my_wx_id):
    try:
        key = KEY_QUEUE_WXMSG_RECV.format(my_wx_id)
        redis = utils.get_redis()

        temp = redis.rpop(key)
        if temp is None:
            return
        msg = utils.json_to_obj(temp)
        return msg
    except Exception as e:
        log.error(f'微信消息出栈异常[{my_wx_id}]：{e}', exc_info=True)

def msg_recv_outqueue_all():
    try:
        key_patten = KEY_QUEUE_WXMSG_RECV.format('wxid_4qg4sxvncs1c22')
        redis = utils.get_redis()
        key_list = redis.keys(key_patten)
        msg_list=[]
        for key in key_list:
            temp = redis.rpop(key)
            if temp is None:
                continue
            try:
                msg = utils.json_to_obj(temp)
                msg_list.append(msg)
            except Exception as e:
                log.error(f'微信消息出栈异常：[{key}] {e}', exc_info=True)
        return msg_list
    except Exception as e:
        log.error(f'微信消息出栈异常：{e}', exc_info=True)


def msg_send_inqueue(send_info):
    try:
        my_wx_id=send_info.get('sender')
        if utils.is_empty_str(my_wx_id):
            log.warning(f'send_info 未包含要使用的微信ID信息：{send_info}')
            return
        key = KEY_QUEUE_WXMSG_SEND.format(my_wx_id)
        redis = utils.get_redis()
        jstr= utils.obj_to_json(send_info)
        redis.lpush(key, jstr)
        log.info(f'wechat-send-msg-inqueue [{my_wx_id}]-> {jstr}')
    except Exception as e:
        log.error(e, exc_info=True)

def msg_send_outqueue(my_wx_id):
    try:
        key = KEY_QUEUE_WXMSG_SEND.format(my_wx_id)
        redis = utils.get_redis()
        temp = redis.rpop(key)
        if temp is None:
            return
        send_info = utils.json_to_obj(temp)
        return send_info
    except Exception as e:
        log.error(e, exc_info=True)

