import json
import typing

import uiautomation

import utils.chrome_ext_cc as chromeExt
import tools
import wintools
import uiautomation as auto
import pyautogui as autogui
import logging,math,os,queue,re,time
from uiautomation import WindowControl,ListControl,ButtonControl,TextControl,EditControl,ListItemControl,DocumentControl,PropertyId
from datetime import datetime,timedelta
from typing import List,Any
from models import WeChatMessageInfo,WeChatSessionInfo,FileTooLargeException,WeChatSendInfo

log=tools.get_logger()
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WECHAT_MAX_FILE_SIZE=50*1024*1024

wx_click_rqueue=queue.Queue()
def wx_click_callback(robj,cmdId):
    tp=robj.get('tp')
    # log.info(f'wx_click_callback tp={tp} cmdId={cmdId}')
    if tp=='tab_created' and not cmdId:
        tabc = robj.get('data')
        tabId = tabc.get("tabId")
        url = tabc.get("url")
        tc = int(tabc.get('t'))
        now=time.time_ns()//1000000
        tsp=now-tc
        if tsp<2000:
            log.info(f'Tab_Created_Callbak TabID={tabId} create-time={tc} now={now} timespan={tsp}ms url={url}')
            wx_click_rqueue.put(tabc)
        else:
            log.warning('Ignore Tab_Create by too long timespan: TabID={tabId} create-time={tc} now={now} timespan={tsp}ms url={url}')

chromeExt.add_handler(wx_click_callback)

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
        session = WeChatSessionInfo()
        session.SessionName = session_name
        session.LastMsgStrTime = temp[0] if len(temp) > 0 else None
        session.LastMsgTime = tools.simpleTimeStr(WeChatUtil.str_to_time(temp[0])) if len(temp) > 0 else None
        session.LastMsgSub = temp[1] if len(temp) > 1 else None
        session.NewMsgNum = int(temp[2]) if len(temp) > 2 else 0
        return session

    @staticmethod
    def fetch_page_info(remark):
        wx_browser = auto.PaneControl(searchDepth=1, Name='微信', ClassName='Chrome_WidgetWin_0')
        if not auto.WaitForExist(wx_browser, 10):
            emsg = f'wx_browser not exists! {remark}'
            log.error(emsg)
            return False,emsg
        # wx_browser.SetActive()
        doc = wx_browser.Control(ClassName='Chrome_RenderWidgetHostHWND')
        if not doc.Exists(maxSearchSeconds=10):
            emsg = f'wx_browser document not exists! {remark}'
            log.error(emsg)
            return False,emsg
        gc = doc.GroupControl()
        if gc.Exists(maxSearchSeconds=30):
            title = doc.Name
            url = doc.GetPropertyValue(PropertyId.LegacyIAccessibleValueProperty)
            log.info(f'fetch-page: {title} {url}')
            tabs = wx_browser.TabControl().TabItemControl().GetParentControl().GetChildren()
            if len(tabs) > 1:
                tab = tabs[-1]
                btn_close = tab.ButtonControl(Name='关闭')
                if btn_close.Exists(maxSearchSeconds=2):
                    btn_close.Click(simulateMove=False)
            return True,[url,title]
        else:
            emsg = f'wx_browser document load timeout! {remark}'
            log.error(emsg)
            return False,emsg


    @staticmethod
    def parse_link_msg(linkbtn,msg_info:WeChatMessageInfo):
        if msg_info.MsgContent is not None:
            summary = '\r\n'.join(msg_info.MsgContent)
        msg_content={'summary':summary}
        msg_info.MsgContent = msg_content

        linkbtn.Click(simulateMove=False)
        log.info(f'Try-Get Link info:{msg_info.Sender} {msg_info.OrgContent} now={time.time_ns()//1000000}')
        try:
            tab=None
            for i in range(10):
                itab=wx_click_rqueue.get(timeout=2)
                tc = int(itab.get('t'))
                now = time.time_ns() // 1000000
                tsp = now - tc
                if tsp<=2000:
                    tab=itab
                    break
            if not tab:
                return

            tabId=tab.get("tabId")
            url=tab.get("url")

            msg_content['url'] = url
            msg_content['tabId'] = tabId
            msg_info.MsgFullGet = True

            log.info(f'Link-GOT {msg_info.Sender} {tabId} {url} {msg_info.OrgContent} now={now} tab-create-time={tc} tsp={tsp}ms')
        except queue.Empty:
            return

        # remark = f'sender={msg_info.Sender}'
        # got, obj= WeChatUtil.fetch_page_info(remark)
        # if got:
        #     url,title=obj[0],obj[1]
        #     msg_content['title']=title
        #     msg_content['url']=url
        #     msg_info.MsgFullGet = True
        # else:
        #     msg_info.MsgFetchError = obj
        # msg_info.MsgContent=msg_content

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

        msg_content =[]
        for n in range(1,5):
            txc = rect_main.TextControl(foundIndex=n)
            if txc.Exists(maxSearchSeconds=0) and not tools.is_empty_str(txc.Name):
                msg_content.append(txc.Name)
        if len(msg_content)==0:
            msg_content.append(name)

        msg_info=WeChatMessageInfo()
        msg_info.OrgContent=name
        msg_info.Sender=sender_btn.Name
        msg_info.MsgContent=msg_content
        msg_info.RecvTime=time.time_ns()
        specialTypes= ['[图片]', '[视频]', '[音乐]', '[链接]']
        if btn_main is not None and name in specialTypes:
            WeChatUtil.parse_link_msg(btn_main,msg_info)
        match=re.match('^\[([\u4e00-\u9fa5]{2,5})\]$',name)
        if match is not None:
            msg_info.MsgContentType=match.group(1)
        else:
            msg_info.MsgContentType = '文本'
            msg_info.MsgContent = '\r\n'.join(msg_content)
            msg_info.MsgFullGet = True
        name1=name.replace('\n',' ')
        log.info(
            f'fetch-msg: sender={msg_info.Sender} org-content={name1} full-get={msg_info.MsgFullGet} btn-main-found:{btn_main != None} {btn_main.BoundingRectangle if btn_main != None else None} content:{msg_info.MsgContent}')
        return msg_info



