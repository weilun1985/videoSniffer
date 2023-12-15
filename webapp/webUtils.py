import asyncio
import aiohttp
import message_center
import models
import tools
from sanic.response.types import ResponseStream,HTTPResponse
from typing import (
    Dict,
    Optional,
    Union
)
from sanic.log import logger

async def res_proxy(
    id: str,
    n:int,
    headers: Optional[Dict[str, str]] = None
) -> Union[ResponseStream,HTTPResponse]:
    headers = headers or {}
    # content_length = None
    # content_type = None
    status: int = 200
    data = message_center.getResInfoFromRedis(id)
    if data is None:
        return HTTPResponse(status=404)

    if isinstance(data, models.VideoInfo):
        real_url = data.res_url
        content_type = 'video/mpeg4'
        # status=206
    elif isinstance(data, models.PictureInfo):
        real_url = data.res_url_list[n]
        content_type = 'image/jpeg'
    else:
        return HTTPResponse(status=404)

    session=aiohttp.ClientSession()
    resp=await session.get(real_url)
    logger.info(f'resproxy: id={id} n={n} real_url={real_url} size={tools.filesize_exp(resp.content_length)}')
    content_length=resp.content_length
    if content_length and content_length>0:
        headers["content-length"] = resp.content_length
        if status==206:
            headers["content-range"] = f"bytes {0}-{content_length}/{content_length}"

    async def _streaming_fn(response):
        try:
            while True:
                chunk = await resp.content.read(1024)
                if not chunk:
                    break
                await response.write(chunk)
        finally:
            resp.close()
            await session.close()
            logger.info('aiohttp-closed!')

    # async def _streaming_fn(response):
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(real_url) as resp:
    #             logger.info(f'resproxy: id={id} n={n} real_url={real_url} size={tools.filesize_exp(resp.content_length)}')
    #             if resp.content_length:
    #                 response.response.headers['Content-Length']=resp.content_length
    #             while True:
    #                 chunk=await resp.content.read(1024)
    #                 if not chunk:
    #                     break
    #                 await response.write(chunk)
    return ResponseStream(
        streaming_fn=_streaming_fn,
        status=status,
        headers=headers,
        content_type=content_type
    )

async def test():
    url = 'http://sns-video-bd.xhscdn.com/pre_post/1040g0cg30rov4oev2m605ooklj4lajdmpdrum78'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.content_length:
                content_length = resp.content_length
                print('content_length: ',content_length)
            if resp.content_type:
                content_type = resp.content_type
                print('content_type: ', content_type)
            while True:
                chunk = await resp.content.read(1024)
                if not chunk:
                    break
                print(len(chunk))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())



