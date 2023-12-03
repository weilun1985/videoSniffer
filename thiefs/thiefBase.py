# 下载器基类
import abc,os
import json
import sys,logging
import requests
import thiefs
import tools
from models import VideoInfo, PictureInfo, ResInfo

# log=tools.get_logger()
app_root_dir=os.path.dirname(sys.argv[0])
download_root_dir=os.path.join(app_root_dir,'download')
# print('download-root-dir:',download_root_dir)
class ThiefBase(metaclass=abc.ABCMeta):

    def __init__(self,target_url):
        self.target_url=target_url
        self.download_dir=os.path.join(download_root_dir,self.name)
        self.download_picture_dir=os.path.join(self.download_dir,'pictures')
        self.download_video_dir = os.path.join(self.download_dir,'videos')

    @property
    def log(self):
        return tools.get_logger()

    @property
    def name(self):
        name=type(self).__name__
        return name

    @abc.abstractmethod
    def target_id(self):
        pass

    @classmethod
    @abc.abstractmethod
    def fetch(self)->(VideoInfo|PictureInfo,bytes|list[bytes]):
        pass

    def check_res_exist(self)->(bool,VideoInfo|PictureInfo):
        res_file_v=os.path.join(self.download_dir,f'video_{self.target_id()}.txt')
        res_file_p=os.path.join(self.download_dir,f'pic_{self.target_id()}.txt')
        exist=False
        info=None
        if os.path.exists(res_file_v):
            exist=True
            with open(res_file_v, 'r') as f:
                # str=f.read()
                jstr=json.load(f)
                info=tools.json_to_obj(jstr,VideoInfo)
        elif os.path.exists(res_file_p):
            exist=True
            with open(res_file_p, 'r') as f:
                # str=f.read()
                jstr = json.load(f)
                info = tools.json_to_obj(jstr, PictureInfo)
        return exist,info

    def check_resfile_exist(self,t:str,res_url)->bool:
        if t =='video':
            res_name = os.path.basename(res_url)
            res_file_path = os.path.join(self.download_video_dir, res_name)
        elif t=='pic':
            res_name = os.path.basename(res_url)
            res_file_path = os.path.join(self.download_picture_dir, res_name)
        return os.path.exists(res_file_path)

    @staticmethod
    def load_res_files(info:VideoInfo|PictureInfo):
        if isinstance(info, VideoInfo):
            res_file_dir=os.path.join(download_root_dir,info.thief,'videos')
            res_name = os.path.basename(info.res_url)
            res_file=os.path.join(res_file_dir,res_name)
            if os.path.exists(res_file):
                info.res_file=res_file
        elif isinstance(info,PictureInfo):
            res_file_dir=os.path.join(download_root_dir,info.thief,'pictures')
            for i in range(len(info.res_url_list)):
                res_url=info.res_url_list[i]
                res_name = os.path.basename(res_url)
                res_file = os.path.join(res_file_dir, res_name)
                if os.path.exists(res_file):
                    info.res_file_list.append(res_file)
    def __save_file(self,res_file_path,data:bytes):
        with open(res_file_path, 'wb') as f:
            f.write(data)
        self.log.info(f'save-file:{res_file_path} {int(len(data) / 1024)}KB')

    def save(self,info:VideoInfo|PictureInfo,data:bytes|list):
        if not os.path.exists(self.download_picture_dir):
            os.makedirs(self.download_picture_dir)
            self.log.info('marke-dir: %s',self.download_picture_dir)
        if not os.path.exists(self.download_video_dir):
            os.makedirs(self.download_video_dir)
            self.log.info('marke-dir: %s', self.download_video_dir)
        index_file:str=None
        if isinstance(info,VideoInfo):
            res_file_v = os.path.join(self.download_dir, f'video_{self.target_id()}.txt')
            index_file=res_file_v
            # 保存字节流
            if data is not None:
                res_name=os.path.basename(info.res_url)
                res_file_path=os.path.join(self.download_video_dir, res_name)
                self.__save_file(res_file_path,data)
        elif isinstance(info,PictureInfo):
            res_file_p = os.path.join(self.download_dir, f'pic_{self.target_id()}.txt')
            index_file = res_file_p
            # 保存字节流
            if data is not None:
                for i in range(len(info.res_url_list)):
                    res_url=info.res_url_list[i]
                    res_data=data[i]
                    if res_data is not None:
                        res_name = os.path.basename(res_url)
                        res_file_path = os.path.join(self.download_picture_dir, res_name)
                        self.__save_file(res_file_path, res_data)
        # 保存索引文件
        info.thief=self.name
        jobj=tools.obj_to_json(info)
        with open(index_file,'w') as f:
            json.dump(jobj,f)
        self.log.info(f'save-index-file:{index_file}')

    def go(self):
        exist, info = self.check_res_exist()
        self.log.info(
            f'start-thief-task: thief={self.name} target={self.target_url} exist={exist}')
        if not exist:
            info, data = self.fetch()
            if info is not None:
                if info.name is not None:
                    info.name=info.name.strip()
                if info.content is not None:
                    info.content=info.content.strip()
                self.save(info, data)
        self.load_res_files(info)
        return info