# 以下是主要微信操作部分
def __get_wx_win():
    wechat = auto.WindowControl(searchDepth=1, Name='微信', ClassName='WeChatMainWndForPC')
    if wechat.Exists():
        wechat.SetActive()
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
    return __search_session(wechat, key)

def send_msg(session_name,msg):
    wechat=__get_wx_win()
    wechat.SetActive()
    current_sess_name = current_chat(wechat)
    if current_sess_name!=session_name:
        __search_session(wechat, session_name)
    edit = wechat.EditControl(Name=session_name)
    if edit.Exists():
        auto.SetClipboardText(msg)
        edit.SendKeys('{Ctrl}a')
        edit.SendKeys('{Ctrl}v')
        edit.SendKeys('{Enter}')
        log.info(f'wx-send-msg: session={session_name} msg-length={len(msg)} content={msg}')
        return True
    else:
        return False

def send_file(session_name,file):
    if not os.path.exists(file):
        log.warning(f'指定的文件不存在: {file}')
        return False
    file_size = os.path.getsize(file)
    if file_size>WECHAT_MAX_FILE_SIZE:
        raise FileTooLargeException
    wechat = __get_wx_win()
    wechat.SetActive()
    current_sess_name = current_chat(wechat)
    if current_sess_name != session_name:
        __search_session(wechat, session_name)
    edit = wechat.EditControl(Name=session_name)
    if edit.Exists():
        wintools.setClipboardFiles([file])
        time.sleep(0.2)
        edit.SendKeys('{Ctrl}a')
        edit.SendKeys('{Ctrl}v')
        if edit.GetValuePattern().Value:
            edit.SendKeys('{Enter}')
            log.info(f'wx-send-file: session={session_name} file-size={tools.filesize_exp(file_size)} file={file}')
            return True
    return False

def __me_is_who(wechat:WindowControl)->str:
    me_btn=wechat.ToolBarControl(Name='导航').ButtonControl(Depth=1,foundIndex=1)
    return me_btn.Name

