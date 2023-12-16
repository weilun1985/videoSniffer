import json
import re,os
import requests

import tools
from thiefs.thiefBase import ThiefBase
from models import ResInfo,VideoInfo,PictureInfo


class Baidu(ThiefBase):
    def target_id(self):
        return tools.md5_str(self.target_url)

    def fetch(self) -> (VideoInfo | PictureInfo, bytes | list[bytes]):
        url = self.target_url
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'}
        res = requests.get(url, headers=headers, allow_redirects=False)
        html = res.text
        real_url = res.headers.get("location")
        res.close()
        # print('\t', 'rel_url:', real_url)
        if real_url is not None:
            res2 = requests.get(real_url, headers=headers)
            html = res2.text
            res2.close()
        match = re.search("<title>(.*?)</title>", html)
        title = match.group(1)

        i0=html.index('window.jsonData')
        str0=html[i0:]
        jstr = tools.tt(str0, '{', '}')
        data=json.loads(jstr)
        query_0 = 'curVideoMeta.playurl'
        video_url = tools.json_select(query_0, data)
        res_info = VideoInfo()
        res_info.res_type = 'video'
        res_info.res_url = video_url
        res_info.share_url = url
        res_info.name = title
        return res_info, None


if __name__ == '__main__':
    shared_url='https://mbd.baidu.com/newspage/data/videolanding?nid=sv_4879939042257911735&sourceFrom=share'
    baidu = Baidu(shared_url)
    info, data = baidu.fetch()
    print(info.__dict__)
