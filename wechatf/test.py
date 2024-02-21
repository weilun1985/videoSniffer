import time
import wechatf

if __name__ == '__main__':
    # test_send_msg()
    # print(wechatf.is_login())
    while True:
        msg = wechatf.get_message()
        if msg:
            print(msg)
            fu=msg['wxid']
            nick=wechatf.get_remark_or_nick_name(fu)
            print(nick)
            wechatf.send_message(fu,'hello')
        time.sleep(1)
    pass