import json,logging
import os.path
import typing
import message_center
import webapp.webUtils
from sanic import response,request,Blueprint
from sanic.log import logger
from sanic_ext import cors


controller_bp=Blueprint('sniffer_web_controller')

@controller_bp.route("/res",methods =['GET'])
@cors(origin='*')
async def res(request: request.Request):
    id=request.args.get('id')
    logger.info(f"found res: id={id}")
    data=message_center.getResInfo4Api(id)
    return wrapper_json(data,None)

@controller_bp.route("/reslist",methods =['GET'])
@cors(origin='*')
async def reslist(request: request.Request):
    logger.info(f"list all res")
    data=message_center.listResInfoIds()
    return wrapper_json(data,None)

@controller_bp.route("/resproxy/<res:\w+_\d+\.\w+>",methods =['GET'])
# @controller_bp.route("/resproxy/((?<res>\w+_\d+)\.(mp4|jpg))",methods =['GET'])
@cors(origin='*')
async def resproxy(request: request.Request,res):
    logger.info(f'resproxy: {res}')
    res2,ext=os.path.splitext(res)
    arr=res2.split('_',2)
    id=arr[0]
    n=int(arr[1])
    return await webUtils.res_proxy(id,n)


# 包装API结果JSON
def wrapper_json(data,exception):
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

