import re
import time
import message_center
from channels import wechat3
import tools
from datetime import datetime
from models import ChannelType

log=tools.get_logger()


def msg_handler(session,me,msg):
    try:
        sender=msg.Sender
        if sender!=me:
            message_center.pushThiefTask(msg)
    except Exception as e:
        log.error(e,exc_info=True)


def run():
    log.info(f'WeChat Processor Start At: {tools.simpleTimeStr(datetime.now())}')
    while True:
        try:
            me = wechat3.me_is_who()
            # 检测新消息
            slist,a,b=wechat3.list_newMsg_session(msg_handler)
            if a>0:
                log.info(f'check new msg compleate, receive={a}, got={b}')
        except Exception as e:
            log.error(e,exc_info=True)
            time.sleep(0.1)

        # 检测完成后，进行消息发送
        # log.info('start check need sends...')
        c,d=0,0
        for i in range(100):
            try:
                send_info = message_center.popSendTask(ChannelType.WECHAT, me)
                if send_info is None:
                    break
                c=c+1
                wechat3.send(send_info)
                d=d+1
            except Exception as e:
                log.error(e, exc_info=True)
        if c>0:
            log.info(f'check need sends compleate, need={c} success={d}')
        time.sleep(0.1)







def test_0():
    redis=tools.get_redis()
    for i in range(10):
        status=redis.lpush(tools.QUEUE_THIEF_TASK,f'hello,{i}')
        print(i,'status=',status)

    while True:
        task=redis.rpop(tools.QUEUE_THIEF_TASK)
        if task is None:
            break
        print(task)

if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    run()

    pass
