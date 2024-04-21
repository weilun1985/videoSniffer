import time
import utils
from models import ResInfo,PictureInfo,VideoInfo
from lxml import etree



WX_MSG_TYPE_MAP = {1: '[文本]', 3: '[图片]', 43: '[视频]', 49: '[链接]', 34: '[语音]', 10000: '[系统消息]', 47: '[表情包]', 492: '[链接]', 494: '[小程序]', 493: '[文件]'}
KEY_QUEUE_WXMSG_RECV='VideoSniffer:WeChat:{}:recv_queue'
KEY_QUEUE_WXMSG_SEND='VideoSniffer:WeChat:{}:send_queue'



log=utils.get_logger()
def wx_msg_tostring(msg):
    if msg:
        msg_type_str=msg.get("msg_type_str")
        content=msg.get("content")
        ll=300
        if msg_type_str and len(content)>ll:
            content=content[0:ll]+'...'
        str=f'sender={msg.get("sender")} type={msg.get("type")} msg_type={msg.get("msg_type")}/{msg.get("msg_type_str")}  is_chat_room={msg.get("is_chatroom")} is_at_me={msg.get("at_me")} msg_id={msg.get("msg_id")}  is_self_msg={msg.get("is_self_msg")} wx_id={msg.get("wx_id")} self_wx_id={msg.get("self_wx_id")} \r\n{content}'
        return str

def wx_msg_tostring_full(msg):
    if msg:
        content=msg.get("content")
        str=f'sender={msg.get("sender")} type={msg.get("type")} msg_type={msg.get("msg_type")}/{msg.get("msg_type_str")}  is_chat_room={msg.get("is_chatroom")} is_at_me={msg.get("at_me")} msg_id={msg.get("msg_id")}  is_self_msg={msg.get("is_self_msg")} wx_id={msg.get("wx_id")} self_wx_id={msg.get("self_wx_id")} \r\n{content}'
        return str

def msg_recv_inqueue(msg):
    try:
        my_wx_id = msg['self_wx_id']
        key=KEY_QUEUE_WXMSG_RECV.format(my_wx_id)
        redis = utils.get_redis()
        jstr = utils.obj_to_json(msg)
        redis.lpush(key, jstr)
        log.info(f'wechat-recv-msg-inqueue [{my_wx_id}]-> {wx_msg_tostring(msg)}')
    except Exception as e:
        log.error(e,exc_info=True)


def msg_recv_outqueue(my_wx_id):
    try:
        key = KEY_QUEUE_WXMSG_RECV.format(my_wx_id)
        redis = utils.get_redis()

        temp = redis.rpop(key)
        if temp is None:
            return
        msg = utils.json_to_obj(temp)
        return msg
    except Exception as e:
        log.error(f'微信消息出栈异常[{my_wx_id}]：{e}', exc_info=True)

def msg_recv_outqueue_all():
    try:
        key_patten = KEY_QUEUE_WXMSG_RECV.format('wxid_bai8c34ycldr12')
        redis = utils.get_redis()
        key_list = redis.keys(key_patten)
        msg_list=[]
        for key in key_list:
            temp = redis.rpop(key)
            if temp is None:
                continue
            try:
                msg = utils.json_to_obj(temp)
                msg_list.append(msg)
            except Exception as e:
                log.error(f'微信消息出栈异常：[{key}] {e}', exc_info=True)
        return msg_list
    except Exception as e:
        log.error(f'微信消息出栈异常：{e}', exc_info=True)


def msg_send_inqueue(send_info):
    try:
        my_wx_id=send_info.get('sender')
        if utils.is_empty_str(my_wx_id):
            log.warning(f'send_info 未包含要使用的微信ID信息：{send_info}')
            return
        key = KEY_QUEUE_WXMSG_SEND.format(my_wx_id)
        redis = utils.get_redis()
        jstr= utils.obj_to_json(send_info)
        redis.lpush(key, jstr)
        log.info(f'wechat-send-msg-inqueue [{my_wx_id}]-> {jstr}')
    except Exception as e:
        log.error(e, exc_info=True)

def msg_send_outqueue(my_wx_id):
    try:
        key = KEY_QUEUE_WXMSG_SEND.format(my_wx_id)
        redis = utils.get_redis()
        temp = redis.rpop(key)
        if temp is None:
            return
        send_info = utils.json_to_obj(temp)
        return send_info
    except Exception as e:
        log.error(e, exc_info=True)

