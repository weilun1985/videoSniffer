import requests

import tools
from models import VideoInfo, PictureInfo
from thiefs.thiefBase import ThiefBase
from urllib.parse import urlencode


class TTT(ThiefBase):
    def __init__(self, sharedObj, target_url: str = None, trigger_time: int = None):
        super().__init__(sharedObj, target_url, trigger_time)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090922) XWEB/8555',
            'Referer': 'https://servicewechat.com/wxfb858b283c41a07f/18/page-frame.html',
            'xweb_xhr': '1'
        }

    def target_id(self):
        return tools.md5_str(self.target_url)

    def _get_file_info(self,path):
        size, type = 0, ''
        params={'url':path}
        encoded_params = urlencode(params)
        url1 = f'https://vdp.weilaizhihui.com/fileinfo?{encoded_params}'
        resp0 = requests.get(url1, headers=self.headers, allow_redirects=True)
        status_code = resp0.status_code
        if status_code == 200:
            rj0 = resp0.json()
            r0 = resp0.text
            resp0.close()
            if rj0 and rj0.get('data'):
                size = rj0.get('data').get('size')
                type = rj0.get('data').get('type')
        else:
            msg = f'未能获取到文件信息，status={status_code} 目标url={path}'
            self.log.error(msg)
        return size,type


    def fetch(self) -> (VideoInfo | PictureInfo, bytes | list[bytes]):
        url0='https://vdp.weilaizhihui.com/media'

        re_url = self.target_url
        resp0 = requests.post(url0, headers=self.headers, data={'p': re_url}, allow_redirects=True)
        status_code = resp0.status_code
        if status_code != 200:
            msg = f'未能正常解析目标网页资源，status={status_code} 目标url={re_url}'
            self.log.error(msg)
            raise Exception(msg)
        rj0 = resp0.json()
        r0 = resp0.text
        resp0.close()

        res_info=None

        if rj0.get('imgs') and len(rj0['imgs'])>0:
            # 图片资源
            res_info = PictureInfo()
            res_info.res_type = 'picture'
            for src in rj0['imgs']:
                res_info.res_url_list.append(src)
                # if size:
                #     res_info.res_size_list.append(size)
        elif rj0.get('main') and len(rj0['main'])>0:
            # 视频资源
            res_info = VideoInfo()
            res_info.res_type = 'video'
            video_url = rj0['main']
            res_info.res_url = video_url
            res_info.res_cover_url = rj0.get('cover')
            size,type=self._get_file_info(video_url)
            res_info.res_size = size
        if res_info:
            res_info.share_url = re_url
            res_info.name = rj0.get('tit')

        return res_info, None


if __name__ == '__main__':
    # shared_url = 'http://xhslink.com/jQn5Gw'
    shared_url='https://www.xiaohongshu.com/explore/65644c11000000003300a4f1?app_platform=android&app_version=8.16.0&ignoreEngage=true&share_from_user_hidden=true&type=normal&xhsshare=CopyLink&appuid=58c1fc305e87e77809373841&apptime=1701620001'
    # shared_url='79 狗眼看时间发布了一篇小红书笔记，快来看吧！ 😆 W5ic3rc3vOtB0vl 😆 http://xhslink.com/BRuHPB，复制本条信息，打开【小红书】App查看精彩内容！'
    ttt = TTT(shared_url)
    info, data = ttt.fetch()
    print(info.__dict__)