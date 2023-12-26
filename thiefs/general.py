import logging
import re,os
import threading
import queue
import utils.chrome_ext_cc as chromeExt
from datetime import datetime
import tools
from thiefs.thiefBase import ThiefBase
from models import ResInfo,VideoInfo,PictureInfo

log=tools.get_logger()
def rs_mapper():
    url_tab={}
    res_dict={}
    res_queue=queue.Queue()
    def save_asso(asso):
        tabId=asso.get('tabId')
        url=asso.get('url')
        url_tab[url]=tabId
    def save_res(res):
        tabId=res.get('tabId')
        reslist=res['list']
        url=reslist[0].get('webUrl')
        url_tab[url]=tabId
        res_dict[tabId]=reslist
        res_queue.put(res)

    def hasTask(url):
        tabId = url_tab.get(url)
        if tabId:
            return True
        return False

    def getResByUrl(url):
        info=None
        tabId=url_tab.pop(url,None)
        if tabId:
            info=res_dict.pop(tabId,None)
        return info

    def waitResByUrl(url):
        info=getResByUrl(url)
        if not info:
            while True:
                try:
                    res_queue.get(timeout=30)
                    info = getResByUrl(url)
                    if info:
                        break
                except queue.Empty:
                    break
        return info

    def getResByTabId(tabId):
        return res_dict.get(tabId)

    def ls():
        print('----url-tabId mapping----------')
        for k,v in url_tab.items():
            print(k,v)
        print('----tabId-res mapping----------')
        for k,v in res_dict.items():
            print(k,v[0].get('title'),v[0].get('webUrl'))

    return {
        'save_res':save_res,
        'save_asso':save_asso,
        'getResByUrl':getResByUrl,
        'getResByTabId':getResByTabId,
        'waitResByUrl':waitResByUrl,
        'hasTask':hasTask,
        'ls':ls
    }

RS_MAPPER=rs_mapper()

def rs_pipline(recv_msg):
    log.info(f'recv: {recv_msg}')
    robj = tools.json_to_obj(recv_msg)
    tp=robj.get('tp')
    data = robj.get('data')
    if tp=='tab_created':
        RS_MAPPER['save_asso'](data)
        pass
    elif tp=='res':
        RS_MAPPER['save_res'](data)
        pass

chromeExt.add_handler(rs_pipline)

class General(ThiefBase):
    def target_id(self):
        return tools.md5_str(self.target_url)

    def fetch(self) -> (VideoInfo | PictureInfo, bytes | list[bytes]):
        url = self.target_url
        # 先看看队列里有没有
        r0=RS_MAPPER['getResByUrl'](url)
        # 如果没有则检查是否在加载中
        if not r0:
            task=RS_MAPPER['hasTask'](url)
            if not task:
                chromeExt.open_new_tab(url)
        r0=RS_MAPPER['waitResByUrl'](url)
        if not r0:
            return None
        if r0[0]['type']=='video/mp4':
            video_url = r0[0]['url']
            res_info = VideoInfo()
            res_info.res_type = 'video'
            res_info.res_url = video_url

            title = r0[0]['title']
            res_info.share_url = url
            res_info.name = title
            return res_info, None





if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'), threading.current_thread().name,threading.current_thread().ident,os.getpid())
    while True:
        url=input('请输入网址:').strip()
        chromeExt.open_new_tab(url)
        RS_MAPPER['ls']()
        result=RS_MAPPER['waitResByUrl'](url)
        print('result:',result)

    print('run ok')
