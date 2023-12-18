import json
import re,os
import requests

import tools
from thiefs.thiefBase import ThiefBase
from models import ResInfo,VideoInfo,PictureInfo


class Xhs(ThiefBase):

    def target_id(self):
        return tools.md5_str(self.target_url)
        # return os.path.basename(self.target_url)

    def fetch(self) -> (VideoInfo | PictureInfo, bytes | list[bytes]):
        url = self.target_url
        headers = {
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
        }
        res = requests.get(url, headers=headers, allow_redirects=True)
        status_code = res.status_code
        html = res.text
        url2 = res.url
        res.close()

        if status_code != 200:
            msg = f'未能正常加载目标网页，status={status_code} 目标url={url} 当前url={url2}'
            self.log.error(msg)
            raise Exception(msg)

        match=re.search("window.__INITIAL_STATE__=(\{.+\})",html)
        if match is None:
            return
        jstr=match.group(1)
        jstr=jstr.replace('undefined','null')
        data=json.loads(jstr)

        # 判断是video 还是 图文
        query_0 = 'note.noteDetailMap.*.note|[0]'
        rs_0=tools.json_select(query_0,data)
        tp=tools.json_select('type', rs_0)
        res_info:ResInfo=None
        if tp=='video':
            video_key=tools.json_select('video.consumer.originVideoKey',rs_0)
            video_key = video_key.replace("\\u002F", "/")
            video_url = "https://sns-video-bd.xhscdn.com/" + video_key

            res_info = VideoInfo()
            res_info.res_type='video'
            res_info.res_url = video_url

            # finfo=tools.remote_file_info(video_url)
            # if finfo:
            #     size=finfo.get('Content-Length')
            #     res_info.res_size=size
            pass
        elif tp=='normal':
            rs_1=tools.json_select('imageList[].infoList[1].url', rs_0)
            res_info = PictureInfo()
            res_info.res_type = 'picture'
            for pic in rs_1:
                if pic.startswith("http:"):
                    pic=f'https:{pic[5:]}'
                res_info.res_url_list.append(pic)
        title=tools.json_select('title',rs_0)
        content=tools.json_select('desc',rs_0)
        res_info.share_url = url
        res_info.name = title
        res_info.content = content
        return res_info, None



if __name__ == '__main__':
    # shared_url = 'http://xhslink.com/jQn5Gw'
    shared_url='https://www.xiaohongshu.com/explore/65644c11000000003300a4f1?app_platform=android&app_version=8.16.0&ignoreEngage=true&share_from_user_hidden=true&type=normal&xhsshare=CopyLink&appuid=58c1fc305e87e77809373841&apptime=1701620001'
    xhs = Xhs(shared_url)
    info, data = xhs.fetch()
    print(info.__dict__)