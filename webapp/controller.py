import json,logging
import typing
import message_center
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

