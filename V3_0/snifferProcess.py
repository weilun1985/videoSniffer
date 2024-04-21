import re,os,time
import utils
import wechatUtils
import res_fetcher


log=utils.get_logger()

def start():
    print('资源嗅探程序启动...')
    lwxid,wxid=None,None
    while True:
        try:
            # wxid='wxid_4qg4sxvncs1c22' # 测试微信
            # wxid='wxid_bai8c34ycldr12' # 正式微信
            wxid=utils.get_config_item('wechat','wxid')
            if not wxid:
                log.error(f'未设置监听微信！')
                time.sleep(1)
                continue
            if not lwxid == wxid:
                log.info(f'开始监听微信通道：{wxid}')
                lwxid=wxid
            msg=wechatUtils.msg_recv_outqueue(wxid)
            if msg:
                res_fetcher.on_msg(msg)
            else:
                time.sleep(0.1)
        except Exception as e:
            log.error(e,exc_info=True)
            time.sleep(0.2)
    input('资源嗅探程序停止，请输入任意键结束。。。')
    pass

if __name__ == '__main__':
    try:
        start()
    except KeyboardInterrupt:
        os._exit(1)