def get_wxapp_info(xml):
    root = etree.fromstring(xml)
    app_id = root.find(".//appmsg").attrib['appid']
    if utils.is_empty_str(app_id):
        app_id_1_node=root.find(".//appmsg/weappinfo/appid")
        app_id=app_id_1_node.text if app_id_1_node is not None else None
    app_name_node=root.find(".//appmsg/appinfo/appname")
    app_name=app_name_node.text if app_name_node is not None else None
    app_version_node=root.find(".//appmsg/appinfo/version")
    app_version = app_version_node.text if app_version_node is not None else None
    app_msg_type_node=root.find(".//appmsg/type")
    app_msg_type=app_msg_type_node.text if app_msg_type_node is not None else None

    titlenode = root.find(".//appmsg/title")
    title = titlenode.text if titlenode is not None else None
    desnode = root.find(".//appmsg/des")
    des = desnode.text if desnode is not None else None
    share_urlnode = root.find(".//appmsg/url")
    share_url = share_urlnode.text if share_urlnode is not None else None

    if utils.is_empty_str(app_id) and app_msg_type=='51':
        # 微信视频号
        finder_desnode = root.find(".//finderFeed/desc")
        title=None
        des = finder_desnode.text if finder_desnode is not None else None
        media_urlnode = root.find(".//finderFeed/mediaList/media/url")
        share_url = media_urlnode.text if media_urlnode is not None else None

    return {
        'app_id':app_id,
        'app_name':app_name,
        'app_version':app_version,
        'app_msg_type':app_msg_type,
        'title':title,
        'des':des,
        'url':share_url
    }


