from PyOfficeRobot.core.WeChatType import *
from datetime import datetime

class WeixMsg:
    def __init__(self):
        self.msg_session:str=None
        self.msg_time:datetime=None
        self.msg_content:str=None
        self.msg_id:str=None

wx=WeChat()
def select_msg():
    sessions=wx.GetSessionList()
    for who in sessions:
        wx.ChatWith(who)
        print(who)
        msg_list=wx.GetAllMessage
        for msg in msg_list:
            print(msg)


def send_msg(who,content,files):
    wx.ChatWith(who)
    wx.SendMsg(content)
    if files is not None:
            wx.SendFiles(*files)

if __name__ == '__main__':
    select_msg()
    pass