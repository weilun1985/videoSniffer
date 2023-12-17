import time
import message_center
from channels import wechat3
import tools
from datetime import datetime
from models import ChannelType

log=tools.get_logger()


def msg_handler(session,msg):
    try:
        message_center.pushThiefTask(msg)
    except Exception as e:
        log.error(e,exc_info=True)


def run():
    log.info(f'WeChat Processor Start At: {tools.simpleTimeStr(datetime.now())}')
    while True:
        try:
            me = wechat3.me_is_who()
            # 检测新消息
            # log.info('start check new msg...')
            # a,b= wechat3.check_new_msg(msg_handler)
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
                if send_info.Content is not None:
                    wechat3.send_msg(send_info.To, send_info.Content)
                if send_info.Files is not None:
                    for file in send_info.Files:
                        log.info(f'send-file-to "{send_info.To}": {file}')
                        wechat3.send_file(send_info.To, file)
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
