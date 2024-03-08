import re
from queue import Queue
import res_db
from lxml import etree
import requests
import utils
from models import VideoInfo, PictureInfo
from urllib.parse import urlencode,unquote_plus
import user_center


log=utils.get_logger()
headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090922) XWEB/8555',
            'Referer': 'https://servicewechat.com/wxfb858b283c41a07f/18/page-frame.html',
            'xweb_xhr': '1'
        }
# URL_PATTERN="(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*(\?[^\s\?\u4e00-\u9fa5\uFF00-\uFF5F\<\>\#\{\}|\^~\[ \]#]*)?(#[\w-]*)?"
URL_PATTERN="(https?:\/\/)([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)*(\?[^\s\?\u4e00-\u9fa5\uFF00-\uFF5F\<\>\#\{\}|\^~\[ \]#]*)?(#[\w-]*)?"
forword_third=['25984985637719491@openim']
forword_fetch_queue=Queue()
app_url = '#小程序://照片去水印小助手/ZzNbrUhZyxxCyut'

def on_msg(wxapi,myinfo,msg):
    msg_type = msg["msg_type"]
    is_self_msg=msg["is_self_msg"]
    is_chat_room=msg.get('is_chatroom')
    is_at_me=msg.get('at_me')
    sender = msg.get('sender')
    reply_to_msg = msg
    # 自己发的消息，或者群里发的但是没有AT自己的消息，忽略
    if is_self_msg or (is_chat_room and not is_at_me):
        return
    if not sender in forword_third:
        def on_new_user(uinfo):
            send_wx_text_reply(wxapi, reply_to_msg,
                               'Hi 新朋友您好，我是您的自媒体素材小助手，目前我已经学会了帮助您下载各大主流媒体平台的无水印视频/图片素材，包括小红书/快手/抖音/视频号/百度/微博……可以关注我的朋友圈获得具体使用方法及后续其他相关信息，另外您在使用过程中碰到任何问题都可以直接微信留言给我哈。')
            pass
        user_center.check_new_user(sender,on_new_user)


    exception_reply, res_info = None, None

    if msg_type == 37:
        # 同意添加好友申请
        wxapi.agree_friend(msg_data=msg)
        return
    elif msg_type in [3,43,493]:
        exception_reply = '抱歉哈，目前还不支持直接发图片/视频文件去除水印的方式，您可以把对应图片/视频的分享链接发给我，我帮您直接下载没有水印的素材。'


    if not exception_reply:
        if not is_res_task(msg):
            log.info(f'非任务对话：{utils.wx_msg_tostring(msg)}')
            return
        try:
            if sender in forword_third:
               r=forword_fetch(wxapi,msg)
               if r:
                   res_info, reply_to_msg=r[0],r[1]
            else:
                res_info=fetch(wxapi,msg)
        except Exception as e:
            exception_reply=str(e)
            log.error(e,exc_info=True)


    if exception_reply:
        send_wx_text_reply(wxapi,reply_to_msg,exception_reply)
    elif res_info:
        # log.info(f'找到资源： 类型={type(res_info).__name__} 名称={res_info.name} 数量={1 if isinstance(res_info,VideoInfo) else len(res_info.res_url_list)} 用户={reply_to_msg.get("wx_id")} {reply_to_msg.get("sender")}\r\n分享链接={res_info.share_url}\r\n')
        log.info(
            f'找到资源：用户={reply_to_msg.get("wx_id")} {reply_to_msg.get("sender")}\r\n{utils.res_info_stringfy(res_info)}')
        res_id=res_info.id
        if isinstance(res_info,VideoInfo):
            send_wx_text_reply(wxapi,reply_to_msg,'为您找到1个视频:')
        elif isinstance(res_info,PictureInfo):
            send_wx_text_reply(wxapi,reply_to_msg,f'为您找到{len(res_info.res_url_list)}张图片:')
        else:
            send_wx_text_reply(wxapi,reply_to_msg, '已为您找到对应资源:')
        send_wx_text_reply(wxapi,reply_to_msg,res_id)
        send_wx_text_reply(wxapi,reply_to_msg, f'请复制上面的提取码，点击下面的链接打开小程序后即可下载:{app_url}')

def is_res_task(msg):
    msg_type = msg["msg_type"]
    if msg_type in [49, 492,494]:
        return True
    if msg_type==1:
        content = msg.get('content')
        match = re.search(URL_PATTERN, content)
        if match is not None:
            return True
    return False

def send_wx_text_reply(wxapi,from_msg,message):
    is_chat_room = from_msg.get('is_chatroom')
    reply_session = from_msg.get('wx_id')
    reply_to = from_msg.get('sender')
    if is_chat_room:
        wxapi.send_text_and_at_member(to_chat_room=reply_session, to_wx_list=[reply_to], msg=message)
    else:
        wxapi.send_text(to_wx=reply_to, msg=message)

