import asyncio
import logging
import re,os
import threading
import queue
import time

import utils.chrome_ext_cc as chromeExt
from datetime import datetime
import tools
from thiefs.thiefBase import ThiefBase
from models import ResInfo,VideoInfo,PictureInfo

# log=tools.get_logger()
# def rs_mapper():
#     url_tab={}
#     res_dict={}
#     res_queue=queue.Queue()
#     def save_asso(asso):
#         tabId=asso.get('tabId')
#         url=asso.get('url')
#         t=asso.get('t')
#         url_tab[url]=tabId
#         log.info(f'save-asso: tabId={tabId} time={t} url={url}')
#
#     def save_res(res):
#         tabId=res.get('tabId')
#         reslist=res['list']
#         url=reslist[0].get('webUrl')
#         t=res.get('t')
#         url_tab[url]=tabId
#         log.info(f'save-res: tabId={tabId} time={t} url={url} res-list-len={len(reslist)}')
#         res_dict[tabId]=reslist
#         res_queue.put(res)
#
#     def hasTask(url,tabId):
#         had=False
#         if (url and url_tab.get(url)):
#             had=True
#         if tabId and not had:
#             for tid in url_tab.values():
#                 if tid==tabId:
#                     had= True
#         log.info(f'check-browers-task: tabId={tabId} url={url} had={had}')
#         return had
#
#     def getRes(url,tabId):
#         info=None
#         if not tabId:
#             tabId=url_tab.pop(url,None)
#         if tabId:
#             info=res_dict.pop(tabId,None)
#         log.info(f'try-get-res: tabId={tabId} url={url} got={info is not None}')
#         return info
#
#     def waitRes(url,tabId):
#         for i in range(60):
#             log.info(f'wait-res: tabId={tabId} url={url} N={i}')
#             info = getRes(url, tabId)
#             if info:
#                 break
#             time.sleep(1)
#         return info
#
#         # info=getRes(url,tabId)
#         # if not info:
#         #     n=0
#         #     while True:
#         #         log.warning(f'wait-res: tabId={tabId} url={url} N={n}')
#         #         try:
#         #             res_queue.get(timeout=60)
#         #             info = getRes(url,tabId)
#         #             if info:
#         #                 break
#         #             n=n+1
#         #         except queue.Empty:
#         #             log.warning(f'wait-res-timeout: tabId={tabId} url={url} N={n}')
#         #             break
#         # return info
#
#
#     def ls():
#         print('----url-tabId mapping----------')
#         for k,v in url_tab.items():
#             print(k,v)
#         print('----tabId-res mapping----------')
#         for k,v in res_dict.items():
#             print(k,v[0].get('title'),v[0].get('webUrl'))
#
#     return {
#         'save_res':save_res,
#         'save_asso':save_asso,
#         'getRes':getRes,
#         'waitRes':waitRes,
#         'hasTask':hasTask,
#         'ls':ls
#     }
#
# RS_MAPPER=rs_mapper()
#
# def rs_pipline(recv_msg):
#     log.info(f'recv: {recv_msg}')
#     robj = tools.json_to_obj(recv_msg)
#     tp=robj.get('tp')
#     data = robj.get('data')
#     if tp=='tab_created':
#         RS_MAPPER['save_asso'](data)
#         pass
#     elif tp=='res':
#         RS_MAPPER['save_res'](data)
#         pass
#
# chromeExt.add_handler(rs_pipline)

class General(ThiefBase):
    def __init__(self,sharedObj,target_url:str=None,trigger_time:int=None):
        super().__init__(sharedObj,target_url,trigger_time)
        self.tabId=None
        if isinstance(self.sharedObj,dict):
            self.tabId=self.sharedObj.get('tabId')

    def target_id(self):
        return tools.md5_str(self.target_url)

    def fetch(self) -> (VideoInfo | PictureInfo, bytes | list[bytes]):
        url = self.target_url
        tabId=self.tabId
        r0=chromeExt.open_and_wait_res(url,tabId)
        if not r0 or len(r0)==0:
            return None,None
        res_info=None
        # 判断当前资源是视频为主，还是图片为主
        video_cnt,pic_cnt=0,0
        max_video,max_video_size=None,0
        max_pic,max_pic_size=None,0
        title = r0[0].get('title')
        for ri in r0:
            ri_type = ri.get('type')
            ri_size=int(ri.get('size')) if ri.get('size') else 0
            ri_url=ri.get('url')
            if ri_type and ri_type in tools.CONTENT_TYPE_VIDEO:
                video_cnt+=1
                if (ri_size and ri_size>max_video_size) or (max_video_size==0):
                    max_video_size=ri_size
                    max_video=ri
            elif ri_type and ri_type in tools.CONTENT_TYPE_IMAGE:
                pic_cnt+=1
                if (ri_size and ri_size>max_pic_size) or (max_pic_size==0):
                    max_pic_size=ri_size
                    max_pic=ri
            else:
                self.log.warning(f"没有识别的媒体类型：type={ri_type} size={ri_size} title={title} url={ri_url}")

        # 如果包含有视频，则认为视频为主
        if max_video:
            res_info = VideoInfo()
            res_info.res_type = 'video'
            video_url = max_video['url']
            res_info.res_url = video_url
            res_info.res_size = max_video_size
            res_info.res_cover_url=max_pic['url'] if max_pic else None
        elif max_pic:
            res_info=PictureInfo()
            res_info.res_type = 'picture'
            for pic in r0:
                src=pic.get('url')
                size=int(pic.get('size')) if pic.get('size') else 0
                if src.startswith("http:"):
                    src = f'https:{pic[5:]}'
                res_info.res_url_list.append(src)
                if size:
                    res_info.res_size_list.append(size)
        else:
            self.log.warning(f'未能找到指定格式的视频或者图片：{title} {r0}')
            return None,None


        res_info.share_url = url
        res_info.name = title

        return res_info, None





if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'), threading.current_thread().name,threading.current_thread().ident,os.getpid())
    while True:
        url=input('请输入网址:').strip()
        chromeExt.open_new_tab(url)
        chromeExt.ls()
        result=chromeExt.wait_res(url,None)
        print('result:',result)

    print('run ok')
