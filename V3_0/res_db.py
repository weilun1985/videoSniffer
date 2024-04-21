import models
import utils

log=utils.get_logger()
def getResInfoFromRedis(id):
    if id is None:
        raise Exception('检索-资源索引信息的ID不能为空！')
    key = utils.SET_RES_INFO.format(id)
    redis = utils.get_redis()
    value = redis.get(key)
    if value is None:
        return None
    obj0=utils.json_to_obj(value)
    info=obj0
    if obj0['res_type']=='video':
        info=models.VideoInfo()
        info.__dict__=obj0
    elif obj0['res_type']=='picture':
        info = models.PictureInfo()
        info.__dict__ = obj0
    return info

def setResInfoToRedis(info):
    id=info.id
    if id is None:
        raise Exception(f'保存-资源索引信息的ID不能为空！ info={info.__dict__}')
    key = utils.SET_RES_INFO.format(id)
    redis = utils.get_redis()
    jstr=utils.obj_to_json(info)
    # log.info(f'set resInfo to redis: id={id}')
    redis.set(key,jstr)

def addResToRegetQueue(res_id):
    pass

def getResInfo4Api(id):
    resInfo=getResInfoFromRedis(id)
    if resInfo is None:
        return
    apiInfo=models.ResInfoForApi.parse(resInfo)
    return apiInfo

def listResInfoIds():
    key_patten=utils.SET_RES_INFO.format('*')
    key_prex=utils.SET_RES_INFO.format('')
    redis = utils.get_redis()
    log.info(f'redis:{redis}')
    key_list=redis.keys(key_patten)
    list=[]
    for key in key_list:
        id=key[len(key_prex):]
        list.append(id)
    return list

def clearResInfo(id):
    key = utils.SET_RES_INFO.format(id)
    redis = utils.get_redis()
    del_cnt=redis.delete(key)
    return del_cnt