def me_is_who():
    wechat = __get_wx_win()
    wechat.SetActive()
    return __me_is_who(wechat)

def list_newMsg_session(newMsgHandler=None):
    wechat = __get_wx_win()
    wechat.SetActive()
    me = __me_is_who(wechat)
    sesListCtl = wechat.ListControl(Name='会话')
    auto.WaitForExist(sesListCtl, 0.1)
    # 只获取新消息，由于无置顶的情况下新消息都会在顶部，因此可以认为如果碰到没有新消息的会话，则可以跳出循环
    show_percent, hidd_percent, s_i = 1, 0, 0
    scrollCtl = sesListCtl.GetScrollPattern()
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
    cursess_item = sesListCtl.GetFirstChildControl()
    a, b = 0, 0
    l=0
    while True:
        name=cursess_item.Name
        if name.endswith('条新消息'):
            l=0
            sess = WeChatUtil.parse_session_info(cursess_item)
            if sess != None and sess.NewMsgNum>0:
                a += sess.NewMsgNum
                session_list.append(sess)
                current_session = current_chat(wechat)
                # 如果消息窗体不是当前会话，则点击当前会话，获取会话的新消息
                if current_session != sess.SessionName:
                    cursess_item.ButtonControl(Name=sess.SessionName).Click(simulateMove=False)
                log.info(f'session={sess.SessionName} new_msg_cnt={sess.NewMsgNum} last_msg_time={sess.LastMsgTime}')
                new_msg_list = get_message_list(session_info=sess, max_count=sess.NewMsgNum)
                b += len(new_msg_list)
                sess.MessageList = new_msg_list
                # 触发回调
                for msg in new_msg_list:
                    try:
                        if newMsgHandler:
                            newMsgHandler(sess, me,msg)
                    except Exception as e:
                        log.error(e, exc_info=True)
                height = cursess_item.BoundingRectangle.height()
                # 下滑区域
                sesListCtl.WheelDown(height)
        else:
            # 如果连续4个没有新消息，则表示没有新消息。注意：不适合设置了置顶联系人的情况
            if l>3:
                break
            else:
                l+=1

        # 切换到下一条消息
        next_item=cursess_item.GetNextSiblingControl()
        if next_item is not None and next_item.Exists():
            cursess_item=next_item
        else:
            break
    return session_list,a,b



def get_session_list(only_new:bool=False):
    wechat = __get_wx_win()
    wechat.SetActive()
    me=__me_is_who(wechat)
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
    abort=False
    for i in range(s_i + 1):
        if abort:
            break
        list0 = sesListCtl.GetChildren()
        if list0 is not None:
            for item in list0:
                sess = WeChatUtil.parse_session_info(item)
                if sess is not None and sess.SessionName not in session_names:
                    # 如果只获取新消息，由于无置顶的情况下新消息都会在顶部，因此可以认为如果碰到没有新消息的会话，则可以跳出循环
                    if only_new and sess.NewMsgNum==0:
                        abort=True
                        break
                    sess.Me=me
                    session_list.append(sess)
                    session_names.append(item.Name)
                    # 点掉按钮
                    if sess.NewMsgNum>0:
                        item.ButtonControl(Name=sess.SessionName).Click(simulateMove=False)
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

def get_message_list(session_info:WeChatSessionInfo=None, time_util=None, max_count=0)->List[WeChatMessageInfo]:
    msg_list: List[WeChatMessageInfo] = []
    wechat = __get_wx_win()
    wechat.SetActive()
    sess_name = current_chat(wechat)
    me=__me_is_who(wechat)

    if session_info is not None and sess_name!=session_info.SessionName:
        if not __search_session(wechat, key=session_info.SessionName):
            log.warning(f'找不到的会话: {session_info.SessionName}')
            return msg_list
        sess_name = current_chat(wechat)
        if sess_name != session_info.SessionName:
            err = f'会话可能窜了: {sess_name}  {session_info.SessionName}'
            log.warning(err)
            return msg_list

    #获取会话列表
    msgListCtl=wechat.ListControl(Name='消息')
    # msgListCtl.Click()
    scrollCtl = msgListCtl.GetScrollPattern()
    # 存在滚动条且可以垂直滚动
    if scrollCtl is not None and scrollCtl.VerticallyScrollable:
        # 先一滚到顶，看看隐藏区域占比多少
        scrollCtl.SetScrollPercent(horizontalPercent=0, verticalPercent=0)
        hidd_percent = scrollCtl.VerticalScrollPercent  # 隐藏区域占比
        show_percent = 1 - hidd_percent  # 可见区域占比
        # 滚回底部
        scrollCtl.SetScrollPercent(horizontalPercent=0, verticalPercent=1)

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
                    itm.MsgTime = tools.simpleTimeStr(time_c)
                    itm.MsgStrTime = current_msg.Name
                # 如果设置了信息获取截止时间，则只取之后的信息
                if time_util != None and time_c < time_util:
                    break
            elif isinstance(msg_info, WeChatMessageInfo):
                msg_info.Me = me
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


