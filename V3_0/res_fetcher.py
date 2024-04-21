import re
import time

import requests
import utils
import wechatUtils
import user_center
from lxml import etree
import res_db
import counter
from models import VideoInfo, PictureInfo,res_info_stringfy
from urllib.parse import urlencode,unquote_plus

KEY_FETCHER_TASK='VideoSniffer:third_taskQueue'
forword_third=['25984985637719491@openim']
log=utils.get_logger()
headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090922) XWEB/8555',
            'Referer': 'https://servicewechat.com/wxfb858b283c41a07f/18/page-frame.html',
            'xweb_xhr': '1'
        }


def on_msg(msg):
    msg_type = msg["msg_type"]
    is_self_msg = msg["is_self_msg"]
    is_chat_room = msg.get('is_chatroom')
    is_at_me = msg.get('at_me')
    sender = msg.get('sender')

    # 自己发的消息，或者群里发的但是没有AT自己的消息，忽略
    if is_self_msg or (is_chat_room and not is_at_me):
        return
    reply_to_msg = msg
    if not sender in forword_third:
        def on_new_user(uinfo):
            wechatUtils.send_wx_text_reply(reply_to_msg,
                                           'Hi 新朋友您好，我是您的自媒体素材小助手，目前我已经学会了帮助您下载各大主流媒体平台的无水印视频/图片素材，包括小红书/快手/抖音/视频号/百度/微博……可以关注我的朋友圈获得具体使用方法及后续其他相关信息，另外您在使用过程中碰到任何问题都可以直接微信留言给我哈。')
            counter.set_new_user(reply_to_msg.get('sender'))
            pass

        user_center.check_new_user(sender, on_new_user)


    if msg_type == 37:
        # 同意添加好友申请
        log.info(f"好友申请：{sender}")
        return

    elif msg_type in [3, 43, 493]:
        wechatUtils.send_wx_text_reply(reply_to_msg,
                                       '抱歉哈，目前还不支持直接发图片/视频文件去除水印的方式，您可以把对应图片/视频的分享链接发给我，我帮您直接下载没有水印的素材。')
        log.info(f"不支持的消息类型：{msg_type}")
        return

    try:
        code, res_info, reply_to_msg = fecth(msg)
        if code == 200:
            wechatUtils.send_wx_resApp_reply(reply_to_msg, res_info)
        elif code == 404:
            wechatUtils.send_wx_text_reply(reply_to_msg, '抱歉哈，我们暂时还没找到对应的资源，程序员小哥哥会抓紧解决哈。')

    except Exception as e:
        log.error(e, exc_info=True)
        wechatUtils.send_wx_text_reply(reply_to_msg, '抱歉哈，我好像出现了点故障，请您稍后再试。')

