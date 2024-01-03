import asyncio
import queue
import time

import tools
import threading
from websockets import serve
from asyncio import Queue as AQueue
from queue import Queue as NQueue
from utils.wx_dw_hosts import is_host_in_wxdw


__conn = None
__cmd_queue = AQueue()
__cmd_callback_handlers={}
__recv_handlers=set()
log=tools.get_logger()

def rs_mapper():
    url_tab={}
    res_dict={}
    res_queue=queue.Queue()
    def save_asso(asso):
        tabId=asso.get('tabId')
        url=asso.get('url')
        t=asso.get('t')
        url_tab[url]=tabId
        log.info(f'save-asso: tabId={tabId} time={t} url={url}')

    def save_res(res):
        tabId=res.get('tabId')
        reslist=res['list']
        url=reslist[0].get('webUrl')
        t=res.get('t')
        url_tab[url]=tabId
        log.info(f'save-res: tabId={tabId} time={t} res-list-len={len(reslist)} url={url} ')
        res_dict[tabId]=reslist
        res_queue.put(res)
        for item in reslist:
            iurl=item.get('url')
            is_host_in_wxdw(iurl)

    def hasTask(url,tabId):
        had=False
        if (url and url_tab.get(url)):
            had=True
        if tabId and not had:
            for tid in url_tab.values():
                if tid==tabId:
                    had= True
        log.info(f'check-browers-task: tabId={tabId} had={had} url={url}')
        return had

    def getRes(url,tabId):
        info=None
        if not tabId:
            tabId=url_tab.pop(url,None)
        if tabId:
            info=res_dict.pop(tabId,None)
        log.info(f'try-get-res: tabId={tabId} got={info is not None} url={url}')
        return info

    def waitRes(url,tabId):
        for i in range(60):
            log.info(f'wait-res: tabId={tabId} N={i} url={url}')
            info = getRes(url, tabId)
            if info:
                break
            time.sleep(1)
        return info


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
        'getRes':getRes,
        'waitRes':waitRes,
        'hasTask':hasTask,
        'ls':ls
    }
RS_MAPPER=rs_mapper()

def __rs_pipline(recv_msg):
    robj = tools.json_to_obj(recv_msg)
    tp=robj.get('tp')
    cmdId=robj.get('cmdId')
    if tp!='keep-alive':
        log.info(f'recv: tp={tp} cmdId={cmdId} content={recv_msg}')
    data = robj.get('data')
    if tp=='tab_created':
        RS_MAPPER['save_asso'](data)
    elif tp=='res':
        RS_MAPPER['save_res'](data)

    if cmdId and __cmd_callback_handlers.get(cmdId):
        rhandler = __cmd_callback_handlers.pop(cmdId)
        if rhandler:
            try:
                rhandler(cmdId,robj)
            except Exception as e:
                log.error(e,exc_info=True)

    for handler in __recv_handlers:
        try:
            handler and handler(robj,cmdId)
        except Exception as e:
            log.error(e,exc_info=True)

# def __rs_pipline(recv_msg):
#     for handler in __recv_handlers:
#         try:
#             handler and handler(recv_msg)
#         except Exception as e:
#             log.error(e,exc_info=True)

def add_handler(handler):
    __recv_handlers.add(handler)

def remove_handler(handler):
    __recv_handlers.remove(handler)

def __chrome_ctrlserver_start():
    async def cmd_send(jcmd):
        # log.info(f"cmd_sender got cmd: {jcmd}")
        try:
            await __conn.send(jcmd)
            log.info(f"cmd_sender send ok: {jcmd}")
        except Exception as e:
            log.error(e, exc_info=True)

    async def ws_main():
        log.info("chrome_ctrlserver ws_main starting...")
        async def echo(websocket, path):
            log.info("chrome_ctrlserver ws_echo starting...")
            global __conn
            __conn = websocket
            while True:
                recv_msg = await websocket.recv()
                __rs_pipline(recv_msg)
                # 获取下待下发命令
                try:
                    jcmd=__cmd_queue.get_nowait()
                    await cmd_send(jcmd)
                except:
                    pass

        async with serve(echo, '0.0.0.0', 8502):
            await asyncio.Future()

    async def cmd_sender():
        log.info("chrome_ctrlserver cmd_sender starting...")
        global __conn
        while True:
            if not __conn:
                # log.info(f"chrome_ctrlserver conn is None!")
                await asyncio.sleep(0.5)
                continue
            log.info(f"cmd_sender wait cmd...")
            jcmd = await __cmd_queue.get()
            await cmd_send(jcmd)

    loop = asyncio.new_event_loop()
    async def run():
        await asyncio.gather(ws_main(),cmd_sender())

    def sendCmd(cmdObj,callback=None):
        jcmd = tools.obj_to_json(cmdObj)
        cmdId=cmdObj.get('cmdId')
        __cmd_queue.put_nowait(jcmd)
        if callback:
            __cmd_callback_handlers[cmdId]=callback
        log.info(f'push cmd ok: Id={cmdId} {cmdObj}')

    def start():
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run())
        except Exception as e:
            log.error(e,exc_info=True)
        finally:
            loop.close()

    t= threading.Thread(target=start,daemon=True,name="chrome-controller")
    t.start()
    return sendCmd

__cmdSender=__chrome_ctrlserver_start()

def open_new_tab(url,callback=None,code=None):
    if not code:
        code=tools.md5_str(url)
    cmdId=tools.md5_str(url)
    cmdObj = {"command": "open_new_tab", "cmdId":cmdId,"opt": {"url": url,"code":code}}
    if callback:
        def fn(cmdId,robj):
            data = robj.get('data')
            tabId = data.get('tabId')
            url = data.get('url')
            t = data.get('t')
            log.info(f'open_new_tab-callback: tabId={tabId} cmdId={cmdId} time={t} url={url}')
            callback(tabId,url,t)
        __cmdSender(cmdObj,fn)
    else:
        __cmdSender(cmdObj)

def close_tab(tabId,callback=None):
    cmdObj = {"command": "close_tab", "opt": {"tabId": tabId}}
    __cmdSender(cmdObj,callback)

def get_res(url, tabId):
    r0 = RS_MAPPER['getRes'](url, tabId)
    return r0

def has_task(url, tabId):
    task = RS_MAPPER['hasTask'](url, tabId)
    return task

def wait_res(url, tabId):
    r0 = RS_MAPPER['waitRes'](url, tabId)
    return r0

def ls():
    RS_MAPPER['ls']()

def open_and_wait_res(url,tabId=None):
    r0 = get_res(url, tabId)
    # 如果没有则检查是否在加载中
    if not r0:
        task = has_task(url, tabId)
        if not task:
            tabId_rqueue = queue.Queue()
            def callback(tid, url, t):
                tabId_rqueue.put(tid)

            open_new_tab(url, callback)
            log.info(f'wait for open tab return: url={url}')
            try:
                tabId = tabId_rqueue.get(timeout=30)
            except Exception as e:
                log.warning(e, exc_info=True)

    r0 = wait_res(url, tabId)
    return r0