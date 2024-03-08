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