def fecth(msg):
    msg_type = msg["msg_type"]
    content = msg.get('content')
    msg_id = msg.get("msg_id")
    sender = msg.get('sender')
    counter.set_active_user(sender)
    counter.incr_fetchd()

    code,res_info,reply_msg,shared_title,shared_url=404,None,msg,None,None
    # code：200=成功，404=没有找到资源，302=重定向，400=信息中不存在资源分享链接
    cached=False
    if sender in forword_third:
        rs=recv_third_result(msg)
        if rs:
            res_info, reply_msg,shared_title,shared_url=rs
            if res_info is not None:
                code=200
                res_db.setResInfoToRedis(res_info)
                log.info(
                    f'找到资源：用户={reply_msg.get("wx_id")} {reply_msg.get("sender")} 缓存={cached}\r\n{res_info_stringfy(res_info)}')
                return code, res_info, reply_msg
        return 0,None,None


    app_id,app_msg_type=None,None
    # 第一步：获取资源的分享链接
    if msg_type == 1:
        # 从文本中找链接
        match = re.search(utils.URL_PATTERN, content)
        if match is not None:
            shared_url = match.group(0)
    elif msg_type in [49, 492]:
        app_info=wechatUtils.get_wxapp_info(content)
        app_id=app_info.get('app_id')
        app_msg_type=app_info.get('app_msg_type')
        shared_url=app_info.get('url')
        shared_title=app_info.get('title')
        if utils.is_empty_str(shared_title):
            shared_title=app_info.get('des')
    # 不存在分享链接
    if utils.is_empty_str(shared_url):
        return 400, res_info, reply_msg


    # 第二步：缓存中找
    res_id=utils.md5_str(shared_url)
    res_info=res_db.getResInfoFromRedis(res_id)
    if res_info is not None:
        return 200, res_info, reply_msg

    # 第三步：新获取
    # 微信视频号，转发
    if utils.is_empty_str(app_id) and app_msg_type == '51':
        # 微信视频号，转发
        forword_fetch(shared_title, shared_url, msg)
        code = 302
        log.info(f'Fetch转发:{shared_title} {shared_url}')
        return code, res_info, reply_msg

    # 非微信视频号，获取
    res_info = fetch_by_shared_url(shared_url)
    if res_info:
        code = 200
        res_db.setResInfoToRedis(res_info)
        log.info(
            f'找到资源：用户={reply_msg.get("wx_id")} {reply_msg.get("sender")} 缓存={cached}\r\n{res_info_stringfy(res_info)}')
    else:
        code = 404
    return code,res_info,reply_msg



def push_task_info(shared_title,shared_url,task_msg):
    task_info={'shared_title':shared_title,'shared_url':shared_url,'task_msg':task_msg}
    jstr = utils.obj_to_json(task_info)
    redis = utils.get_redis()
    redis.lpush(KEY_FETCHER_TASK, jstr)

def pop_task_info():
    redis = utils.get_redis()
    temp = redis.lpop(KEY_FETCHER_TASK)
    if temp is None:
        return
    task = utils.json_to_obj(temp)
    return task



def recv_third_result(msg):
    msg_type = msg["msg_type"]
    if msg_type == 494:
        # 第三方返回回来的结果消息
        content = msg.get('content')
        root = etree.fromstring(content)
        weapp_id_node=root.find(".//appmsg/weappinfo/appid")
        weapp_id=weapp_id_node.text if weapp_id_node is not None else None

        if not weapp_id=='wxfb858b283c41a07f':
            # 不是微抖下载器的结果，返回
            return


        titlenode = root.find(".//appmsg/title")
        title = titlenode.text if titlenode is not None else None
        pagepathnode = root.find(".//appmsg/weappinfo/pagepath")
        pagepath = pagepathnode.text if pagepathnode is not None else None
        if not pagepath:
            return
        a = len('pages/index/detail.html?')
        if a < 0:
            log.warning(f'转发返回的资源地址格式异常：{pagepath}')
            return
        p,t,i=utils.get_url_query_values(pagepath,"p","t","i")
        if t and len(t)>0:
            title=t
        elif title and len(title)>5:
            title=title[5:]
        res_info=None
        if p and p.startswith('http'):
            res_url = p
            file_info = get_file_info(res_url)
            if not file_info:
                # 没找到资源的信息
                log.warning(f'不存在指定资源的文件信息：{title} {res_url}')
                return
            res_info = VideoInfo()
            res_info.res_type = 'video'
            res_info.res_url = res_url
            res_info.res_size = file_info[0]

        elif i and i.startswith('http'):
            res_info = PictureInfo()
            res_info.res_type = 'picture'
            pic_arr = i.split('@@')
            if len(pic_arr)==1:
                src=pic_arr[0]
                res_info.res_url_list.append(src)
            else:
                for i in range(1,len(pic_arr)):
                    src=pic_arr[0]+pic_arr[i]
                    res_info.res_url_list.append(src)

        res_info.name = title

        task_info=pop_task_info()
        if not task_info:
            log.error(f'未找到对应资源的回调记录：{title}')
            return
        task_msg = task_info['task_msg']
        shared_url=task_info['shared_url']
        shared_title=task_info['shared_title']
        res_info.id=utils.md5_str(shared_url)
        res_info.share_url = shared_url
        res_info.got_time = int(time.time())
        return res_info, task_msg,shared_title,shared_url

