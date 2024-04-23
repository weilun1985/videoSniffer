import asyncio
import os
import random
import time
from V3_0.utils import get_logger,get_config_item
from V3_0.wechatUtils import msg_recv_outqueue,send_wx_text_reply
from chats.sider_v2 import chat


log=get_logger()

class ChatMessage:
    def __init__(self,from_msg):
        self.text = ""
        self.time0=None
        self.from_msg=from_msg
        def reply(message):
            send_wx_text_reply(self.from_msg,message)
            print(message)
        self.resp_text_h=reply

    def write_text(self, text):
        time1=time.time()
        if self.time0==None:
            self.time0=time1
        self.text += text
        ts=time1-self.time0
        if ts>2 and len(self.text)>0:
            self.resp_text_h(self.text)
            self.text=''
            self.time0=time1

    def done(self):
        time1 = time.time()
        if len(self.text)>0:
            self.resp_text_h(self.text)
            self.text=''
            self.time0=time1

async def mian():
    print("Ai-Hub处理服务启动...")
    # 创建一个集合来管理任务
    tasks = set()

    async def task_to_run(msg):
        content = msg.get('content')
        sender = msg.get('sender')

        print(f'{sender}： {content}')

        chatMsg=ChatMessage(from_msg=msg)

        session = 'C0ZZSM03N2R1'
        await chat(content,session_id=session,model=0,out=chatMsg)

    async def wait_tasks():
        if len(tasks)>0:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                tasks.remove(task)

    def get_task_info():
        wxid = get_config_item('wechat', 'wxid')
        msg = msg_recv_outqueue(wxid)
        if not msg:
            return
        msg_type = msg["msg_type"]
        is_self_msg = msg["is_self_msg"]
        is_chat_room = msg.get('is_chatroom')
        is_at_me = msg.get('at_me')
        sender = msg.get('sender')
        msg_id = msg.get("msg_id")
        if is_self_msg or (is_chat_room and not is_at_me):
            return
        if msg_type == 1:
            return msg

    while True:
        # 动态添加新的任务
        if len(tasks) < 10:  # 假设我们只运行最多10个任务
            msg=get_task_info()
            if msg is not None:
                new_task = asyncio.create_task(task_to_run(msg))
                tasks.add(new_task)
                content = msg.get('content')
                print(f"task {content} added, currently running {len(tasks)} tasks.")
            else:
                await wait_tasks()
        else:
            print('await task.')
            await wait_tasks()

        # 如果没有任务在运行，则退出循环
        if not tasks:
            time.sleep(1)

    print("Ai-Hub处理服务停止")

def start():
    asyncio.run(mian())

if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        os._exit(1)