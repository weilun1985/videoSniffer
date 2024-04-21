from WeChatPYAPI import WeChatPYApi
from wechatUtils import WX_MSG_TYPE_MAP,KEY_QUEUE_WXMSG_SEND,KEY_QUEUE_WXMSG_RECV
import utils
import time
from queue import Queue
import os
import logging


log=utils.get_logger()
wx=None
my_info=None
friend_list= {}



def __msg_preproc(msg):
    global my_info
    wx_acc = my_info['wx_account']
    my_wx_id=my_info['wx_id']
    is_self_msg=msg.get('is_self_msg')
    wx_id = msg.get("wx_id")
    sender = msg.get("sender")
    # 判断是否是群消息
    if wx_id and wx_id.endswith("@chatroom"):
        msg['is_chatroom'] = True
        at_list=msg.get('at_list')
        self_wx_id=msg.get('self_wx_id')
        if at_list and self_wx_id in at_list:
            msg['at_me']=True
    else:
        msg['is_chatroom'] = False
        if utils.is_empty_str(sender):
            if is_self_msg==1:
                msg['sender'] = msg['self_wx_id']
            else:
                msg['sender']=wx_id
    msg_type=msg.get('msg_type')
    if msg_type:
        msg_type_str = WX_MSG_TYPE_MAP.get(msg_type)
        if msg_type_str:
            msg['msg_type_str']=msg_type_str
        else:
            log.warning(f'未定义的消息类型：微信账号={wx_acc}/{my_wx_id} 发送人={wx_id} msg_type={msg_type} 详细={utils.wx_msg_tostring(msg)}')



def __msg_recv_inqueue(msg):
    try:
        global my_info
        wx_acc=my_info['wx_account']
        my_wx_id = my_info['wx_id']
        key=KEY_QUEUE_WXMSG_RECV.format(my_wx_id)
        redis = utils.get_redis()
        jstr = utils.obj_to_json(msg)
        redis.lpush(key, jstr)
        log.info(f'wechat-recv-msg-inqueue [{wx_acc}/{my_wx_id}]-> {utils.wx_msg_tostring(msg)}')
    except Exception as e:
        log.error(e,exc_info=True)

def __msg_recv_outqueue():
    try:
        global my_info
        wx_acc = my_info['wx_account']
        my_wx_id = my_info['wx_id']
        key = KEY_QUEUE_WXMSG_RECV.format(my_wx_id)
        redis = utils.get_redis()
        temp = redis.rpop(key)
        if temp is None:
            return
        msg = utils.json_to_obj(temp)
        return msg
    except Exception as e:
        log.error(f'微信消息出栈异常[{wx_acc}/{my_wx_id}]：{e}', exc_info=True)

def __msg_send_outqueue():
    try:
        global my_info
        wx_acc = my_info['wx_account']
        key = KEY_QUEUE_WXMSG_SEND.format(wx_acc)
        redis = utils.get_redis()
        temp = redis.rpop(key)
        if temp is None:
            return
        msg = utils.json_to_obj(temp)
        return msg
    except Exception as e:
        log.error(e, exc_info=True)

def __on_msg_callback(msg):
    """消息回调，建议异步处理，防止阻塞"""
    # 预处理接收消息
    __msg_preproc(msg)
    # 接收消息存存队列
    __msg_recv_inqueue(msg)


def __on_exit_callback(event):
    """退出事件回调"""
    action = event["action"]
    wx_id = event["wx_id"]
    if action == 1:
        log.warning("微信({})：进程结束，请重新启动微信".format(wx_id))
    elif action == 2:
        log.warning("微信({})：已退出登录，请重新登录".format(wx_id))

def __pull_friends():
    global wx
    # 拉取列表（好友/群/公众号等）拉取可能会阻塞，可以自行做异步处理
    # 好友列表：pull_type = 1
    # 群列表：pull_type = 2
    # 公众号列表：pull_type = 3
    # 其他：pull_type = 4
    flist = w.pull_list(pull_type=1)

    for friend in flist:
        f_wx_io = friend['wx_id']
        f_wx_acc = friend['wx_account']
        f_wx_name = friend['nick_name']
        friend_list[f_wx_io] = friend
        log.info(f'好友\t{f_wx_io}\t{f_wx_acc}\t{f_wx_name}')
    log.info(f"获取好友列表:共{len(flist)}人")


# def __check_add_friend(wx_id):
#     global w,my_info
#     if wx_id == my_info["wx_id"]:
#         return
#
#     friend=friend_list.get(wx_id)
#     if friend:
#         f_wx_id = friend['wx_id']
#         f_wx_acc = friend['wx_account']
#         f_wx_name = friend['nick_name']
#         print(f'is friend:{f_wx_id} {f_wx_acc} {f_wx_name}')
#     else:
#         print(f'not is friend:{wx_id}')
#
# def __check_user_auth(msg):
#     pass



def start(msg_handler=None):
    # 初次使用需要pip安装两个库：
    # pip install requests
    # pip install pycryptodomex

    # # 查看帮助
    # help(WeChatPYApi)
    global wx,my_info
    # 实例化api对象【要多开的话就实例化多个《WeChatPYApi》对象】
    w = WeChatPYApi(msg_callback=__on_msg_callback, exit_callback=__on_exit_callback, logger=log)

    # 启动微信【调试模式可不调用该方法】
    errno, errmsg = w.start_wx()
    # errno, errmsg = w.start_wx(path=os.path.join(BASE_DIR, "login_qrcode.png"))  # 保存登录二维码
    if errno != 0:
        log.error(errmsg)
        if errmsg != "当前为调试模式，不需要调用“start_wx”":
            return

    # 这里需要阻塞，等待获取个人信息
    while True:
        my_info = w.get_self_info()
        if not my_info:
            time.sleep(2)
        else:
            break
    log.info(f"登陆成功: {my_info}")
    # 获取好友列表
    __pull_friends()

    # 进入循环
    while True:
        msg_recv=__msg_recv_outqueue()
        if msg_recv:
            type = msg_recv['type']
            if type == 100:
                if msg_handler:
                    try:
                        msg_handler(w,my_info,msg_recv)
                    except Exception as e:
                        log.error(e,exc_info=True)
                else:
                    log.warning(f'未关联处理程序的消息：{msg_recv}')
            elif type == 666:
                log.warning("{} 撤回了消息：{}".format(msg_recv["wx_id"], msg_recv["content"]))
        msg_send=__msg_send_outqueue()
        if msg_send:
            pass
        if not (msg_recv or msg_send):
            time.sleep(1)


    input('请输入任意键结束。。。')



# if __name__ == '__main__':
#     try:
#         start()
#     except KeyboardInterrupt:
#         os._exit(1)