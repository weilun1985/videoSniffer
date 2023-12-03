import re
import uuid
import requests


# 抽取文本中的url
def find_url(string):
    tmp = string.replace("，", " ")
    return re.search("(?P<url>https?://[^\s]+)", tmp).group("url")


# 下载视频到本地
def download(url):
    r = requests.get(url, stream=True)
    with open(str(uuid.uuid4())+".mp4", "wb") as f:
        for chunk in r.iter_content(chunk_size=512):
            f.write(chunk)

# 解析视频链接
def get_video_url(url):
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'}
    res = requests.get(url, headers=headers, allow_redirects=False)
    html=res.text
    real_url = res.headers.get("location")
    print('\t','rel_url:',real_url)
    if real_url is not None:
        res2 = requests.get(real_url, headers=headers)
        html=res2.text
    video_key = re.findall(r'"originVideoKey":"(.*?)"', html)[0]
    video_key = video_key.replace("\\u002F", "/")
    video_url = "http://sns-video-bd.xhscdn.com/" + video_key
    # print(video_url)
    return video_url


if __name__ == '__main__':
    shareLinks = ["""4 素昭发布了一篇小红书笔记，快来看吧！ 😆 8RbAPTyVecUiArU 😆 http://xhslink.com/MhQAax，复制本条信息，打开【小红书】App查看精彩内容！""",
                 'https://www.xiaohongshu.com/explore/6566e0f6000000003c013e41?app_platform=android&app_version=8.16.0&ignoreEngage=true&share_from_user_hidden=true&type=video&xhsshare=CopyLink&appuid=58c1fc305e87e77809373841&apptime=1701616223',
                 'https://www.xiaohongshu.com/explore/6566e0f6000000003c013e41?app_platform=android&app_version=8.16.0&ignoreEngage=true&share_from_user_hidden=true&type=video&xhsshare=WeixinSession&appuid=58c1fc305e87e77809373841&apptime=1701616277']
    for shk in shareLinks:
        url = find_url(shk)
        print('url-0:',url)
        video_url = get_video_url(url)
        print('video_url:',video_url)
    # download(video_url)
