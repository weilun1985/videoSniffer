import asyncio
import json
import re,os
from datetime import datetime

import websockets

import tools
from thiefs.thiefBase import ThiefBase
from models import ResInfo,VideoInfo,PictureInfo


class General(ThiefBase):
    def target_id(self):
        return tools.md5_str(self.target_url)

    def fetch(self) -> (VideoInfo | PictureInfo, bytes | list[bytes]):
        url = self.target_url


def ws_server_run():
    async def main_logic(websocket, path):
        a=0
        while True:
            recv_msg=await websocket.recv()

            print(a,recv_msg)
            await websocket.send(tools.simpleTimeStr(datetime.now()))
            a+=1

    start_server = websockets.serve(main_logic, '0.0.0.0', 8502)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == '__main__':
    print('start at:',datetime.today().date().strftime('%Y%m%d %H:%M:%S'))
    ws_server_run()