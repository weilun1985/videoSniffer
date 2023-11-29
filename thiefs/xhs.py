# 小红书
import datetime
import re,os,logging
import requests
from thiefs.thiefBase import ThiefBase,VideoInfo,PictureInfo
from playwright.sync_api import sync_playwright


log=logging.getLogger("xhs")
__dir=os.path.dirname(os.path.realpath(__file__))
__name0=os.path.splitext(os.path.basename(__file__))[0]
state=os.path.join(__dir,f'{__name0}_state.txt')
log.info('state_file:%s',state)
playwright = sync_playwright().start()
browser = playwright.firefox.launch(headless=True)
context = browser.new_context(storage_state=state, ignore_https_errors=True)

# context = browser.new_context(ignore_https_errors=True)

def get_page(url):
    page = context.new_page()
    page.goto(url)
    log.info(f'goto:{url}')
    page.wait_for_load_state('networkidle')
    context.storage_state(path=state)
    return page

class Xhs(ThiefBase):

     def target_id(self):
         return os.path.basename(self.target_url)

     def fetch(self)->(VideoInfo|PictureInfo,bytes|list[bytes]):
        url = self.target_url
        page=get_page(url)
        html = page.content()
        title,context =None,None
        title_ele=page.query_selector('#detail-title')
        content_ele=page.query_selector('#detail-desc')
        if title_ele is not None:
            title=title_ele.inner_text()
        if content_ele is not None:
            content=content_ele.inner_text()

        # context.close()
        # browser.close()
        # playwright.stop()

        if title is None:
            title = re.search('<title>(.+?)</title>', html).group(1)
        videos = re.findall('http:[\w\\\.\-]+?\.mp4', html)
        video_url = videos[0]
        video_url = video_url.replace('\\u002F', '/')

        info = VideoInfo()
        info.share_url = self.target_url
        info.name=title
        info.content=content
        info.res_url=video_url

        data=None
        if not self.check_resfile_exist('video',video_url):
            log.info(f'start download: {title} {video_url}')
            try:
                resp = requests.get(video_url)
                if resp.status_code != 200:
                    log.warning(f'download_res_fail: status={resp.status_code} res_url={video_url}', )
                else:
                    data=resp.content
                    info.res_downloaded=True
            except Exception as e:
                log.error(e)
        return info,data


if __name__ == '__main__':
    shared_url='http://xhslink.com/jQn5Gw'
    xhs=Xhs(shared_url)
    info,data=xhs.fetch()
    print(info.__dict__)