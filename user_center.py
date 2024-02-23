from datetime import datetime

import tools

log=tools.get_logger()



USER_INFO='VideoSniffer:User:{}:Info'   # {'uid':id,'create_time':create_time,'last_active_time':latime,'msg_cnt':msg_cnt,'task_cnt':task_cnt}

def get_user_info(uid):
    user_info, is_new_user = None, False
    if not tools.is_empty_str(uid):
        key=USER_INFO.format(uid)
        redis = tools.get_redis()
        value = redis.get(key)
        now_time = datetime.now().strftime('%Y%m%d%H%M%S')

        if value is None:
            user_info={'uid':uid,'create_time':now_time,'last_active_time':now_time,'msg_cnt':0,'task_cnt':0}
            is_new_user=True
        else:
            user_info = tools.json_to_obj(value)
            user_info['last_active_time']=now_time
    return user_info,is_new_user

def update_user_info(user_info):
    uid=user_info['uid']
    key = USER_INFO.format(uid)
    redis = tools.get_redis()
    jstr = tools.obj_to_json(user_info)
    redis.set(key, jstr)
    log.info(f'update user info to redis: {user_info}')


def check_user_auth(uid):
    msg,authed,user_info=None,False,None
    user_info,is_new_user=get_user_info(uid)
    if is_new_user:
        msg='Hi新朋友您好，我是您的自媒体素材小助手，目前我已经学会了帮助您下载各大主流媒体平台的无水印视频/图片素材，包括小红书/快手/抖音/视频号/百度/微博……可以关注我的朋友圈获得具体使用方法及后续其他相关信息，另外您在使用过程中碰到任何问题都可以直接微信留言给我哈。'
        update_user_info(user_info)

    authed=True
    return msg,authed,user_info

