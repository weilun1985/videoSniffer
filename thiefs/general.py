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

# def chrome_ctrlserver_start():
#     async def ws_main():
#         log.info("chrome_ctrlserver ws_main starting...")
#         async def echo(websocket, path):
#             log.info("chrome_ctrlserver ws_echo starting...")
#             global __conn
#             conn = websocket
#             while True:
#                 recv_msg = await websocket.recv()
#                 rs_pipline(recv_msg)
#
#         async with serve(echo, '0.0.0.0', 8502):
#             await asyncio.Future()
#
#     async def cmd_sender():
#         log.info("chrome_ctrlserver cmd_sender starting...")
#         global __conn
#         while True:
#             if not conn:
#                 log.info(f"chrome_ctrlserver conn is None!")
#                 await asyncio.sleep(0.5)
#                 continue
#             log.info(f"cmd_sender wait cmd...")
#             jcmd = await cmd_queue.get()
#             log.info(f"cmd_sender got cmd: {jcmd}")
#             try:
#                 await conn.send(jcmd)
#                 log.info(f"cmd_sender send ok: {jcmd}")
#             except Exception as e:
#                 log.error(e,exc_info=True)
#
#     loop = asyncio.new_event_loop()
#     async def run():
#         await asyncio.gather(ws_main(),cmd_sender())
#
#     def sendCmd(cmdObj):
#         jcmd = tools.obj_to_json(cmdObj)
#         cmd_queue.put_nowait(jcmd)
#         log.info(f'push cmd ok:{cmdObj}')
#
#     def start():
#         try:
#             asyncio.set_event_loop(loop)
#             loop.run_until_complete(run())
#         except Exception as e:
#             log.error(e,exc_info=True)
#         finally:
#             loop.close()
#
#     t= threading.Thread(target=start,daemon=True,name="chrome-controller")
#     t.start()
#     return sendCmd
#
# cmdSender=chrome_ctrlserver_start()
#
# def cmd_fetch(url):
#     cmdObj = {"command": "open_new_tab", "opt": {"url": url}}
#     cmdSender(cmdObj)

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
