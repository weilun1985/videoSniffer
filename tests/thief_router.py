import re
from thiefs.thiefBase import ThiefBase
from thiefs.xhs import Xhs

def do_route(shared_text)->ThiefBase|None:
    match = re.search('(http|https)://([\w\.]+)/[\w/?=&]+', shared_text)
    if match is None:
        return
    host = match.group(2)
    url = match.group(0)
    thief: ThiefBase = None
    if host == 'xhslink.com':
        thief = Xhs(url)
    elif host == 'v.douyin.com':
        pass
    elif host == 'mr.baidu.com':
        pass
    return thief



if __name__ == '__main__':
    shared_text='52 环球超级豪墅发布了一篇小红书笔记，快来看吧！ aPyV0bLjjACXCuO http://xhslink.com/J3E9vw，复制本条信息，打开【小红书】App查看精彩内容！'
    thief=do_route(shared_text)
    print(thief.name,thief.target_url,thief.target_id())
    info=thief.go()
    print(info.__dict__)