def check_new_msg(handler):
    seslist0 = get_session_list()
    seslist1 = []
    # 获取有新信息的会话
    a,b=0,0
    for ses in seslist0:
        if ses.NewMsgNum > 0:
            seslist1.append(ses)
            a=a+ses.NewMsgNum
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
                    b=b+1
                except Exception as e:
                    log.error(e,exc_info=True)
        except Exception as e:
            log.error(e,exc_info=True)
    return a,b


def reswxapp_menu_click(wxapp):
    menuBtn = wxapp.ButtonControl(Name='菜单')
    auto.WaitForExist(menuBtn, timeout=2)
    boundR = menuBtn.BoundingRectangle
    l0, t0, r0, b0 ,w0 ,h0= boundR.left, boundR.top, boundR.right, boundR.bottom,boundR.width(),boundR.height()
    # 分享按钮的坐标
    x1 = l0 + int(-4.1 * w0) + 10
    y1 = t0 + int(3.0 * h0) + 10
    # 重载按钮的坐标
    # l2, t2, r2, b2 = l0 - 166, t0 + 307, r0 - 160, b0 + 358
    # x2, y2 = l2 + 10, t2 + 10
    x2 = l0 + int(-2.8 * w0) + 10
    y2 = t0 + int(5.6 * h0) + 10
    menuBtn.Click(simulateMove=False)

    # img_path_share = os.path.join(CURRENT_DIR, 'share.png')
    # location_1 = autogui.locateOnScreen(img_path_share)
    # img_path_reload = os.path.join(CURRENT_DIR, 'reload.png')
    # location_2 = autogui.locateOnScreen(img_path_reload)
    #
    # print(f'({x1},{y1}) ({location_1.left},{location_1.top})')
    # print(f'({x2},{y2}) ({location_2.left},{location_2.top})')

    return x1,y1,x2,y2

def reswxapp_click_reload(wxapp=None):
    # 清空剪切板，并重载小程序
    auto.SetClipboardText('')
    if not wxapp:
        wxapp=open_reswxapp()
    if wxapp:
        x1,y1,x2,y2=reswxapp_menu_click(wxapp)
        wxapp.SetActive()
        autogui.click(x2, y2)
        return True
    return False


def reswxapp_click_share(wxapp=None):
    if not wxapp:
        wxapp = open_reswxapp()
    if wxapp:
        x1, y1, x2, y2 = reswxapp_menu_click(wxapp)
        wxapp.SetActive()
        autogui.click(x1, y1)
        return True
    return False

