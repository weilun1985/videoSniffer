import uiautomation as auto
import logging,math,os,queue,re,time
from uiautomation import WindowControl,ListControl,ButtonControl,TextControl,EditControl,ListItemControl,DocumentControl,PropertyId
from datetime import datetime,timedelta
from typing import List

log=logging.getLogger()
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
        self.MsgContent=None
        self.Sender:str=None
        self.MsgContentType:str=None

class WeChatUtil:
    @staticmethod
    def name_to_date_str(today:datetime, name):
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

    @staticmethod
    def str_to_time(str):
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
            dstr=f'{WeChatUtil.name_to_date_str(today,g.group(1))} {g.group(2)}'
            time=datetime.strptime(dstr,'%Y-%m-%d %H:%M')
        elif re4.match(str) is not None:
            time = datetime.strptime(str, '%y/%m/%d')
        elif re5.match(str) is not None:
            time = datetime.strptime(f'{today.strftime("%Y-%m-%d")} {str}', '%Y-%m-%d %H:%M')
        elif re6.match(str) is not None:
            dstr = WeChatUtil.name_to_date_str(today, str)
            time = datetime.strptime(dstr, '%Y-%m-%d')
        return time

    @staticmethod
    def parse_session_info(item:ListItemControl):
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
        session.LastMsgTime = WeChatUtil.str_to_time(temp[0]) if len(temp) > 0 else None
        session.LastMsgSub = temp[1] if len(temp) > 1 else None
        session.NewMsgNum = int(temp[2]) if len(temp) > 2 else 0
        return session

    @staticmethod
    def parse_message_info(listItem:ListItemControl):
        name=listItem.Name
        msg_content = name

        sender_btn = listItem.ButtonControl(searchDepth=2)
        if not sender_btn.Exists(maxSearchSeconds=0):
            # 没有发送者，可能是系统消息
            # 判断是否是时间
            time_split=WeChatUtil.str_to_time(msg_content)
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
            page_info=WeChatUtil.fetch_page_info()
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

    @staticmethod
    def fetch_page_info():
        wx_browser=auto.PaneControl(searchDepth=1, Name='微信', ClassName='Chrome_WidgetWin_0')
        if not auto.WaitForExist(wx_browser, 10):
            log.error('wx_browser not exists!')
            return
        # wx_browser.SetActive()
        doc=wx_browser.Control(ClassName='Chrome_RenderWidgetHostHWND')
        if not doc.Exists(maxSearchSeconds=10):
            log.error('wx_browser document not exists!')
            return
        gc=doc.GroupControl()
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

# 以下是主要微信操作部分
def __get_wx_win():
    wechat = auto.WindowControl(searchDepth=1, Name='微信', ClassName='WeChatMainWndForPC')
    if wechat.Exists():
        return wechat

def __search(wechat:WindowControl,key):
    search = wechat.EditControl(Name='搜索')
    search.Click(simulateMove=False)
    auto.SetClipboardText(key)
    search.SendKeys('{Ctrl}v')
    search.SendKeys('{Enter}')

def search(key):
    wechat = __get_wx_win()
    wechat.SetActive()
    __search(wechat, key)

def send_msg(session_name,msg):
    wechat=__get_wx_win()
    wechat.SetActive()
    __search(wechat,session_name)
    edit = wechat.EditControl(Name=session_name)
    if edit.Exists():
        auto.SetClipboardText(msg)
        edit.SendKeys('{Ctrl}a')
        edit.SendKeys('{Ctrl}v')
        edit.SendKeys('{Enter}')
        log.info(f'wx-send-msg: session={session_name} msg-length={len(msg)} content={msg}')
    else:
        return False

def get_session_list():
    wechat = __get_wx_win()
    wechat.SetActive()
    sesListCtl = wechat.ListControl(Name='会话')
    auto.WaitForExist(sesListCtl,0.1)
    show_percent,hidd_percent,s_i = 1,0,0
    scrollCtl =sesListCtl.GetScrollPattern()
    # 存在滚动条且可以垂直滚动
    if scrollCtl is not None and scrollCtl.VerticallyScrollable:
        scrollCtl.SetScrollPercent(horizontalPercent=0, verticalPercent=0)
        # 先一滚到底，看看隐藏区域占比多少
        scrollCtl.SetScrollPercent(horizontalPercent=0, verticalPercent=1)
        hidd_percent = scrollCtl.VerticalScrollPercent  # 隐藏区域占比
        show_percent = 1 - hidd_percent  # 可见区域占比
        # 计算垂直滚动条要向下滚动的次数
        s_i = math.ceil(hidd_percent / show_percent)
        # 滚回顶部
        scrollCtl.SetScrollPercent(horizontalPercent=0, verticalPercent=0)
    # 开始获取会话列表
    session_list = []
    session_names = []
    for i in range(s_i + 1):
        list0 = sesListCtl.GetChildren()
        if list0 is not None:
            for item in list0:
                sess = WeChatUtil.parse_session_info(item)
                if sess is not None and sess.SessionName not in session_names:
                    session_list.append(sess)
                    session_names.append(item.Name)
        # 滚动
        if scrollCtl is not None and scrollCtl.VerticalScrollPercent < 1:
            scrollCtl.SetScrollPercent(horizontalPercent=0, verticalPercent=(i + 1) * show_percent)
    return session_list

def get_message_list(session_info:SessionInfo=None,time_util=None,max_count=0)->List[MessageInfo]:
    wechat = __get_wx_win()
    wechat.SetActive()
    __search(wechat, session_info.SessionName)
    #获取会话列表


def test_2():
    print()

def test_3():
    list = get_session_list()
    a = 1
    for session in list:
        print(a, session.__dict__)
        a += 1

def test_4():
    send_msg('我我我',f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(name)s] [%(process)d] [%(thread)d] %(levelname)s - (%(funcName)s) -> %(message)s')
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    test_3()
    pass