
import os
import re
import time
from ctypes import *
from pathlib import Path
from datetime import datetime,timedelta

import uiautomation as uia
import win32clipboard  # pywin32
import win32clipboard as wc
import win32con
import win32gui
from uiautomation import ListControl,ButtonControl,TextControl,EditControl,ListItemControl,DocumentControl,PropertyId

class SessionInfo:
    def __init__(self):
        self.SessionName:str=None
        self.LastMsgStrTime:str=None
        self.LastMsgTime:datetime=None
        self.LastMsgSub:str=None
        self.NewMsgNum:int=0

class MessageInfo:
    def __init__(self):
        self.SessionName:str=None
        self.MsgTime:datetime=None
        self.MsgStrTime:str=None
        self.MsgContent:str=None
        self.Sender:str=None

class WxParam:
    SYS_TEXT_HEIGHT = 33
    TIME_TEXT_HEIGHT = 34
    RECALL_TEXT_HEIGHT = 45
    CHAT_TEXT_HEIGHT = 52
    CHAT_IMG_HEIGHT = 117
    SpecialTypes = ['[文件]', '[图片]', '[视频]', '[音乐]', '[链接]']

class WeChat:
    def __init__(self):
        uia.SetGlobalSearchTimeout(0.01)
        self.wx_win = uia.WindowControl(ClassName='WeChatMainWndForPC')
        self.SessionList = self.wx_win.ListControl(Name='会话')
        self.EditMsg = self.wx_win.EditControl(Name='编辑')
        self.SearchBox = self.wx_win.EditControl(Name='搜索')
        self.MsgList = self.wx_win.ListControl(Name='消息')

    def str_to_time(self,str):
        time=None
        if str == '昨天':
            time=datetime.today()-timedelta(seconds=1)
        elif re.match('\d{2}/\d{2}/\d{2}',str) is not None:
            time=datetime.strptime(str,'%y/%m/%d')
        elif re.match('\d+:\d+',str) is not None:
            time=datetime.strptime(f'{datetime.today().date().strftime("%Y-%m-%d")} {str}','%Y-%m-%d %H:%M')
        return time

    def get_session_list(self):
        uia.SetGlobalSearchTimeout(0.01)
        # self.UiaAPI.SwitchToThisWindow()
        list0=self.SessionList.GetChildren()
        session_list=[]
        for item in list0:
            temp=[]
            session_name=item.ButtonControl().Name
            for i in range(2,5):
                try:
                    tc= item.TextControl(foundIndex=i)
                    if tc.Exists(maxSearchSeconds=0):
                        str = item.TextControl(foundIndex=i).Name
                        temp.append(str)
                except:
                    break
            session=SessionInfo()
            session.SessionName=session_name
            session.LastMsgStrTime=temp[0] if len(temp)>0 else None
            session.LastMsgTime=self.str_to_time(temp[0]) if len(temp)>0 else None
            session.LastMsgSub=temp[1] if len(temp)>1 else None
            session.NewMsgNum=temp[2] if len(temp)>2 else 0
            session_list.append(session)
        return session_list

    def search(self, keyword):
        uia.SetGlobalSearchTimeout(0.01)
        # self.UiaAPI.SwitchToThisWindow()
        self.wx_win.SetFocus()
        self.wx_win.SendKeys('{Ctrl}f', waitTime=1)
        self.SearchBox.SendKeys(keyword, waitTime=1.5)
        self.SearchBox.SendKeys('{Enter}')

    def chat_with(self,session_name):
        uia.SetGlobalSearchTimeout(0.01)
        # self.UiaAPI.SwitchToThisWindow()
        # 先从现有会话中找
        btn=self.SessionList.ButtonControl(Name=session_name)
        if btn.Exists(maxSearchSeconds=0):
            btn.Click(waitTime=0.1)
        else:
            self.search(session_name)


    def fetch_wx_pageInfo(self):
        wx_browser=uia.PaneControl(ClassName='Chrome_WidgetWin_0')
        if not wx_browser.Exists(maxSearchSeconds=10):
            print('wx_browser not exists!')
            return
        wx_browser.SwitchToThisWindow()
        wx_browser.SetFocus()
        doc=wx_browser.Control(ClassName='Chrome_RenderWidgetHostHWND')
        if not doc.Exists(maxSearchSeconds=10):
            print('wx_browser document not exists!')
            return
        gc=doc.GroupControl()
        # uia.WaitForExist(gc, timeout=30)
        if gc.Exists(maxSearchSeconds=30):
            title=doc.Name
            url=doc.GetPropertyValue(PropertyId.LegacyIAccessibleValueProperty)

            tab = wx_browser.TabControl()
            if not tab.Exists(maxSearchSeconds=3):
                return
            btn_close = tab.ButtonControl(Name='关闭')
            if btn_close.Exists(maxSearchSeconds=2):
                btn_close.Click()
            return (title,url)



    def fetch_message(self,listItem:ListItemControl):
        name=listItem.Name
        msg_content = name
        msg_sender = None
        sender_btn = listItem.ButtonControl()
        if sender_btn.Exists(maxSearchSeconds=0):
            msg_sender = sender_btn.Name
        print(msg_content, msg_sender)
        if name=='[链接]':
            listItem.ButtonControl(foundIndex=2).Click()
            page_info=self.fetch_wx_pageInfo()
            if page_info is not None:
                title,url=page_info
                print('\t',title,url)
            pass
        elif name=='[视频]':

            pass
        elif name=='[图片]':

            pass




    def get_message_list(self):
        uia.SetGlobalSearchTimeout(0)
        # self.UiaAPI.SwitchToThisWindow()
        list0=self.MsgList.GetChildren()
        for item in list0:
            self.fetch_message(item)
        pass


if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    wx=WeChat()
    list=wx.get_session_list()
    for session in list:
        print(session.__dict__)
    print('')
    wx.chat_with('Li')
    wx.get_message_list()
    pass


