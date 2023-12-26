import logging
import re,os
import threading
import time
import utils.chrome_ext_cc as chromeExt
from datetime import datetime
import tools
from thiefs.thiefBase import ThiefBase
from models import ResInfo,VideoInfo,PictureInfo

log=logging.getLogger("ChromeCtrl")

def rs_mapper():
    tabId_dict,code_dict,url_dict={},{},{}
    rs_dict={}
    # rs_list=[]
    def save_asso(asso):
        tabId=asso.get('tabId')
        code=asso.get('code')
        url=asso.get('url')
        if tabId:
            tabId_dict[tabId]=asso
        if code:
            code_dict[code]=asso
        if url:
            url_dict[url]=asso
    def save_res(res):
        tabId=res.get('tabId')
        reslist=res['list']
        url=reslist[0].get('webUrl')
        # rs_list.append(res)
        rs_dict[tabId]=reslist


    def getResByUrl(url):
        asso=url_dict.get(url)
        if asso:
            tabId=asso.get('tabId')
        if tabId:
            return rs_dict.get(tabId)

    def getResByTabId(tabId):
        return rs_dict.get(tabId)

    return {
        'save_res':save_res,
        'save_asso':save_asso,
        'getResByUrl':getResByUrl,
        'getResByTabId':getResByTabId
    }

RS_MAPPER=rs_mapper()

def rs_pipline(recv_msg):
    log.info(f'recv: {recv_msg}')
    robj = tools.json_to_obj(recv_msg)
    tp=robj.get('tp')
    data = robj.get('data')
    if tp=='asso':
        RS_MAPPER['save_asso'](data)
        pass
    elif tp=='res':
        RS_MAPPER['save_res'](data)
        pass


class General(ThiefBase):
    def target_id(self):
        return tools.md5_str(self.target_url)

    def fetch(self) -> (VideoInfo | PictureInfo, bytes | list[bytes]):
        url = self.target_url




if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'), threading.current_thread().name,threading.current_thread().ident,os.getpid())
    chromeExt.add_handler(rs_pipline)
    while True:
        url=input('请输入网址:').strip()
        chromeExt.open_new_tab(url)

    print('run ok', threading.current_thread().name,threading.current_thread().ident,os.getpid())
