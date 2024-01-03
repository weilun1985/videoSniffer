import os.path
import tools
from urllib.parse import urlparse

HOSTSET_WX_DW="VideoSniffer:HostSet:WxDw"
HOSTSET_NOT_WX_DW="VideoSniffer:HostSet:Not_WxDw"
__name,__ext=os.path.splitext(__file__)
__dir=os.path.dirname(os.path.abspath(__file__))
__host_file=os.path.join(__dir,f'{__name}.txt')


if os.path.exists(__host_file):
    with open(__host_file) as file:
        lines_list = [line.strip() for line in file.readlines() if line.strip()]
    if len(lines_list)>0:
        redis=tools.get_redis()
        # 清空原有的
        redis.delete(HOSTSET_WX_DW)
        # 写入新的列表
        redis.sadd(HOSTSET_WX_DW,*lines_list)
        # redis.close()

def is_host_in_wxdw(url):
    p_url=urlparse(url)
    host=p_url.hostname
    redis = tools.get_redis()
    is_in=redis.sismember(HOSTSET_WX_DW,host)
    if not is_in:
        redis=tools.get_redis()
        redis.sadd(HOSTSET_NOT_WX_DW,host)
        # redis.close()
        print(f'record not in download host:{host}')

    return is_in

