import utils

class FileTooLargeException(Exception):
    def __init__(self,path,max_size):
        self.file=path
        self.max_size=max_size

    def __str__(self):
        return f'文件大小超过限制{utils.filesize_exp(self.max_size)}, 文件={self.file}'

class ResInfo:
    def __init__(self):
        self.id:str=None
        self.thief: str = None
        self.name: str = None
        self.content: str = None
        self.share_url: str = None
        self.res_downloaded: bool = False
        self.res_type:str =None
        self.got_time:int=None


class VideoInfo(ResInfo):
    def  __init__(self):
        self.res_url:str=None
        self.res_file:str=None
        self.res_size:int=0
        self.res_cover_url:str=None

class PictureInfo(ResInfo):
    def __init__(self):
        self.res_url_list = []
        self.res_size_list=[]
        self.res_file_list=[]


class ResInfoForApi:
    def __init__(self):
        self.id=None
        self.title=None
        self.descp=None
        self.video=None
        self.image=None

def res_info_stringfy(res_info):
    if res_info is None:
        return
    str=f'资源ID：{res_info.id}'
    str+=f'\r\n资源类型：{type(res_info).__name__}'
    if hasattr(res_info,'name'):
        str += f'\r\n资源名称：{res_info.name}'
    if hasattr(res_info, 'content'):
        str += f'\r\n资源描述：{res_info.content}'
    str+=f'\r\n分享URL：{res_info.share_url}'
    str+=f'\r\n资源数量：{1 if isinstance(res_info,VideoInfo) else len(res_info.res_url_list)}'
    if isinstance(res_info,VideoInfo):
        str+=f'\r\n\t1. {res_info.res_url}'
    else:
        for index,url in enumerate(res_info.res_url_list):
            str+=f'\r\n\t{index}. {url}'
    return str