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
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'}
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        }
        res = requests.get(url, headers=headers, allow_redirects=True)
        status_code =res.status_code
        html = res.text
        url2=res.url
        res.close()

        if status_code!=200:
            msg=f'未能正常加载目标网页，status={status_code} 目标url={url} 当前url={url2}'
            self.log.error(msg)
            raise Exception(msg)
        # if res.status_code==302:
        #     real_url = res.headers.get("location")
        #     res.close()
        #     res2 = requests.get(real_url, headers=headers)
        #     html = res2.text
        #     res2.close()
        try:
            i0=html.index('window.jsonData')
        except ValueError:
            msg = f'返回网页可能不是目标网页，status={status_code} 目标url={url} 当前url={url2}'
            self.log.error(msg)
            raise Exception(msg)

        str0=html[i0:]
        jstr = tools.tt(str0, '{', '}')
        data=json.loads(jstr)
        query_0 = 'curVideoMeta.playurl'
        video_url = tools.json_select(query_0, data)
        res_info = VideoInfo()
        res_info.res_type = 'video'
        res_info.res_url = video_url
        res_info.share_url = url

        match = re.search("<title>(.*?)</title>", html)
        title = match.group(1)
        res_info.name = title

        # test_dw(res_info.res_url)
        return res_info, None




def test_dw(url):
    url0='https://vd4.bdstatic.com/mda-pm833x8j2n4bzt09/720p_frame30/h264_cae_acd/1702098158625665451/mda-pm833x8j2n4bzt09.mp4?v_from_s=bdapp-resbox-zan-hnb'
    print(url0)
    print(url)
    res = requests.get(url, allow_redirects=False)
    real_url = res.headers.get("location")
    print(res.status_code)
    print(len(res.content))



if __name__ == '__main__':
    # shared_url='https://mbd.baidu.com/newspage/data/videolanding?nid=sv_4879939042257911735&sourceFrom=share'
    # shared_url='https://mbd.baidu.com/newspage/data/videolanding?nid=sv_7430501643266873810&sourceFrom=share'
    shared_url='https://mbd.baidu.com/newspage/data/videolanding?nid=sv_7430501643266873810&sourceFrom=share'
    baidu = Baidu(shared_url)
    info, data = baidu.fetch()
    print(info.__dict__)
