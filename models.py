from datetime import datetime
from typing import List,Any

import tools



class WeChatSessionInfo:
    def __init__(self):
        self.SessionName:str=None
        self.LastMsgStrTime:str=None
        self.LastMsgTime:str=None
        self.LastMsgSub:str=None
        self.NewMsgNum:int=0
        self.Me:str=None

class WeChatMessageInfo:
    def __init__(self):
        self.SessionName:str=None
        self.MsgTime:str=None
        self.MsgStrTime:str=None
        self.MsgContent=None
        self.Sender:str=None
        self.Me:str=None
        self.MsgContentType:str=None
        self.MsgFullGet:bool=False
        self.MsgFetchError:str=None

class WeChatSendInfo:
    def __init__(self):
        self.To: str = None
        self.Me: str = None
        self.Files: List = None
        self.At: str = None
        self.Content: str = None



class MailInfo:
    def __init__(self):
        self.mail_id=None
        self.subject=None
        self.from_name=None
        self.from_mail=None
        self.Me:str=None
        self.mail_date=None
        self.mail_time=None
        self.text_content=None
        self.html_content=None
        self.files=[]

class MailSendInfo:
    def __init__(self):
        self.To:str=None
        self.Me:str=None
        self.Files: List = None
        self.Subject:str=None
        self.TextContent:str=None
        self.HtmlContent:str=None


class ChannelType():
    WECHAT = 'wechat'      #微信
    MAILBOX = 'mailbox'    #邮箱



class ThiefTaskInfo:
    def __init__(self):
        self.ChannelType:str=None
        self.ChannelID:str=None
        self.From:str=None
        self.Receiver:str=None
        self.Time:datetime=None
        self.MessageBody:Any=None