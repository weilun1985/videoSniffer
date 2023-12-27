import asyncio
import tools
import threading
from websockets import serve
from asyncio import Queue as AQueue
from queue import Queue as NQueue


__conn = None
__cmd_queue = AQueue()
log=tools.get_logger()
__recv_handlers=set()

def __rs_pipline(recv_msg):
    for handler in __recv_handlers:
        try:
            handler and handler(recv_msg)
        except Exception as e:
            log.error(e,exc_info=True)

def add_handler(handler):
    __recv_handlers.add(handler)

def remove_handler(handler):
    __recv_handlers.remove(handler)

def __chrome_ctrlserver_start():
    async def ws_main():
        log.info("chrome_ctrlserver ws_main starting...")
        async def echo(websocket, path):
            log.info("chrome_ctrlserver ws_echo starting...")
            global __conn
            __conn = websocket
            while True:
                recv_msg = await websocket.recv()
                __rs_pipline(recv_msg)

        async with serve(echo, '0.0.0.0', 8502):
            await asyncio.Future()

    async def cmd_sender():
        log.info("chrome_ctrlserver cmd_sender starting...")
        global __conn
        while True:
            if not __conn:
                log.info(f"chrome_ctrlserver conn is None!")
                await asyncio.sleep(0.5)
                continue
            log.info(f"cmd_sender wait cmd...")
            jcmd = await __cmd_queue.get()
            log.info(f"cmd_sender got cmd: {jcmd}")
            try:
                await __conn.send(jcmd)
                log.info(f"cmd_sender send ok: {jcmd}")
            except Exception as e:
                log.error(e,exc_info=True)

    loop = asyncio.new_event_loop()
    async def run():
        await asyncio.gather(ws_main(),cmd_sender())

    def sendCmd(cmdObj):
        jcmd = tools.obj_to_json(cmdObj)
        __cmd_queue.put_nowait(jcmd)
        log.info(f'push cmd ok:{cmdObj}')

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

def open_new_tab(url):
    cmdObj = {"command": "open_new_tab", "opt": {"url": url}}
    __cmdSender(cmdObj)

def close_tab(tabId):
    cmdObj = {"command": "close_tab", "opt": {"tabId": tabId}}
    __cmdSender(cmdObj)