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

class FileTooLargeException(Exception):
    def __init__(self,path,max_size):
        self.file=path
        self.max_size=max_size

    def __str__(self):
        return f'文件大小超过限制{tools.filesize_exp(self.max_size)}, 文件={self.file}'

class ResInfo:
    def __init__(self):
        self.id:str=None
        self.thief: str = None
        self.name: str = None
        self.content: str = None
        self.share_url: str = None
        self.res_downloaded: bool = False
        self.res_type:str =None


class VideoInfo(ResInfo):
    def  __init__(self):
        self.res_url:str=None
        self.res_file:str=None

class PictureInfo(ResInfo):
    def __init__(self):
        self.res_url_list = []
        self.res_file_list=[]

class ResInfoForApi:
    def __init__(self):
        self.id=None
        self.title=None
        self.descp=None
        self.video=None
        self.image=None


    @staticmethod
    def parse(res:ResInfo):
        host="https://1e63211h01.yicp.fun/resproxy/"
        index_info=ResInfoForApi()
        index_info.id=res.id
        index_info.title=res.name
        index_info.descp=res.content
        # index_info.res_downloaded=res.res_downloaded
        index_info.res_type=res.res_type
        if isinstance(res,VideoInfo):
            index_info.video={
                'url':res.res_url,
                'durl':f'{host}{res.id}_0.mp4'
            }
        elif isinstance(res,PictureInfo):
            urls=[]
            durls=[]
            a=0
            for url in res.res_url_list:
                urls.append(url)
                durls.append(f'{host}{res.id}_{a}.jpg')
                a+=1
            index_info.image={
                'urls':urls,
                'durls':durls
            }
        return index_info
