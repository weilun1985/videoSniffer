import traceback

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
        self.MsgFullGet:bool=False
        self.MsgFetchError:str=None

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
        # 获取发送人按钮
        sender_btn = listItem.ButtonControl(searchDepth=2)
        if not sender_btn.Exists(maxSearchSeconds=0):
            # 没有发送者，可能是系统消息
            # 判断是否是时间
            time_split=WeChatUtil.str_to_time(name)
            return time_split
        sender_name=sender_btn.Name
        # 获取内容区域
        if sender_btn.GetPreviousSiblingControl() is None:
            rect_main=sender_btn.GetNextSiblingControl().GetLastChildControl().GetFirstChildControl().GetFirstChildControl() # 3级
        else:
            rect_main=sender_btn.GetPreviousSiblingControl().GetFirstChildControl().GetFirstChildControl().GetFirstChildControl() #3级
        # 获取内容区域按钮，内容区域的按钮特征是按钮面积最大
        btn_max_area=0
        btn_main=None
        for n in range(1,5):
            btn=rect_main.ButtonControl(foundIndex=n)
            if not btn.Exists(maxSearchSeconds=0):
                break
            if btn.BoundingRectangle is not None:
                area=btn.BoundingRectangle.width()*btn.BoundingRectangle.height()
                if area==0:
                    continue
                # print(n,'. ',btn.BoundingRectangle)
                if area>btn_max_area:
                    btn_max_area=area
                    btn_main=btn

        msg_content = []
        for n in range(1,5):
            txc = rect_main.TextControl(foundIndex=n)
            if txc.Exists(maxSearchSeconds=0):
                msg_content.append(txc.Name)

        msg_info=MessageInfo()
        msg_info.Sender=sender_btn.Name
        msg_info.MsgContent=msg_content

        if name=='[链接]':
            msg_info.MsgContentType='链接'
            btn_main.Click(simulateMove=False)
            remark=f'sender={msg_info.Sender} topic={name}'
            page_info,emsg=WeChatUtil.fetch_page_info(remark)
            if page_info is not None:
                msg_content.append(page_info)
                msg_info.MsgFullGet=True
            elif emsg is not None:
                msg_info.MsgFetchError=emsg
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
        else:
            msg_info.MsgContentType = '文本'
            msg_info.MsgFullGet=True
        name1=name.replace('\n',' ')
        log.info(
            f'fetch-msg: sender={msg_info.Sender} topic={name1} full-get={msg_info.MsgFullGet} btn-main-found:{btn_main != None} {btn_main.BoundingRectangle if btn_main != None else None} content:{msg_content}')
        return msg_info

    @staticmethod
    def fetch_page_info(remark):
        wx_browser=auto.PaneControl(searchDepth=1, Name='微信', ClassName='Chrome_WidgetWin_0')
        if not auto.WaitForExist(wx_browser, 10):
            emsg =f'wx_browser not exists! {remark}'
            log.error(emsg)
            return None,emsg
        # wx_browser.SetActive()
        doc=wx_browser.Control(ClassName='Chrome_RenderWidgetHostHWND')
        if not doc.Exists(maxSearchSeconds=10):
            emsg=f'wx_browser document not exists! {remark}'
            log.error(emsg)
            return None,emsg
        gc=doc.GroupControl()
        if gc.Exists(maxSearchSeconds=30):
            title=doc.Name
            url=doc.GetPropertyValue(PropertyId.LegacyIAccessibleValueProperty)
            log.info(f'fetch-page: {title} {url}')
            tabs=wx_browser.TabControl().TabItemControl().GetParentControl().GetChildren()
            if len(tabs)>1:
                tab = tabs[-1]
                btn_close = tab.ButtonControl(Name='关闭')
                if btn_close.Exists(maxSearchSeconds=2):
                    btn_close.Click(simulateMove=False)
            return {'title':title,'url':url},None
        else:
            emsg = f'wx_browser document load timeout! {remark}'
            log.error(emsg)
            return None,emsg

# 以下是主要微信操作部分
def __get_wx_win():
    wechat = auto.WindowControl(searchDepth=1, Name='微信', ClassName='WeChatMainWndForPC')
    if wechat.Exists():
        return wechat

def __search_session(wechat:WindowControl, key):
    search = wechat.EditControl(Name='搜索')
    search.Click(simulateMove=False)
    auto.SetClipboardText(key)
    search.SendKeys('{Ctrl}a')
    search.SendKeys('{Ctrl}v',waitTime=0.1)

    resltListCtl=wechat.ListControl(RegexName='@str:IDS_FAV_SEARCH_RESULT:')
    if not auto.WaitForExist(resltListCtl,2):
        return False
    r1=resltListCtl.TextControl(Name='联系人',Depth=2)
    r2=resltListCtl.TextControl(Name='群聊',Depth=2)
    if r1 is None and r2 is None:
        return False


    search.SendKeys('{Enter}',waitTime=0.1)
    log.info(f"wechat search: {key}")
    return True

def search_session(key):
    wechat = __get_wx_win()
    wechat.SetActive()
    __search_session(wechat, key)

def send_msg(session_name,msg):
    wechat=__get_wx_win()
    wechat.SetActive()
    __search_session(wechat, session_name)
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

def current_chat(wechat)->str:
    session_name=None
    s_topic_btn = wechat.ButtonControl(Name='聊天信息')
    if s_topic_btn.Exists(maxSearchSeconds=0):
        topic = s_topic_btn.GetParentControl().GetParentControl().GetPreviousSiblingControl().TextControl()
        session_name = topic.Name
        if re.match('^(.+)\s\(\d+\)$', topic.Name) != None:
            session_name = topic.Name.rsplit(' ', 2)[0]
    return session_name