def get_wx_app_xml(title,res_id,from_wx_id):
    ts=int(time.time())
    xml=f'''
    <?xml version="1.0"?>
<msg>
	<appmsg appid="" sdkver="0">
		<title>{title}</title>
		<des />
		<username />
		<action>view</action>
		<type>33</type>
		<showtype>0</showtype>
		<content />
		<url>https://mp.weixin.qq.com/mp/waerrpage?appid=wx6986d528afafd77a&amp;type=upgrade&amp;upgradetype=3#wechat_redirect</url>
		<lowurl />
		<forwardflag>0</forwardflag>
		<dataurl />
		<lowdataurl />
		<contentattr>0</contentattr>
		<streamvideo>
			<streamvideourl />
			<streamvideototaltime>0</streamvideototaltime>
			<streamvideotitle />
			<streamvideowording />
			<streamvideoweburl />
			<streamvideothumburl />
			<streamvideoaduxinfo />
			<streamvideopublishid />
		</streamvideo>
		<canvasPageItem>
			<canvasPageXml><![CDATA[]]></canvasPageXml>
		</canvasPageItem>
		<appattach>
			<totallen>0</totallen>
			<attachid />
			<cdnattachurl />
			<emoticonmd5></emoticonmd5>
			<aeskey></aeskey>
			<fileext />
			<islargefilemsg>0</islargefilemsg>
		</appattach>
		<extinfo />
		<androidsource>3</androidsource>
		<sourceusername>gh_c8da7eae451a@app</sourceusername>
		<sourcedisplayname>无水印视频下载助手</sourcedisplayname>
		<commenturl />
		<thumburl />
		<mediatagname />
		<messageaction><![CDATA[]]></messageaction>
		<messageext><![CDATA[]]></messageext>
		<emoticongift>
			<packageflag>0</packageflag>
			<packageid />
		</emoticongift>
		<emoticonshared>
			<packageflag>0</packageflag>
			<packageid />
		</emoticonshared>
		<designershared>
			<designeruin>0</designeruin>
			<designername>null</designername>
			<designerrediretcturl><![CDATA[null]]></designerrediretcturl>
		</designershared>
		<emotionpageshared>
			<tid>0</tid>
			<title>null</title>
			<desc>null</desc>
			<iconUrl><![CDATA[null]]></iconUrl>
			<secondUrl />
			<pageType>0</pageType>
			<setKey>null</setKey>
		</emotionpageshared>
		<webviewshared>
			<shareUrlOriginal />
			<shareUrlOpen />
			<jsAppId />
			<publisherId>wxapp_wx6986d528afafd77apages/index/index.html?id={res_id}</publisherId>
			<publisherReqId />
		</webviewshared>
		<template_id />
		<md5 />
		<websearch />
		<weappinfo>
			<pagepath><![CDATA[pages/index/index.html?id={res_id}]]></pagepath>
			<username>gh_c8da7eae451a@app</username>
			<appid>wx6986d528afafd77a</appid>
			<version>4</version>
			<type>2</type>
			<weappiconurl><![CDATA[http://wx.qlogo.cn/mmhead/Q3auHgzwzM6SSiabXEMrHFvcEjW0HOpkWUAkcAicPFZw5LCRY0P4GlmA/96]]></weappiconurl>
          	<weapppagethumbrawurl><![CDATA[https://1e63211h01.yicp.fun/static/fetchok.png]]></weapppagethumbrawurl>
			<shareId><![CDATA[1_wx6986d528afafd77a_{res_id}_{ts}_0]]></shareId>
			<appservicetype>0</appservicetype>
			<secflagforsinglepagemode>0</secflagforsinglepagemode>
			<videopageinfo>
				<thumbwidth>717</thumbwidth>
				<thumbheight>574</thumbheight>
				<fromopensdk>0</fromopensdk>
			</videopageinfo>
		</weappinfo>
		<statextstr />
		<musicShareItem>
			<musicDuration>0</musicDuration>
		</musicShareItem>
		<finderLiveProductShare>
			<finderLiveID><![CDATA[]]></finderLiveID>
			<finderUsername><![CDATA[]]></finderUsername>
			<finderObjectID><![CDATA[]]></finderObjectID>
			<finderNonceID><![CDATA[]]></finderNonceID>
			<liveStatus><![CDATA[]]></liveStatus>
			<appId><![CDATA[]]></appId>
			<pagePath><![CDATA[]]></pagePath>
			<productId><![CDATA[]]></productId>
			<coverUrl><![CDATA[]]></coverUrl>
			<productTitle><![CDATA[]]></productTitle>
			<marketPrice><![CDATA[0]]></marketPrice>
			<sellingPrice><![CDATA[0]]></sellingPrice>
			<platformHeadImg><![CDATA[]]></platformHeadImg>
			<platformName><![CDATA[]]></platformName>
			<shopWindowId><![CDATA[]]></shopWindowId>
			<flashSalePrice><![CDATA[0]]></flashSalePrice>
			<flashSaleEndTime><![CDATA[0]]></flashSaleEndTime>
			<ecSource><![CDATA[]]></ecSource>
			<sellingPriceWording><![CDATA[]]></sellingPriceWording>
			<platformIconURL><![CDATA[]]></platformIconURL>
			<firstProductTagURL><![CDATA[]]></firstProductTagURL>
			<firstProductTagAspectRatioString><![CDATA[0.0]]></firstProductTagAspectRatioString>
			<secondProductTagURL><![CDATA[]]></secondProductTagURL>
			<secondProductTagAspectRatioString><![CDATA[0.0]]></secondProductTagAspectRatioString>
			<firstGuaranteeWording><![CDATA[]]></firstGuaranteeWording>
			<secondGuaranteeWording><![CDATA[]]></secondGuaranteeWording>
			<thirdGuaranteeWording><![CDATA[]]></thirdGuaranteeWording>
			<isPriceBeginShow>false</isPriceBeginShow>
			<lastGMsgID><![CDATA[]]></lastGMsgID>
			<promoterKey><![CDATA[]]></promoterKey>
			<discountWording><![CDATA[]]></discountWording>
			<priceSuffixDescription><![CDATA[]]></priceSuffixDescription>
			<showBoxItemStringList />
		</finderLiveProductShare>
		<finderOrder>
			<appID><![CDATA[]]></appID>
			<orderID><![CDATA[]]></orderID>
			<path><![CDATA[]]></path>
			<priceWording><![CDATA[]]></priceWording>
			<stateWording><![CDATA[]]></stateWording>
			<productImageURL><![CDATA[]]></productImageURL>
			<products><![CDATA[]]></products>
			<productsCount><![CDATA[0]]></productsCount>
		</finderOrder>
		<finderShopWindowShare>
			<finderUsername><![CDATA[]]></finderUsername>
			<avatar><![CDATA[]]></avatar>
			<nickname><![CDATA[]]></nickname>
			<commodityInStockCount><![CDATA[]]></commodityInStockCount>
			<appId><![CDATA[]]></appId>
			<path><![CDATA[]]></path>
			<appUsername><![CDATA[]]></appUsername>
			<query><![CDATA[]]></query>
			<liteAppId><![CDATA[]]></liteAppId>
			<liteAppPath><![CDATA[]]></liteAppPath>
			<liteAppQuery><![CDATA[]]></liteAppQuery>
			<platformTagURL><![CDATA[]]></platformTagURL>
			<saleWording><![CDATA[]]></saleWording>
			<lastGMsgID><![CDATA[]]></lastGMsgID>
			<profileTypeWording><![CDATA[]]></profileTypeWording>
			<reputationInfo>
				<hasReputationInfo>0</hasReputationInfo>
				<reputationScore>0</reputationScore>
				<reputationWording />
				<reputationTextColor />
				<reputationLevelWording />
				<reputationBackgroundColor />
			</reputationInfo>
			<productImageURLList />
		</finderShopWindowShare>
		<findernamecard>
			<username />
			<avatar><![CDATA[]]></avatar>
			<nickname />
			<auth_job />
			<auth_icon>0</auth_icon>
			<auth_icon_url />
			<ecSource><![CDATA[]]></ecSource>
			<lastGMsgID><![CDATA[]]></lastGMsgID>
		</findernamecard>
		<finderGuarantee>
			<scene><![CDATA[0]]></scene>
		</finderGuarantee>
		<directshare>0</directshare>
		<gamecenter>
			<namecard>
				<iconUrl />
				<name />
				<desc />
				<tail />
				<jumpUrl />
			</namecard>
		</gamecenter>
		<patMsg>
			<chatUser />
			<records>
				<recordNum>0</recordNum>
			</records>
		</patMsg>
		<secretmsg>
			<issecretmsg>0</issecretmsg>
		</secretmsg>
		<referfromscene>0</referfromscene>
		<gameshare>
			<liteappext>
				<liteappbizdata />
				<priority>0</priority>
			</liteappext>
			<appbrandext>
				<litegameinfo />
				<priority>-1</priority>
			</appbrandext>
			<gameshareid />
			<sharedata />
			<isvideo>0</isvideo>
			<duration>0</duration>
			<isexposed>0</isexposed>
			<readtext />
		</gameshare>
		<mpsharetrace>
			<hasfinderelement>0</hasfinderelement>
			<lastgmsgid />
		</mpsharetrace>
		<wxgamecard>
			<framesetname />
			<mbcarddata />
			<minpkgversion />
			<mbcardheight>0</mbcardheight>
			<isoldversion>0</isoldversion>
		</wxgamecard>
	</appmsg>
	<fromusername>{from_wx_id}</fromusername>
	<scene>0</scene>
	<appinfo>
		<version>1</version>
		<appname />
	</appinfo>
	<commenturl />
</msg>
    '''
    return xml