def forword_fetch(wxapi,msg):
    msg_type = msg["msg_type"]
    if msg_type==494:
        # 第三方返回回来的结果消息
        content= msg.get('content')
        root = etree.fromstring(content)
        titlenode = root.find(".//appmsg/title")
        title=titlenode.text if titlenode is not None  else None
        pagepathnode=root.find(".//appmsg/weappinfo/pagepath")
        pagepath=pagepathnode.text if pagepathnode is not None  else None
        if not pagepath:
            return
        a=len('pages/index/detail.html?p=')
        if a<0:
            log.warning(f'转发返回的资源地址格式异常：{pagepath}')
            return
        res_url=pagepath[a:]
        res_url=unquote_plus(res_url)
        log.info(f'找到转发返回的资源地址：{res_url}')
        # 微信小程序
        encfilekey=utils.get_url_query_value(res_url,"encfilekey")
        if forword_fetch_queue.empty():
            log.warning(f'不存在回调记录：{title} {encfilekey} {res_url}')
            return
        record=forword_fetch_queue.get_nowait()
        if not record:
            log.error(f'未找到回调记录：{title} {encfilekey} {res_url}')
            return
        encfilekey0=record['encfilekey']
        finder_des=record['finder_des']
        task_msg=record['task_msg']
        media_url=record['media_url']

        if not encfilekey0==encfilekey:
            log.error(f'encfilekey 比对不一致：{finder_des} encfilekey={encfilekey} VS {encfilekey0} {res_url} \r\n{utils.wx_msg_tostring(task_msg)}')
            return

        res_info = VideoInfo()
        res_info.res_type = 'video'
        video_url = res_url
        res_info.res_url = video_url
        size, type = get_file_info(video_url)
        res_info.res_size = size
        res_info.share_url = media_url
        res_info.name = finder_des

        log.info(f"forword-fetch:{finder_des} {title} {res_url}")
        setres_to_cache(res_info)
        return res_info,task_msg

def getres_from_cache(shared_url):
    id=utils.md5_str(shared_url)
    res_info=res_db.getResInfoFromRedis(id)
    log.info(f'GetRes_from_cache: {id} {type(res_info).__name__} hit={(not res_info is None)} {shared_url}')
    return res_info

def setres_to_cache(res_info):
    share_url=res_info.share_url
    id = utils.md5_str(share_url)
    res_info.id=id
    res_db.setResInfoToRedis(res_info)
    log.info(f'SetRes_to_cache: {id} {type(res_info).__name__} {share_url}')
    pass

def fetch(wxapi,msg):
    # print(f'fetch:{utils.wx_msg_tostring(msg)}')
    msg_type = msg["msg_type"]
    content = msg.get('content')
    msg_id=msg.get("msg_id")
    share_url,res_info = None,None

    if msg_type == 1:
        # 从文本中找链接
        match = re.search(URL_PATTERN, content)
        if match is not None:
            share_url = match.group(0)
        else:
            # raise Exception('您发过来的内容中没能找到有效的链接哈，请您确认下是否有发送了对应平台的内部分享链接而不是外部分享链接。目前可以支持外部分享链接及分享卡片，详细内容可以查看我的朋友圈。')
            log.info(f'未包含有效链接的内容: 发送人={msg.get("sender")} 内容={content}')
            return
    elif msg_type in [49, 492]:
        root = etree.fromstring(content)
        appid=root.find(".//appmsg").attrib['appid']
        titlenode = root.find(".//appmsg/title")
        title=titlenode.text if titlenode is not None else None
        desnode = root.find(".//appmsg/des")
        des=desnode.text if desnode is not None  else None
        share_urlnode = root.find(".//appmsg/url")
        share_url=share_urlnode.text if share_urlnode is not None  else None
        # print(title, des, share_url)
        # 如果是微信视频号，则转发
        if utils.is_empty_str(appid) and share_url and share_url.startswith('https://support.weixin.qq.com'):
            finder_desnode=root.find(".//finderFeed/desc")
            finder_des=finder_desnode.text if finder_desnode is not None else None
            media_urlnode=root.find(".//finderFeed/mediaList/media/url")
            media_url=media_urlnode.text if media_urlnode is not None else None
            share_url=media_url
            # 查缓存，看资源是否存在
            res_info=getres_from_cache(share_url)
            if res_info:
                return res_info
            # 如果缓存不存在，则转发
            log.info(f'转发微信视频号：{finder_des} {media_url}')
            # 登记转发记录，以回调时使用
            encfilekey=utils.get_url_query_value(media_url,"encfilekey")
            forword_fetch_queue.put({'encfilekey':encfilekey,'finder_des':finder_des,'media_url':media_url,'task_msg':msg})
            wxapi.forward_msg(to_wx=forword_third[0],msg_id=msg_id)
            return
    if share_url:
        # 查缓存，如果缓存不存在，去获取资源
        res_info = getres_from_cache(share_url)
        if res_info:
            return res_info
        res_info = fetch_by_shared_url(share_url)
        if res_info:
            setres_to_cache(res_info)
        return res_info

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
            if video_url.startswith('https://dwn.weilaizhihui.com/down?q='):
                video_url=utils.get_url_query_value(video_url,'q')
            res_info.res_url = video_url
            res_info.res_cover_url = rj0.get('cover')
            size, type = get_file_info(video_url)
            res_info.res_size = size
    if res_info:
        res_info.share_url = shared_url
        tit=rj0.get('tit')
        if tit or not tit=='平台提示当前链接已是无水印视频请勿重复提交':
            res_info.name = rj0.get('tit')

    return res_info

def get_file_info(path):
    size, type = 0, ''
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
            size = rj0.get('data').get('size')
            type = rj0.get('data').get('type')
    else:
        msg = f'未能获取到文件信息，status={status_code} 目标url={path}'
        log.error(msg)
    return size,type