def get_message_list(session_info:SessionInfo=None,time_util=None,max_count=0)->List[MessageInfo]:
    wechat = __get_wx_win()
    wechat.SetActive()
    sess_name = current_chat(wechat)
    if session_info is not None and sess_name!=session_info.SessionName:
        __search_session(wechat, key=session_info.SessionName)
        sess_name = current_chat(wechat)
        if sess_name != session_info.SessionName:
            err = f'会话可能窜了: {sess_name}  {session_info.SessionName}'
            log.warning(err)
            raise Exception(err)

    #获取会话列表
    msgListCtl=wechat.ListControl(Name='消息')
    msgListCtl.Click()
    scrollCtl = msgListCtl.GetScrollPattern()
    # 存在滚动条且可以垂直滚动
    if scrollCtl is not None and scrollCtl.VerticallyScrollable:
        # 先一滚到顶，看看隐藏区域占比多少
        scrollCtl.SetScrollPercent(horizontalPercent=0, verticalPercent=0)
        hidd_percent = scrollCtl.VerticalScrollPercent  # 隐藏区域占比
        show_percent = 1 - hidd_percent  # 可见区域占比
        # 滚回底部
        scrollCtl.SetScrollPercent(horizontalPercent=0, verticalPercent=1)
    msg_list: List[MessageInfo] = []
    list0 = msgListCtl.GetChildren()
    # print('got messages size:',len(list0))
    if list0 is None or len(list0) == 0:
        return msg_list

    current_list=msgListCtl.GetChildren()
    # for itm in current_list:
    #     print(f'{itm.Name}-rect-0:', itm.BoundingRectangle)

    current_msg = current_list[-1]
    while True:
        # 如果设置了信息获取最大条数，则只取最大条数信息
        if max_count > 0 and len(msg_list) >= max_count:
            break
        # print(f'{current_msg.Name}-rect-0:', current_msg.BoundingRectangle)

        msg_info = WeChatUtil.parse_message_info(current_msg)
        if msg_info is not None:
            if isinstance(msg_info, datetime):
                # 将之前没有时间的消息都标注为这个时间
                time_c = msg_info
                for itm in msg_list:
                    if itm.MsgTime is not None:
                        break
                    itm.MsgTime = time_c
                    itm.MsgStrTime = current_msg.Name
                # 如果设置了信息获取截止时间，则只取之后的信息
                if time_util != None and time_c < time_util:
                    break
            elif isinstance(msg_info, MessageInfo):
                msg_info.SessionName = sess_name
                if len(msg_list) == 0:
                    msg_list.append(msg_info)
                    if session_info != None:
                        msg_info.MsgTime = session_info.LastMsgTime
                else:
                    msg_list.insert(0, msg_info)
        # 上翻聊天记录
        befor = current_msg.GetPreviousSiblingControl()
        if befor is not None and befor.Exists():
            if isinstance(befor, ButtonControl):
                print('--------->', befor.Name)
                befor.Click(simulateMove=False, waitTime=0.1)
                print('reget-prev-is: ', current_msg.GetPreviousSiblingControl())
                break
            else:
                height = current_msg.BoundingRectangle.height()
                current_msg = befor
                # 上滑区域
                msgListCtl.WheelUp(height)
        else:
            break
    # 再清理一轮消息
    if time_util != None:
        temp_list = []
        for msg in msg_list:
            if msg.MsgTime < time_util:
                continue
            temp_list.append(msg)
        msg_list = temp_list
    if max_count > 0 and len(msg_list) > max_count:
        n = len(msg_list) - max_count
        temp_list = msg_list[n:]
        msg_list = temp_list
    return msg_list


def monitor_new_msg(handler):
    seslist0 = get_session_list()
    seslist1 = []
    # 获取有新信息的会话
    for ses in seslist0:
        if ses.NewMsgNum > 0:
            seslist1.append(ses)
    # 获取新信息
    for ses in seslist1:
        try:
            log.info(f'session={ses.SessionName} new_msg_cnt={ses.NewMsgNum} last_msg_time={ses.LastMsgTime}')

            new_msg_list = get_message_list(session_info=ses, max_count=ses.NewMsgNum)
            ses.MessageList = new_msg_list
            # 触发回调
            for msg in new_msg_list:
                try:
                    handler(ses, msg)
                except Exception as e:
                    log.error(e,exc_info=True,stack_info=True)
        except Exception as e:
            log.error(e,exc_info=True,stack_info=True)
    pass



def test_2():
    msglist = get_message_list(session_info=None)
    a = 1
    for msg in msglist:
        if msg.MsgFullGet==False:
            print(msg.__dict__)
        a += 1
    pass

def test_3():
    list = get_session_list()
    a = 1
    for session in list:
        print(a, session.__dict__)
        a += 1

def test_4():
    send_msg('我我我',f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')


def test_5():
    mq = queue.Queue()
    def fun(ses, msg):
        print(f'received: {msg.__dict__}')
        mq.put(msg)

    while True:
        print('start check new msg...')
        monitor_new_msg(fun)
        print(f'start reply msg, mq_size={mq.qsize()}')
        for i in range(mq.qsize()):
            msg = mq.get_nowait()
            json.encoder()
            re_msg = f'reply for "{msg.MsgContentType} - {len(msg.MsgContent)}" by "{msg.Sender}" at {msg.MsgTime.strftime("%Y-%m-%d %H:%m")}'
            send_msg(msg.SessionName, re_msg)
        time.sleep(5)
    pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(name)s] [%(process)d] [%(thread)d] %(levelname)s - (%(funcName)s) -> %(message)s')
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    test_5()
    pass