def fetch_by_shared_url(shared_url):
    url0 = 'https://vdp.weilaizhihui.com/media'
    resp0 = requests.post(url0, headers=headers, data={'p': shared_url}, allow_redirects=True)
    status_code = resp0.status_code
    if status_code != 200:
        msg = f'未能正常解析目标网页资源，status={status_code} 目标url={shared_url}'
        log.error(msg)
        raise Exception(msg)
    rj0 = resp0.json()
    r0 = resp0.text
    log.info(f'fecth from share_url: {shared_url}\r\n{r0}')
    resp0.close()

    res_info = None
    if rj0:
        if rj0.get('imgs') and len(rj0['imgs']) > 0:
            # 图片资源
            res_info = PictureInfo()
            res_info.res_type = 'picture'
            for src in rj0['imgs']:
                res_info.res_url_list.append(src)
                # if size:
                #     res_info.res_size_list.append(size)
        elif rj0.get('main') and len(rj0['main']) > 0:
            # 视频资源
            res_info = VideoInfo()
            res_info.res_type = 'video'
            video_url = rj0['main']
            url_prefix='https://dwn.weilaizhihui.com/down?q='
            if video_url.startswith(url_prefix):
                a=len(url_prefix)
                video_url=video_url[a:]
                video_url=unquote_plus(video_url)
                # video_url=utils.get_url_query_value(video_url,'q')
            res_info.res_url = video_url
            res_info.res_cover_url = rj0.get('cover')

            finfo=get_file_info(video_url)
            if finfo:
                size=finfo[0]
                type=finfo[1]
                res_info.res_size = size
            else:
                log.warning(f'未能获取到找视频资源的文件信息：\r\n分享链接= {shared_url}\r\n资源URL= {video_url}')
                return None
    if res_info:
        res_info.share_url = shared_url
        res_info.id = utils.md5_str(shared_url)
        tit=rj0.get('tit')
        if tit or not tit=='平台提示当前链接已是无水印视频请勿重复提交':
            res_info.name = rj0.get('tit')
        res_info.got_time = int(time.time())
    return res_info

def forword_fetch(shared_title,shared_url,msg):
    push_task_info(shared_title,shared_url,msg)
    wechatUtils.msg_send_inqueue({
        'action': 'forward_msg',
        'sender': msg.get('self_wx_id'),
        'options': {
            'to_wx': forword_third[0],
            'msg_id': msg.get("msg_id")
        }
    })

def get_file_info(path):
    # size, type = 0, ''
    params={'url':path}
    encoded_params = urlencode(params)
    url1 = f'https://vdp.weilaizhihui.com/fileinfo?{encoded_params}'
    resp0 = requests.get(url1, headers=headers, allow_redirects=True)
    status_code = resp0.status_code
    if status_code == 200:
        rj0 = resp0.json()
        r0 = resp0.text
        resp0.close()
        log.info(f'get file info: {path}\r\n{r0}')
        if rj0 and rj0.get('data'):
            status_code= rj0.get('code')
            if status_code ==200:
                size = rj0.get('data').get('size')
                type = rj0.get('data').get('type')
                log.info(
                    f'成功获取到资源信息：{status_code}\r\n资源URL= {path}\r\n 资源大小= {utils.filesize_exp(size)} 类型= {type}')
                return size,type
    msg = f'未能获取到资源信息，status={status_code} 目标url={path}'
    log.error(msg)


def re_fetch(res_id):
    res_info=res_db.getResInfoFromRedis(res_id)
    if res_info is None:
        return 404
    share_url=res_info.share_url
    res_info_new=fetch_by_shared_url(share_url)
    if res_info_new is None:
        return 404
    # 刷入缓存
    res_db.setResInfoToRedis(res_info_new)
    return res_info_new