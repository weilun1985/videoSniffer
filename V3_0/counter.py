import utils
from datetime import datetime

KEY_COUNTER_Fetched='VideoSniffer:Counter:{}:Fetched'
KEY_COUNTER_NewUser='VideoSniffer:Counter:{}:NewUser'
KEY_COUNTER_ActiveUser='VideoSniffer:Counter:{}:ActiveUser'


def incr_fetchd():
    current_date_time = datetime.now()
    current_date_string = current_date_time.strftime("%Y%m%d")
    key = KEY_COUNTER_Fetched.format(current_date_string)
    redis = utils.get_redis()
    redis.incr(key)

def set_new_user(uid):
    current_date_time = datetime.now()
    current_date_string = current_date_time.strftime("%Y%m%d")
    key = KEY_COUNTER_NewUser.format(current_date_string)
    redis = utils.get_redis()
    redis.sadd(key,uid)

def set_active_user(uid):
    current_date_time = datetime.now()
    current_date_string = current_date_time.strftime("%Y%m%d")
    key = KEY_COUNTER_ActiveUser.format(current_date_string)
    redis = utils.get_redis()
    redis.sadd(key, uid)

