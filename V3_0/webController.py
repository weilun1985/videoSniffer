import json,logging
import os.path
import typing
import res_db
import utils
from webUtils import res_proxy
from sanic import response,request,Blueprint
from sanic.log import logger
from sanic_ext import cors


controller_bp=Blueprint('sniffer_web_controller')

@controller_bp.route("/res",methods =['GET'])
@cors(origin='*')
async def res(request: request.Request):
    id=request.args.get('id')
    if utils.is_empty_str(id):
        errmsg = f'资源ID不能为空，请确认ID是否正确，或重新发起资源查找。'
        return wrapper_json(None,errmsg)
    logger.info(f"load res: id={id}")
    try:
        data=res_db.getResInfo4Api(id)
    except Exception as e:
        logger.error(e,exc_info=True)
        errmsg=f'抱歉，服务出现了异常，请稍后再试：{e}'
        return wrapper_json(None, errmsg)
    if data is None:
        errmsg=f'未找到ID为“{id}”的资源，请确认ID是否正确，或重新发起资源查找。'
        return wrapper_json(None, errmsg)
    return wrapper_json(data,None)

@controller_bp.route("/res_err",methods =['GET'])
@cors(origin='*')
async def res_err(request):
    id = request.args.get('id')
    err=request.args.get('err')
    logger.info(f"res report err: id={id} err={err}")
    from res_fetcher import re_fetch
    info=re_fetch(id)
    return wrapper_json(info, None)


@controller_bp.route("/res_clear",methods =['GET'])
@cors(origin='*')
async def res_clear(request: request.Request):
    id=request.args.get('id')
    if utils.is_empty_str(id):
        errmsg = f'资源ID不能为空，请确认ID是否正确。'
        return wrapper_json(None,errmsg)
    logger.info(f"clear res: id={id}")
    try:
        del_cnt=res_db.clearResInfo(id)
        if del_cnt==0:
            errmsg = f'未能清理ID为“{id}”的资源，请确认ID是否正确'
    except Exception as e:
        logger.error(e,exc_info=True)
        errmsg=f'抱歉，服务出现了异常，请稍后再试：{e}'
        return wrapper_json(None, errmsg)
    return wrapper_json(True,None)

@controller_bp.route("/reslist",methods =['GET'])
@cors(origin='*')
async def reslist(request: request.Request):
    logger.info(f"list all res")
    data=res_db.listResInfoIds()
    return wrapper_json(data,None)

@controller_bp.route("/resproxy/<res:\w+_\d+\.\w+>",methods =['GET'])
@cors(origin='*')
async def resproxy(request: request.Request,res):
    logger.info(f'resproxy: {res}')
    res2,ext=os.path.splitext(res)
    arr=res2.split('_',2)
    id=arr[0]
    n=int(arr[1])
    return await res_proxy(id,n)

@controller_bp.route("/report",methods =['POST'])
@cors(origin='*')
async def report(request: request.Request):
    if len(request.body) > 0:
        req_data = json.loads(request.body.decode("utf-8"))
        print(req_data)
    return wrapper_json('ok')

# 包装API结果JSON
def wrapper_json(data,exception=None):
    result = {"success": True, "data": None, "errmsg": None}
    if exception is not None:
        result["success"]=False
        result["errmsg"]=exception
    else:
        if hasattr(data,'__dict__'):
            result["data"]=data.__dict__
        else:
            result["data"]=data
    return response.json(body=result)

