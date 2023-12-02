import logging
import math
import os
import queue
import re
import time
from ctypes import *
from pathlib import Path
from datetime import datetime,timedelta
from typing import List

import uiautomation as uiauto
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
        self.MessageList=[]

class MessageInfo:
    def __init__(self):
        self.SessionName:str=None
        self.MsgTime:datetime=None
        self.MsgStrTime:str=None
        self.MsgContent=None
        self.Sender:str=None
        self.MsgContentType:str=None

class WxParam:
    SYS_TEXT_HEIGHT = 33
    TIME_TEXT_HEIGHT = 34
    RECALL_TEXT_HEIGHT = 45
    CHAT_TEXT_HEIGHT = 52
    CHAT_IMG_HEIGHT = 117
    SpecialTypes = ['[文件]', '[图片]', '[视频]', '[音乐]', '[链接]']


log=logging.getLogger()

class WeChat:
    def __init__(self):
        uiauto.SetGlobalSearchTimeout(0.01)
        self.wx_win = uiauto.WindowControl(ClassName='WeChatMainWndForPC')
        self.wx_win.SetActive()
        self.SessionList = self.wx_win.ListControl(Name='会话')
        self.SearchBox = self.wx_win.EditControl(Name='搜索')
        self.MsgList = self.wx_win.ListControl(Name='消息')

    def name_to_date_str(self,today:datetime, name):
        if name == '星期一':
            target_date =  today - timedelta(days=today.weekday()) + timedelta(days=0)
        elif name == '星期二':
            target_date =  today - timedelta(days=today.weekday()) + timedelta(days=1)
        elif name == '星期三':
            target_date =  today - timedelta(days=today.weekday()) + timedelta(days=2)
        elif name == '星期四':
            target_date =  today - timedelta(days=today.weekday()) + timedelta(days=3)
        elif name == '星期五':
            target_date =  today - timedelta(days=today.weekday()) + timedelta(days=4)
        elif name == '星期六':
            target_date =  today - timedelta(days=today.weekday()) + timedelta(days=5)
        elif name == '昨天':
            target_date = today - timedelta(seconds=1)
        else:
            return None
        return target_date.strftime('%Y-%m-%d')

    def str_to_time(self,str):
        re1=re.compile('\d{4}年\d+月\d+日\s\d+:\d+') #2023年11月20日 23:13
        re2=re.compile('(星期[一二三四五六日]|昨天)\s(\d+:\d+)') #星期一 1:23 or 昨天 11:28
        re4=re.compile('\d{2}/\d+/\d+') #22/1/17
        re5=re.compile('\d+:\d+') #7:01
        re6=re.compile('昨天|星期[一二三四五六日]')
        time=None
        today=datetime.strptime(datetime.now().strftime('%Y-%m-%d'),'%Y-%m-%d')

        if re1.match(str) is not None:
            time=datetime.strptime(str,'%Y年%m月%d日 %H:%M')
        elif re2.match(str) is not None:
            g=re2.match(str)
            dstr=f'{self.name_to_date_str(today,g.group(1))} {g.group(2)}'
            time=datetime.strptime(dstr,'%Y-%m-%d %H:%M')
        elif re4.match(str) is not None:
            time = datetime.strptime(str, '%y/%m/%d')
        elif re5.match(str) is not None:
            time = datetime.strptime(f'{today.strftime("%Y-%m-%d")} {str}', '%Y-%m-%d %H:%M')
        elif re6.match(str) is not None:
            dstr = self.name_to_date_str(today, str)
            time = datetime.strptime(dstr, '%Y-%m-%d')
        return time

    # def get_session_list(self):
    #     uia.SetGlobalSearchTimeout(0.01)
    #     # self.UiaAPI.SwitchToThisWindow()
    #
    #     list0=self.SessionList.GetChildren()
    #     session_list=[]
    #     for item in list0:
    #         temp=[]
    #         session_name=item.ButtonControl().Name
    #         for i in range(2,5):
    #             try:
    #                 tc= item.TextControl(foundIndex=i)
    #                 if tc.Exists(maxSearchSeconds=0):
    #                     str = item.TextControl(foundIndex=i).Name
    #                     temp.append(str)
    #             except:
    #                 break
    #         session=SessionInfo()
    #         session.SessionName=session_name
    #         session.LastMsgStrTime=temp[0] if len(temp)>0 else None
    #         session.LastMsgTime=self.str_to_time(temp[0]) if len(temp)>0 else None
    #         session.LastMsgSub=temp[1] if len(temp)>1 else None
    #         session.NewMsgNum=temp[2] if len(temp)>2 else 0
    #         session_list.append(session)
    #     return session_list

    def get_session_info(self,item:ListItemControl):
        head_btn = item.ButtonControl()
        if not head_btn.Exists(maxSearchSeconds=0):
            return
        session_name = head_btn.Name
        if session_name=='折叠置顶聊天':
            return
        temp = []
        for i in range(2, 5):
            tc = item.TextControl(foundIndex=i)
            if tc.Exists(maxSearchSeconds=0):
                str = item.TextControl(foundIndex=i).Name
                temp.append(str)
        session = SessionInfo()
        session.SessionName = session_name
        session.LastMsgStrTime = temp[0] if len(temp) > 0 else None
        session.LastMsgTime = self.str_to_time(temp[0]) if len(temp) > 0 else None
        session.LastMsgSub = temp[1] if len(temp) > 1 else None
        session.NewMsgNum = int(temp[2]) if len(temp) > 2 else 0
        return session

    def get_session_list(self):
        # self.wx_win.SetActive()
        show_percent=1
        hidd_percent=0
        scroll=self.SessionList.GetScrollPattern()
        # print(self.SessionList.BoundingRectangle)
        # print(scroll.VerticallyScrollable, scroll.VerticalScrollPercent, scroll.VerticalViewSize)
        # 存在滚动条且可以垂直滚动
        if scroll is not None and scroll.VerticallyScrollable:
            scroll.SetScrollPercent(horizontalPercent=0, verticalPercent=0)
            # 先一滚到底，看看隐藏区域占比多少
            scroll.SetScrollPercent(horizontalPercent=0, verticalPercent=1)
            hidd_percent=scroll.VerticalScrollPercent #隐藏区域占比
            show_percent=1-hidd_percent # 可见区域占比
            # 滚回顶部
            scroll.SetScrollPercent(horizontalPercent=0, verticalPercent=0)
        # 开始获取会话列表
        # print(hidd_percent,show_percent,hidd_percent/show_percent,math.ceil(hidd_percent/show_percent))
        # print(scroll.VerticallyScrollable, scroll.VerticalScrollPercent, scroll.VerticalViewSize)
        # 计算垂直滚动条要向下滚动的次数
        s_i=math.ceil(hidd_percent/show_percent)
        # print(s_i)
        session_list = []
        session_names=[]
        item=self.SessionList.ListItemControl()
        for i in range(s_i+1):
            list0 = self.SessionList.GetChildren()
            if list0 is not None:
                for item in list0:
                    session=self.get_session_info(item)
                    if session is not None and session.SessionName not in session_names:
                        session_list.append(session)
                        session_names.append(item.Name)
            # 滚动
            # print(i,scroll.VerticalScrollPercent,i*show_percent)
            if scroll is not None and scroll.VerticalScrollPercent<1:
                scroll.SetScrollPercent(horizontalPercent=0, verticalPercent=(i+1)*show_percent,waitTime=1)
        # 滚回顶部
        if scroll!=None:
            scroll.SetScrollPercent(horizontalPercent=0, verticalPercent=0)
        return session_list

    def search(self, keyword):
        uiauto.SetGlobalSearchTimeout(0.01)
        self.wx_win.SwitchToThisWindow()
        self.wx_win.SendKeys('{Ctrl}f', waitTime=1)
        self.SearchBox.SetFocus()
        self.SearchBox.SendKeys(keyword, waitTime=1.5)
        self.SearchBox.SendKeys('{Enter}')

    # def chat_with(self,session_name):
    #     uia.SetGlobalSearchTimeout(0.01)
    #     # self.wx_win.SetActive()
    #     # self.wx_win.SwitchToThisWindow()
    #     # 先从现有会话中找
    #     btn=self.SessionList.ButtonControl(Name=session_name)
    #     if btn.Exists(maxSearchSeconds=0):
    #         btn.Click(waitTime=0.1,simulateMove=False)
    #     else:
    #         self.search(session_name)
    #     if self.current_chat()==session_name:
    #         return True
    #     return False

    def current_chat(self):
        session_name=None
        s_topic_btn = self.wx_win.ButtonControl(Name='聊天信息')
        if s_topic_btn.Exists(maxSearchSeconds=0):
            topic = s_topic_btn.GetParentControl().GetParentControl().GetPreviousSiblingControl().TextControl()
            session_name = topic.Name
            if re.match('^(.+)\s\(\d+\)$', topic.Name) != None:
                session_name = topic.Name.rsplit(' ', 2)[0]
        return session_name

    def fetch_wx_pageInfo(self):
        # self.wx_win.SetActive()
        wx_browser=uiauto.PaneControl(ClassName='Chrome_WidgetWin_0')
        if not uiauto.WaitForExist(wx_browser, 20):
            log.error('wx_browser not exists!')
            return
        # wx_browser.SwitchToThisWindow()
        # wx_browser.SetActive()
        doc=wx_browser.Control(ClassName='Chrome_RenderWidgetHostHWND')
        if not doc.Exists(maxSearchSeconds=10):
            log.error('wx_browser document not exists!')
            return
        gc=doc.GroupControl()
        # uia.WaitForExist(gc, timeout=30)
        if gc.Exists(maxSearchSeconds=30):
            title=doc.Name
            url=doc.GetPropertyValue(PropertyId.LegacyIAccessibleValueProperty)
            log.info('fetch-page:',title,url)
            tabs=wx_browser.TabControl().TabItemControl().GetParentControl().GetChildren()
            if len(tabs)>1:
                tab = tabs[-1]
                btn_close = tab.ButtonControl(Name='关闭')
                if btn_close.Exists(maxSearchSeconds=2):
                    btn_close.Click(simulateMove=False)
            return {'title':title,'url':url}



    def fetch_message(self,listItem:ListItemControl):
        # self.wx_win.SetActive()
        # listItem.SetFocus()
        name=listItem.Name
        msg_content = name

        sender_btn = listItem.ButtonControl(searchDepth=2)
        if not sender_btn.Exists(maxSearchSeconds=0):
            # 没有发送者，可能是系统消息
            # 判断是否是时间
            time_split=self.str_to_time(msg_content)
            return time_split

        msg_info=MessageInfo()
        msg_info.Sender=sender_btn.Name
        msg_info.MsgContent=msg_content
        msg_info.MsgContentType='文本'
        log.info(f'start-fetch-msg: {msg_info.Sender} {msg_info.MsgContentType}')
        if name=='[链接]':
            msg_info.MsgContentType='链接'
            open_btn=listItem.ButtonControl(foundIndex=2)
            if open_btn.Exists(maxSearchSeconds=0):
                open_btn.Click()
            page_info=self.fetch_wx_pageInfo()
            msg_info.MsgContent=page_info
        elif name=='[视频]':
            msg_info.MsgContentType = '视频'
            pass
        elif name=='[图片]':
            msg_info.MsgContentType = '图片'
            pass
        elif name == '[文件]':
            msg_info.MsgContentType = '文件'
            pass
        elif name =='[动画表情]':
            msg_info.MsgContentType = '动画表情'
            pass
        elif name == '[音乐]':
            msg_info.MsgContentType = '音乐'
            pass
        return msg_info
        # print(msg_info.Sender, ':\r\n\t', msg_info.MsgContent)



    def get_message_list(self,session_info:SessionInfo=None,time_util=None,max_count=0)->List[MessageInfo]:
        # uia.SetGlobalSearchTimeout(0)
        # self.wx_win.SwitchToThisWindow()
        # 获取会话标题
        s_topic_btn=self.wx_win.ButtonControl(Name='聊天信息')
        if s_topic_btn.Exists(maxSearchSeconds=0):
            topic=s_topic_btn.GetParentControl().GetParentControl().GetPreviousSiblingControl().TextControl()
            session_name=topic.Name
            if re.match('^(.+)\s\(\d+\)$',topic.Name)!=None:
                session_name=topic.Name.rsplit(' ',2)[0]
            # session_name=re.match('([^\(\)]+)(\s\(\d+\)|)',topic.Name).group(1)
            # print(session_name)
        if session_info !=None:
            if session_name!=session_info.SessionName:
                err=f'会话可能窜了: {session_name}  {session_info.SessionName}'
                log.warning(err)
                raise Exception(err)
        # 获取会话可视区比例
        show_percent = 1
        hidd_percent = 0
        self.MsgList.SetFocus()
        self.MsgList.Click()
        scroll = self.MsgList.GetScrollPattern()
        # 存在滚动条且可以垂直滚动
        if scroll is not None and scroll.VerticallyScrollable:
            # 先一滚到顶，看看隐藏区域占比多少
            scroll.SetScrollPercent(horizontalPercent=0, verticalPercent=0)
            hidd_percent = scroll.VerticalScrollPercent  # 隐藏区域占比
            show_percent = 1 - hidd_percent  # 可见区域占比
            # 滚回底部
            scroll.SetScrollPercent(horizontalPercent=0, verticalPercent=1)
        msg_list:List[MessageInfo]=[]
        list0=self.MsgList.GetChildren()
        # print('got messages size:',len(list0))
        if list0 is None or len(list0)==0:
            return msg_list

        current_msg=self.MsgList.GetChildren()[-1]
        while True:
            # 如果设置了信息获取最大条数，则只取最大条数信息
            if max_count > 0 and len(msg_list) >= max_count:
                break
            msg_info=self.fetch_message(current_msg)
            if msg_info is not None:
                if isinstance(msg_info,datetime):
                    # print('this is time:',msg_info)
                    # 将之前没有时间的消息都标注为这个时间
                    time_c=msg_info
                    for itm in msg_list:
                        if itm.MsgTime is not None:
                            break
                        itm.MsgTime=time_c
                        itm.MsgStrTime=current_msg.Name
                    # 如果设置了信息获取截止时间，则只取之后的信息
                    if time_util != None and time_c<time_util:
                        break
                elif isinstance(msg_info,MessageInfo):
                    msg_info.SessionName=session_name
                    if len(msg_list)==0:
                        msg_list.append(msg_info)
                        if session_info != None:
                            msg_info.MsgTime = session_info.LastMsgTime
                    else:
                        msg_list.insert(0,msg_info)


            befor=current_msg.GetPreviousSiblingControl()
            if befor is not None and befor.Exists():
                if isinstance(befor,ButtonControl):
                    print('--------->',befor.Name)
                    befor.Click(simulateMove=False,waitTime=0.1)
                    print('reget-prev-is: ',current_msg.GetPreviousSiblingControl())
                    break
                else:
                    height = current_msg.BoundingRectangle.height()
                    current_msg=befor
                    # 上滑区域
                    self.MsgList.WheelUp(height)
            else:
                break
        #再清理一轮消息
        if time_util != None:
            temp_list=[]
            for msg in msg_list:
                if msg.MsgTime<time_util:
                    continue
                temp_list.append(msg)
            msg_list=temp_list
        if max_count>0 and len(msg_list)>max_count:
            n=len(msg_list)-max_count
            temp_list=msg_list[n:]
            msg_list = temp_list
        return msg_list

    def new_message_monitor(self,handler):
        seslist0 = self.get_session_list()
        seslist1 = []
        # 获取有新信息的会话
        for ses in seslist0:
            if ses.NewMsgNum > 0:
                seslist1.append(ses)
        # 获取新信息
        for ses in seslist1:
            try:
                log.info(f'session={ses.SessionName} new_msg_cnt={ses.NewMsgNum} last_msg_time={ses.LastMsgTime}')
                self.chat_with(ses.SessionName)
                new_msg_list = self.get_message_list(session_info=ses, max_count=ses.NewMsgNum)
                ses.MessageList = new_msg_list
                # 触发回调
                for msg in new_msg_list:
                    try:
                        handler(ses,msg)
                    except Exception as e:
                        log.error(e)
            except Exception as e:
                log.error(e)
        pass

    def get_edit_control(self,session_name):
        self.wx_win.SwitchToThisWindow()
        edit_control = self.wx_win.EditControl(Name=session_name)
        if not edit_control.Exists(maxSearchSeconds=0.1):
            if not self.chat_with(session_name):
                log.warning(f'无法打开会话:{session_name}')
                return
            else:
                edit_control = self.wx_win.EditControl(Name=session_name)
        if not edit_control.Exists(maxSearchSeconds=0.1):
            log.warning(f'无法获取倒对话输入框:{session_name}')
            return
        return edit_control

    def send_msg(self,session_name,msg,clear=True):
        wechat=uiauto.WindowControl(searchDepth=1,Name='微信',ClassName='WeChatMainWndForPC')
        wechat.SetActive()
        search=wechat.EditControl(Name='搜索')
        edit=wechat.EditControl(Name=session_name)
        # btnSend=wechat.ButtonControl(Name='发送(S)')

        search.Click(simulateMove=False)
        uiauto.SetClipboardText(session_name)
        search.SendKeys('{Ctrl}v')
        search.SendKeys('{Enter}')

        # time.sleep(1)
        uiauto.SetClipboardText(msg)
        edit.SendKeys('{Ctrl}v')
        edit.SendKeys('{Enter}')
        # btnSend.Click()

        log.info(f'wx-send-msg: session={session_name} msg-length={len(msg)} content={msg}')
        return True

    # def get_new_messages(self):
    #     seslist0=self.get_session_list()
    #     seslist1=[]
    #     # 获取有新信息的会话
    #     for ses in seslist0:
    #         if ses.NewMsgNum>0:
    #             seslist1.append(ses)
    #     # 获取新信息
    #     for ses in seslist1:
    #         print(f'session={ses.SessionName} new_msg_cnt={ses.NewMsgNum} last_msg_time={ses.LastMsgTime}')
    #         self.chat_with(ses.SessionName)
    #         new_msg_list=self.get_message_list(session_info=ses,max_count=ses.NewMsgNum)
    #         ses.MessageList=new_msg_list
    #         a = 1
    #         for msg in new_msg_list:
    #             print(a, f'[{msg.SessionName}] # ', msg.Sender,
    #                   msg.MsgTime.strftime('%Y-%m-%d %H:%M') if msg.MsgTime is not None else None)
    #             print('\t', msg.MsgContentType, msg.MsgContent)
    #             a += 1

