# 如果你是Python36。请删除37、38、39的pyd文件，其他版本同理
from WeChatPYAPI import WeChatPYApi

import time
import logging
from queue import Queue
import os
from datetime import datetime
from multiprocessing.dummy import Pool

import utils

# 当前目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.INFO)  # 日志器
msg_queue = Queue()  # 消息队列
pool = Pool(5)  # 线程池

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




def forward(w, msg):
    """转发消息【异步】"""

    # 阻塞等待某些资源下载完毕
    time.sleep(0.5)

    # 如果是图片、视频、文件，要先判断本地是否已经下载好了
    if msg["msg_type"] in [3, 43, 493]:

        # 如果是视频的话，把后缀替换成mp4就是真实路径
        file_path = msg["file_path"].replace(".jpg", ".mp4") if msg["msg_type"] == 43 else msg["file_path"]

        # 1、这里循环是防止某些资源文件过大，还未完全下载完毕
        # 2、严谨点应该控制好循环次数与间隔时间，真的还未下载完（考虑本地网络问题）就放弃该资源吧
        for i in range(5):
            time.sleep(1)
            if os.path.exists(r"{}".format(file_path)):
                break

        # 文件类型会在下载完成之后，更新MsgSvrID，所以要从数据库中查询最新的MsgSvrID
        if msg["msg_type"] == 493:
            db_num = 0
            while True:
                # 查询数据库
                ret = w.select_db(
                    "MSG{}.db".format(db_num),
                    "select MsgSvrID from MSG where StrTalker='{}' AND localId='{}' AND CreateTime='{}';".format(
                        msg["wx_id"],
                        msg["local_id"],
                        msg["time_stamp"]
                    )
                )
                if ret is None:
                    break
                if ret:
                    msg["msg_id"] = ret[0]["MsgSvrID"]
                    break
                db_num += 1

    # 转发消息
    w.forward_msg("filehelper", msg["msg_id"])


def on_message(msg):
    """消息回调，建议异步处理，防止阻塞"""
    # print(msg)
    print(utils.wx_msg_tostring(msg))
    msg_queue.put(msg)


def on_exit(event):
    """退出事件回调"""

    action = event["action"]
    wx_id = event["wx_id"]
    if action == 1:
        print("微信({})：进程结束，请重新启动微信".format(wx_id))
    elif action == 2:
        print("微信({})：已退出登录，请重新登录".format(wx_id))


def main():
    # 初次使用需要pip安装两个库：
    # pip install requests
    # pip install pycryptodomex

    # 查看帮助
    help(WeChatPYApi)

    # 实例化api对象【要多开的话就实例化多个《WeChatPYApi》对象】
    w = WeChatPYApi(msg_callback=on_message, exit_callback=on_exit, logger=logging)

    # 调试模式：
    # debug_pid=日志中输出的进程pid
    # 注意：你的微信必须使用start_wx方法登录成功后，才能使用调试模式
    # w = WeChatPYApi(msg_callback=on_message, exit_callback=on_exit, logger=logging, debug_pid=15396)

    # 启动微信【调试模式可不调用该方法】
    errno, errmsg = w.start_wx()
    # errno, errmsg = w.start_wx(path=os.path.join(BASE_DIR, "login_qrcode.png"))  # 保存登录二维码
    if errno != 0:
        print(errmsg)
        if errmsg != "当前为调试模式，不需要调用“start_wx”":
            return

    # 这里需要阻塞，等待获取个人信息
    while not w.get_self_info():
        time.sleep(2)

    my_info = w.get_self_info()
    print("登陆成功！")
    print(my_info)

    # 拉取列表（好友/群/公众号等）拉取可能会阻塞，可以自行做异步处理
    # 好友列表：pull_type = 1
    # 群列表：pull_type = 2
    # 公众号列表：pull_type = 3
    # 其他：pull_type = 4
    lists = w.pull_list(pull_type=3)
    print(lists)

    app_code= w.get_small_app_code(
        app_id="wx6986d528afafd77a"
    )
    print('app_code:',app_code)

    xml = get_wx_app_xml('好兄弟，一辈子', '23edf889fabb7772ccd96805626c5115',my_info.get('wx_id'))
    w.send_xml(to_wx='lichzh1985',xml_str=xml)
    print('发送小程序xml完成，请验证')

    # 获取朋友圈数据
    # moments = w.get_moments()
    # if not moments:
    #     print("没有最新的朋友圈")
    # else:
    #     for item in moments:
    #         print(item)

    # 获取群成员列表
    # lists = w.get_chat_room_members(to_chat_room="123@chatroom")
    # print(lists)

    # 发送文本消息
    # w.send_text(to_wx="filehelper", msg='作者QQ:\r437382693')
    # time.sleep(1)

    # 发送图片消息
    # w.send_img(to_wx="filehelper", path=r"C:\Users\Administrator\Desktop\1.png")
    # time.sleep(1)

    # 发送文件/视频
    # w.send_file(to_wx="filehelper", path=r"C:\Users\Administrator\Desktop\1.mp4")
    # time.sleep(1)

    # 发送好友名片
    # w.send_friend_card(
    #     to_wx="filehelper",
    #     friend_wx=my_info["wx_id"],
    #     friend_name="三水君"
    # )
    # time.sleep(1)

    # 发送卡片链接
    # w.send_card_link(
    #     to_wx="filehelper",
    #     title="QQ",
    #     desc="437382693",
    #     target_url="http://www.baidu.com",
    #     img_url="https://img.alicdn.com/bao/uploaded/TB1AptvRKH2gK0jSZJnXXaT1FXa.png_310x310.jpg"
    # )
    # time.sleep(1)

    # 处理消息回调【具体根据自己的业务来写，这里只是一个简陋的演示】
    while True:
        msg = msg_queue.get()

        # 正常消息
        if msg["type"] == 100:
            # 自己发送的消息
            if msg["is_self_msg"]:
                print("收到了自己发送的消息！")

            # 别人发送的消息
            else:
                if msg["msg_type"] == 37:
                    # 同意添加好友申请
                    w.agree_friend(msg_data=msg)

                # 处理图片消息
                elif msg["msg_type"] == 3:
                    file_path, file_name = os.path.split(msg["file_path"])
                    if file_name.endswith("dat"):
                        cur_time = datetime.now().strftime("%Y-%m-%d %H-%M-%S ")
                        file_name = cur_time + file_name.replace(".dat", "")
                        print(file_name)

                        # 这里睡2秒是防止某些图片过大，还未完全下载完毕
                        # time.sleep(2)

                        # 保存图片
                        # w.save_img(
                        #     save_path=os.path.join(BASE_DIR, "temp\\{}.png".format(file_name)),
                        #     msg_data=msg,
                        # )

                # 收款
                elif msg["msg_type"] == 490:
                    is_recv = msg["detail"]["is_recv"]
                    if is_recv:
                        # 收款
                        w.collection(msg_data=msg)

                # 如果是XXX发来的信息，转发消息【异步】
                if msg["wx_id"] == "wxid_xxx":
                    pool.apply_async(forward, (w, msg))

        # 撤回消息
        # 注意：撤回消息中的参数，跟正常消息的参数不一致，可自行判断type是否是666，分别放到不同的队列中处理
        elif msg["type"] == 666:
            print("{} 撤回消息：{}".format(msg["wx_id"], msg["content"]))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        os._exit(1)
