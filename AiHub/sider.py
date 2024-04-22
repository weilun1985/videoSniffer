import asyncio
import aiohttp
import json
import requests
from http.cookies import SimpleCookie

from sseclient import SSEClient


async def send_post_request(url, json_data, headers=None,cookies=None):
    async with aiohttp.ClientSession(headers=headers,cookies=cookies) as session:
        async with session.post(url, data=json_data, headers=headers,cookies=cookies) as response:
            async for line in response.content:
                if line:
                    data = line.decode('utf-8').strip()
                    print(data)  # 输出SSE数据

def parse_cookie_string(cookie_str):
    cookie_map = {}
    cookie = SimpleCookie()
    cookie.load(cookie_str)

    for key, morsel in cookie.items():
        cookie_map[key] = morsel.value

    return cookie_map

url = 'https://sider.ai/api/v2/completion/text'
post_data = {"prompt":"接下来的世界经济形式会怎么样？","stream":True,"app_name":"ChitChat_Chrome_Ext","app_version":"4.8.0","tz_name":"Asia/Shanghai","cid":"C0ZZSM03N2R1","model":"gpt-3.5","search":False,"auto_search":False,"filter_search_history":False,"from":"chat","group_id":"default","chat_models":[],"tools":{"auto":["text_to_image","search","data_analysis"]}}
custom_headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5Njk3NzIxLCJyZWdpc3Rlcl90eXBlIjoicGhvbmUiLCJhcHBfbmFtZSI6IkNoaXRDaGF0X01hYyIsInRva2VuX2lkIjoiMjYzMjc0ZWItNDFkNC00MmQxLThkMjUtYTk2M2Q3ZTJlY2VhIiwiaXNzIjoic2lkZXIuYWkiLCJhdWQiOlsiIl0sImV4cCI6MTc0MzU5ODg1OCwibmJmIjoxNzEyNDk0ODU4LCJpYXQiOjE3MTI0OTQ4NTh9.dqpmuzAhBapFiWNepF2RI0s-BLxjDXI3gGtw_K3Y7nY',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Origin':'chrome-extension://difoiogjjojoaoomphldepapgpbgkhkb',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

cookie_str='_ga=GA1.1.1468870152.1712494801; _gcl_au=1.1.1742065004.1712494801; lang=zh_CN; _clck=65zy1f%7C2%7Cfkq%7C0%7C1558; _uetvid=c0fa5000f4de11eeb5cce16764f9e3fe; token=Bearer%20eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5Njk3NzIxLCJyZWdpc3Rlcl90eXBlIjoicGhvbmUiLCJhcHBfbmFtZSI6IkNoaXRDaGF0X01hYyIsInRva2VuX2lkIjoiMjYzMjc0ZWItNDFkNC00MmQxLThkMjUtYTk2M2Q3ZTJlY2VhIiwiaXNzIjoic2lkZXIuYWkiLCJhdWQiOlsiIl0sImV4cCI6MTc0MzU5ODg1OCwibmJmIjoxNzEyNDk0ODU4LCJpYXQiOjE3MTI0OTQ4NTh9.dqpmuzAhBapFiWNepF2RI0s-BLxjDXI3gGtw_K3Y7nY; refresh_token=discard; userinfo-avatar=https://chitchat-avatar.s3.amazonaws.com/default-avatar-7.png; userinfo-type=phone; userinfo-name=%E5%B7%8D%E4%BB%91; pricingTrigger=web_f_my_overview; _ga_0PRFKME4HP=GS1.1.1713460298.3.1.1713460362.0.0.0; CloudFront-Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9maWxlLWNkbi5zaWRlci5haS9pbWFnZS9VMEtBSFpKSkFMMi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzE2Mjk2NzU4fX19XX0_; CloudFront-Signature=DXYKWg~Xf9k~SuNzNSsHuh9kYIcxbKn02~waYJ~5QLjYuOuCTJlVZYl58EoEO0nLWZZ7EvbyT-AecBWf0ipmUhKZzCgRuN4pNgXro-CnQhIwzazJFjP4wxlCem6DR4IkGlJL~sePMld95B4viekdPUwrvAU~HT0FC1qNId-1yWPZYvqPoPTvp5zT0CFKy9O9YL1gDbC~l4DRANVlP70dK0vl-TMFUxQRZ1MHkHo92J-LowldE4Go1f4g4nVrjkCmPmUf5CBgZ00uUYScW6rN7BaQR71W0wiXH7EPQNGOpVpsSyKlFTWCZIL8D42v28adGs8~AZ88mNTDypYhZZArQQ__; CloudFront-Key-Pair-Id=K344F5VVSSM536'
custom_cookies=parse_cookie_string(cookie_str)



async def main():
    await send_post_request(url, json_data=json.dumps(post_data), headers=custom_headers,cookies=custom_cookies)


def test0():
    response = requests.post(url, headers=custom_headers, cookies=custom_cookies, data=json.dumps(post_data), stream=True)
    client = SSEClient(response)
    for event in client.events():
        print(event.data)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # test0()
