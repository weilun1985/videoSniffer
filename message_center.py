import models
import tools
from models import MailInfo,WeChatMessageInfo,WeChatSendInfo,MailSendInfo,ChannelType,ThiefTaskInfo
from datetime import datetime


log=tools.get_logger()
def pushThiefTask(info:MailInfo|WeChatMessageInfo):
    task=ThiefTaskInfo()
    if isinstance(info,WeChatMessageInfo):
        task.ChannelType=ChannelType.WECHAT
        task.ChannelID=info.Me
        task.From=info.Sender
        task.Receiver=info.Me
        task.Time=info.MsgTime
        task.MessageBody=tools.obj_to_json(info)
    elif isinstance(info,MailInfo):
        task.ChannelType=ChannelType.MAILBOX
        task.ChannelID=info.Me
        task.From=info.from_mail
        task.Receiver=info.Me
        task.Time=info.mail_time
        task.MessageBody=tools.obj_to_json(info)
    else:
        log.warning(f'unknown message type:"{info}"!')
        return False
    # 推送进任务队列
    queue_name=tools.QUEUE_THIEF_TASK
    task_json=tools.obj_to_json(task)
    redis = tools.get_redis()
    status = redis.lpush(queue_name,task_json)
    # log.info(f'queue={queue_name} status={status} From={task.ChannelType} - {task.ChannelID} - {task.From} -{task.Time}')
    return status>0

def popThiefTask()->ThiefTaskInfo:
    queue_name = tools.QUEUE_THIEF_TASK
    redis = tools.get_redis()
    temp=redis.rpop(queue_name)
    if temp is None:
        return
    task=tools.json_to_obj(temp,ThiefTaskInfo)
    msg_body_str=task.MessageBody
    if task.ChannelType==ChannelType.WECHAT:
        msg_body=tools.json_to_obj(msg_body_str,WeChatMessageInfo)
        task.MessageBody=msg_body
    elif task.ChannelType==ChannelType.MAILBOX:
        msg_body=tools.json_to_obj(msg_body_str,MailInfo)
        task.MessageBody=msg_body
    return task

def pushSendTask(info:WeChatSendInfo|MailSendInfo):
    channel_type,channel_id=None,None
    if isinstance(info,WeChatSendInfo):
        queue_name=tools.QUEUE_SEND_TEMPL.format(f'{ChannelType.WECHAT}:{info.Me}')
    elif isinstance(info,MailSendInfo):
        queue_name=tools.QUEUE_SEND_TEMPL.format(ChannelType.MAILBOX)
    else:
        return False
    task_json=tools.obj_to_json(info)
    redis = tools.get_redis()
    status = redis.lpush(queue_name,task_json)
    # log.info(
    #     f'queue={queue_name} status={status} To={channel_type} - {info.Me} - {info.To} -{tools.simpleTimeStr(datetime.now())}')
    return status > 0

def popSendTask(channelType,channelID)->WeChatSendInfo:
    if channelType==ChannelType.WECHAT:
        queue_name=tools.QUEUE_SEND_TEMPL.format(f'{ChannelType.WECHAT}:{channelID}')
    elif channelType==ChannelType.MAILBOX:
        queue_name=tools.QUEUE_SEND_TEMPL.format(ChannelType.MAILBOX)
    else:
        log.warning(f'unknown channel type:"{channelType}"!')
        return
    redis = tools.get_redis()
    temp = redis.rpop(queue_name)
    if temp is None:
        return
    if channelType == ChannelType.WECHAT:
        task=tools.json_to_obj(temp,WeChatSendInfo)
    elif channelType ==ChannelType.MAILBOX:
        task=tools.json_to_obj(temp,MailSendInfo)
    return task

def wechatSend(me,to,content,files=None):
    msg = WeChatSendInfo()
    msg.To = to
    msg.Me = me
    msg.Content = content
    msg.Files=files
    pushSendTask(msg)

def getResInfoFromRedis(id):
    if id is None:
        raise Exception('检索-资源索引信息的ID不能为空！')
    key = tools.SET_RES_INFO.format(id)
    redis = tools.get_redis()
    value = redis.get(key)
    if value is None:
        return None
    obj0=tools.json_to_obj(value)
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
    key = tools.SET_RES_INFO.format(id)
    redis = tools.get_redis()
    jstr=tools.obj_to_json(info)
    log.info(f'set resInfo to redis: id={id}')
    redis.set(key,jstr)

def clearResInfo(id):
    key = tools.SET_RES_INFO.format(id)
    redis = tools.get_redis()
    del_cnt=redis.delete(key)
    return del_cnt

def getResInfo4Api(id):
    resInfo=getResInfoFromRedis(id)
    if resInfo is None:
        return
    apiInfo=models.ResInfoForApi.parse(resInfo)
    return apiInfo

def listResInfoIds():
    key_patten=tools.SET_RES_INFO.format('*')
    key_prex=tools.SET_RES_INFO.format('')
    redis = tools.get_redis()
    key_list=redis.keys(key_patten)
    list=[]
    for key in key_list:
        id=key[len(key_prex):]
        list.append(id)
    return list
