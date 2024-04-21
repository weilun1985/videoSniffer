from datetime import datetime

import utils

log=utils.get_logger()



USER_INFO='VideoSniffer:User:{}:Info'   # {'uid':id,'create_time':create_time,'last_active_time':latime,'msg_cnt':msg_cnt,'task_cnt':task_cnt}

def get_user_info(uid):
    user_info, is_new_user = None, False
    if not utils.is_empty_str(uid):
        key=USER_INFO.format(uid)
        redis = utils.get_redis()
        value = redis.get(key)
        now_time = datetime.now().strftime('%Y%m%d%H%M%S')

        if value is None:
            user_info={'uid':uid,'create_time':now_time,'last_active_time':now_time,'msg_cnt':0,'task_cnt':0}
            is_new_user=True
        else:
            user_info = utils.json_to_obj(value)
            user_info['last_active_time']=now_time
    return user_info,is_new_user

def update_user_info(user_info):
    uid=user_info['uid']
    key = USER_INFO.format(uid)
    redis = utils.get_redis()
    jstr = utils.obj_to_json(user_info)
    redis.set(key, jstr)
    log.info(f'update user info to redis: {user_info}')


def check_new_user(uid,handle):
    user_info,is_new_user=get_user_info(uid)
    if is_new_user:
        update_user_info(user_info)
        if handle:
            handle(user_info)
    return is_new_user

