import json,logging
from sanic import response,request,Blueprint
from sanic.log import logger
from sanic_ext import cors

controller_bp=Blueprint('sniffer_web_controller')

@controller_bp.route("/res",methods =['GET'])
@cors(origin='*')
async def res(request: request.Request):
    request.args.get('id')
    logger.info(f"load res: id={id}")
    data={}
    
    return wrapper_json(data,None)

@controller_bp.route("/reslist",methods =['GET'])
@cors(origin='*')
async def reslist(request: request.Request):
    logger.info(f"list all res")
    data={}

    return wrapper_json(data,None)

# 包装API结果JSON
def wrapper_json(data,exception):
    result = {"success": True, "data": None, "errmsg": None}
    if exception is not None:
        result["success"]=False
        result["errmsg"]=exception
    else:
        result["data"]=data
    return response.json(body=result)