def test_1():
    wx = WeChat()
    list = wx.get_session_list()
    a = 1
    for session in list:
        print(a, session.__dict__)
        a += 1
    print('')
    wx.chat_with('我我我')
    msglist = wx.get_message_list()
    a = 1
    for msg in msglist:
        print(a, f'[{msg.SessionName}] # ', msg.Sender,
              msg.MsgTime.strftime('%Y-%m-%d %H:%M') if msg.MsgTime is not None else None)
        print('\t', msg.MsgContentType, msg.MsgContent)
        a += 1
    pass

def test_2():
    def fun(ses,msg):
        print(f'[{msg.SessionName}] # ', msg.Sender,
              msg.MsgTime.strftime('%Y-%m-%d %H:%M') if msg.MsgTime is not None else None)
        print('\t', msg.MsgContentType, msg.MsgContent)

    wx = WeChat()
    while True:
        print('start check new msg...')
        wx.new_message_monitor(fun)
        time.sleep(5)

def test_3():
    mq=queue.Queue()
    def fun(ses,msg):
        print(f'[{msg.SessionName}] # ', msg.Sender,
              msg.MsgTime.strftime('%Y-%m-%d %H:%M') if msg.MsgTime is not None else None,msg.MsgContentType, msg.MsgContent)
        mq.put(msg)

    wx = WeChat()
    while True:
        print('start check new msg...')
        wx.new_message_monitor(fun)
        print('start reply msg...')
        print('mq_size:',mq.qsize())
        for i in range(mq.qsize()):
            msg=mq.get_nowait()
            re_msg=f'reply for "{msg.MsgContentType} - {len(msg.MsgContent)}" by "{msg.Sender}" at {msg.MsgTime.strftime("%Y-%m-%d %H:%m")}'
            wx.send_msg(msg.SessionName,re_msg)

        time.sleep(5)
    pass

def test_4():
    wx = WeChat()
    wx.send_msg('我我我',f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(name)s] [%(process)d] [%(thread)d] %(levelname)s - (%(funcName)s) -> %(message)s')
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    test_3()
    pass


