from queue import Queue

from WeChatPYAPI import WeChatPYApi
import wechatUtils
import utils
import time
import os


log=utils.get_logger()
wx=None
my_info=None
friend_list= {}
local_msg_queue= Queue()

def msg_preproc(msg):
    global my_info,wx
    wx_acc=my_info.get('wx_account') if my_info else None
    my_wx_id=my_info.get('wx_id') if my_info else None

    is_self_msg=msg.get('is_self_msg')
    wx_id = msg.get("wx_id")
    self_wx_id=msg.get('self_wx_id')
    sender = msg.get("sender")
    if utils.is_empty_str(self_wx_id):
        if my_wx_id is not None:
            self_wx_id=my_wx_id
            msg['self_wx_id']=self_wx_id
        else:
            log.warning('暂未识别出当前微信ID，消息延迟处理。')
            return False


    # 判断是否是群消息
    if wx_id and wx_id.endswith("@chatroom"):
        msg['is_chatroom'] = True
        at_list=msg.get('at_list')
        self_wx_id=self_wx_id
        if at_list and (self_wx_id in at_list):
            msg['at_me']=True
    else:
        msg['is_chatroom'] = False
        if utils.is_empty_str(sender):
            if is_self_msg==1:
                msg['sender'] = self_wx_id
            else:
                msg['sender']=wx_id
    msg_type=msg.get('msg_type')
    if msg_type:
        msg_type_str = wechatUtils.WX_MSG_TYPE_MAP.get(msg_type)
        if msg_type_str:
            msg['msg_type_str']=msg_type_str
        else:
            log.warning(f'未定义的消息类型：微信账号={wx_acc}/{my_wx_id} 发送人={wx_id} msg_type={msg_type} 详细={utils.wx_msg_tostring(msg)}')
        if msg_type == 37:
            # 同意添加好友申请
            wx.agree_friend(msg_data=msg)
    return True

def msg_inqueue(msg):
    try:
        # 预处理接收消息
        if msg_preproc(msg):
            # 接收消息存存队列
            wechatUtils.msg_recv_inqueue(msg)
        else:
            local_msg_queue.put(msg)
    except Exception as e:
        log.error(e, exc_info=True)

def on_msg_callback(msg):
    # 处理历史消息
    while not local_msg_queue.empty():
        h_msg=local_msg_queue.get_nowait()
        msg_inqueue(h_msg)
    #  处理新消息
    msg_inqueue(msg)

def on_exit_callback(event):
    """退出事件回调"""
    action = event["action"]
    wx_id = event["wx_id"]
    if action == 1:
        log.warning("微信({})：进程结束，请重新启动微信".format(wx_id))
    elif action == 2:
        log.warning("微信({})：已退出登录，请重新登录".format(wx_id))

def pull_friends():
    global wx
    # 拉取列表（好友/群/公众号等）拉取可能会阻塞，可以自行做异步处理
    # 好友列表：pull_type = 1
    # 群列表：pull_type = 2
    # 公众号列表：pull_type = 3
    # 其他：pull_type = 4
    flist = wx.pull_list(pull_type=1)

    for friend in flist:
        f_wx_io = friend['wx_id']
        f_wx_acc = friend['wx_account']
        f_wx_name = friend['nick_name']
        friend_list[f_wx_io] = friend
        log.info(f'好友\t{f_wx_io}\t{f_wx_acc}\t{f_wx_name}')
    log.info(f"获取好友列表:共{len(flist)}人")

def start():
    # 初次使用需要pip安装两个库：
    # pip install requests
    # pip install pycryptodomex

    # # 查看帮助
    # help(WeChatPYApi)
    global wx,my_info
    # 实例化api对象【要多开的话就实例化多个《WeChatPYApi》对象】
    wx = WeChatPYApi(msg_callback=on_msg_callback, exit_callback=on_exit_callback, logger=log)

    # 启动微信【调试模式可不调用该方法】
    errno, errmsg = wx.start_wx()
    # errno, errmsg = w.start_wx(path=os.path.join(BASE_DIR, "login_qrcode.png"))  # 保存登录二维码
    if errno != 0:
        log.error(errmsg)
        if errmsg != "当前为调试模式，不需要调用“start_wx”":
            return

    # 这里需要阻塞，等待获取个人信息
    while True:
        my_info = wx.get_self_info()
        if not my_info:
            time.sleep(2)
        else:
            break
    log.info(f"微信消息收发程序已启动: {my_info}")
    # 获取好友列表
    pull_friends()
    my_wx_id=my_info.get("wx_id")

    # 进入待发消息循环
    while True:
        try:
            send_info=wechatUtils.msg_send_outqueue(my_wx_id)
            if send_info:
                action=send_info.get('action')
                options=send_info.get('options')
                if action=='send_text':
                    wx.send_text(to_wx=options.get('to_wx'), msg=options.get('msg'))
                elif action=='send_text_and_at_member':
                    wx.send_text_and_at_member(to_chat_room=options.get('to_chat_room'), to_wx_list=options.get('to_wx_list'), msg=options.get('msg'))
                elif action=='send_xml':
                    wx.send_xml(to_wx=options.get('to_wx'), xml_str=options.get('xml_str'))
                elif action=='forward_msg':
                    wx.forward_msg(to_wx=options.get('to_wx'), msg_id=options.get('msg_id'))
                elif action=='stop':
                    log.warning(f'微信操作中止：action={action} options={options}')
                    break
                else:
                    log.warning(f'微信未知的操作发起：action={action} options={options}')
            else:
                time.sleep(0.1)
        except Exception as e:
            log.error(e,exc_info=True)
            time.sleep(0.2)
    input('微信消息收发程序，请输入任意键结束。。。')
    log.info(f"微信消息收发程序已停止: {my_info}")



if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        os._exit(1)