def send_wx_text_reply(from_msg,message):
    is_chat_room = from_msg.get('is_chatroom')
    reply_session = from_msg.get('wx_id')
    reply_to = from_msg.get('sender')
    if is_chat_room:
        # wxapi.send_text_and_at_member(to_chat_room=reply_session, to_wx_list=[reply_to], msg=message)
        msg_send_inqueue({
            'action':'send_text_and_at_member',
            'sender':from_msg.get('self_wx_id'),
            'options':{
                'to_chat_room':reply_session,
                'to_wx_list':[reply_to],
                'msg':  message
            }
        })
    else:
        # wxapi.send_text(to_wx=reply_to, msg=message)
        msg_send_inqueue({
            'action': 'send_text',
            'sender': from_msg.get('self_wx_id'),
            'options': {
                'to_wx': reply_to,
                'msg': message
            }
        })

def send_wx_resLink_reply(reply_to_msg,res_info):
    app_url = '#小程序://照片去水印小助手/ZzNbrUhZyxxCyut'
    res_id = res_info.id

    if isinstance(res_info, VideoInfo):
        title='为您找到1个视频:'
        send_wx_text_reply(reply_to_msg, title)
    elif isinstance(res_info, PictureInfo):
        title=f'为您找到{len(res_info.res_url_list)}张图片:'
        send_wx_text_reply(reply_to_msg, title)
    else:
        title='已为您找到对应资源:'
        send_wx_text_reply(reply_to_msg, title)
    send_wx_text_reply( reply_to_msg, res_id)
    send_wx_text_reply( reply_to_msg, f'请复制上面的提取码，点击下面的链接打开小程序后即可下载:{app_url}')
    res_name = res_info.name if hasattr(res_info, 'name') else title
    log.info(f'已回发资源小程序[链接]：资源ID={res_id} 资源名称={res_name} 接收人={reply_to_msg.get("sender")}')

def send_wx_resApp_reply(reply_to_msg,res_info):
    reply_session = reply_to_msg.get('wx_id')
    reply_to = reply_to_msg.get('sender')
    from_wxid=reply_to_msg.get('self_wx_id')
    if isinstance(res_info, VideoInfo):
        title = '为您找到1个视频:'
    elif isinstance(res_info, PictureInfo):
        title = f'为您找到{len(res_info.res_url_list)}张图片:'
    else:
        title = '已为您找到对应资源:'
    res_name=res_info.name if hasattr(res_info, 'name') else title
    res_id=res_info.id
    xml=get_wx_app_xml(res_name,res_id,from_wxid)
    # wxapi.send_xml(to_wx=reply_session,xml_str=xml)
    msg_send_inqueue({
        'action': 'send_xml',
        'sender': reply_to_msg.get('self_wx_id'),
        'options': {
            'to_wx': reply_session,
            'xml_str': xml
        }
    })

    log.info(f'已回发资源小程序[卡片]：资源ID={res_id} 资源名称={res_name} 接收人={reply_to_msg.get("sender")}')