def open_reswxapp():
    wxapp = auto.PaneControl(searchDepth=1, Name='照片去水印小助手', ClassName='Chrome_WidgetWin_0')
    if not wxapp.Exists(maxSearchSeconds=2):
        log.warning('there are no weixing miniapp windows!')
        # 打开微信小程序
        wxwin=__get_wx_win()
        btn=wxwin.ButtonControl(Name='小程序面板')
        btn.Click(simulateMove=False)
        mini_apps=auto.PaneControl(searchDepth=1,ClassName='Chrome_WidgetWin_0')
        auto.WaitForExist(mini_apps,timeout=2)
        mini_doc=mini_apps.DocumentControl(Name='小程序',ClassName='Chrome_RenderWidgetHostHWND')
        auto.WaitForExist(mini_doc,timeout=2)
        mini_apps_close=mini_apps.GetLastChildControl().ButtonControl(Name='关闭',searchDepth=4)
        wxapp_btn=mini_doc.GroupControl(Name='照片去水印小助手')
        if wxapp_btn.Exists(maxSearchSeconds=3):
            print(wxapp_btn.BoundingRectangle)
            mini_apps.SetActive()
            wxapp_btn.Click(simulateMove=False,waitTime=2)
            # autogui.click(wxapp_btn.BoundingRectangle.left, wxapp_btn.BoundingRectangle.top)
            log.info('click open mini app Icon!')
        else:
            log.warning('unfound wx miniApp button!')
            return None
        if mini_apps_close.Exists(maxSearchSeconds=1):
            mini_apps.SetActive()
            mini_apps_close.Click(simulateMove=False)
    if not auto.WaitForExist(wxapp,timeout=3):
        return None
    wxapp.SetActive()
    return wxapp

def send_reswxapp(session_name,resId):
    def reset():
        if reswxapp_click_reload():
            # 将资源ID写入剪切板，待小程序自动读取
            auto.SetClipboardText(resId)
            time.sleep(0.1)
            return reswxapp_click_share()
        return False
    if not reset():
        return False
    shchat = auto.WindowControl(searchDepth=1, ClassName='SelectContactWnd')
    auto.WaitForExist(shchat, 3)
    shchat.SetActive()
    search = shchat.EditControl(Name='搜索')
    search.Click(simulateMove=False, waitTime=0.1)
    auto.SetClipboardText(session_name)
    search.SendKeys('{Ctrl}a')
    search.SendKeys('{Ctrl}v', waitTime=0.1)
    search.SendKeys('{Enter}', waitTime=0.1)
    sendbtn = shchat.ButtonControl(Name='发送')
    sendbtn.Click(simulateMove=False)
    log.info(f'wx-send-mini_app: session={session_name}  resId={resId}')
    return True

def send(send_info:WeChatSendInfo):
    if send_info.Content is not None:
        match = re.match(r'^res:(\w{32})$', send_info.Content)
        if match:
            resId = match.group(1)
            def send_by_text():
                app_url = '#小程序://照片去水印小助手/ZzNbrUhZyxxCyut'
                send_msg(send_info.To, resId)
                send_msg(send_info.To, f'请复制上面的提取码，点击下面的链接打开小程序后即可下载:{app_url}')
            try:
                if not send_reswxapp(send_info.To, resId):
                    send_by_text()
            except Exception as e:
                log.error(e, exc_info=True)
                send_by_text()
        else:
            send_msg(send_info.To, send_info.Content)
    if send_info.Files is not None:
        for file in send_info.Files:
            log.info(f'send-file-to "{send_info.To}": {file}')
            send_file(send_info.To, file)
    pass

def test_5():
    mq = queue.Queue()
    def fun(ses,me, msg):
        print(f'received: me={me} sender={msg.Sender} msg={msg.__dict__}')
        mq.put(msg)

    while True:
        print(f'start check new msg... mq_size={mq.qsize()}')
        list_newMsg_session(fun)
        # for i in range(mq.qsize()):
        #     msg = mq.get_nowait()
        #     jstr=json.dumps(msg.MsgContent)
        #     re_msg = f'reply for "{msg.MsgContentType} - {len(jstr)}" by "{msg.Sender}" at {msg.MsgTime.strftime("%Y-%m-%d %H:%m")}'
        #     send_msg(msg.SessionName, re_msg)
        time.sleep(5)
    pass

def test_6():
    file=r"E:\myworking\myprojects\xiaohongshu_downloader\download\Xhs\videos\01e5594329b536aa010370038be4b08976_258.mp4"
    send_file('Li',file)

def test_7():
    match = re.match(r'^res:(\w{32})$', 'res:e7928fbe531c079088f25eb935006f38')
    resId=match.group(1)
    sess_name='文件传输助手'
    send_reswxapp(sess_name,resId)

def test_8():
    wxapp=open_reswxapp()
    reswxapp_menu_click(wxapp)


if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    test_7()
    pass