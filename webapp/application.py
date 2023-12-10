# coding:utf-8
# pip3 install sanic
# pip3 install sanic.ext
# pip3 install sanic-jinja2
# pip3 install sanic_cors

import logging
import os
import app_conf as conf
from sanic import Sanic
from sanic import request
from sanic.log import logger
from sanic_jinja2 import SanicJinja2 as sj,FileSystemLoader
from controller import controller_bp

app= Sanic('videoSniffer-web')
app.static(uri='/static', file_or_directory=f'{conf.current_file_dir}/static',directory_view=True)
app.static(name='favicon.ico',uri='/favicon.ico',file_or_directory=f'{conf.current_file_dir}/static/favicon.ico')
tp_loader = FileSystemLoader(conf.template_dir)
tp = sj(app,loader=tp_loader)
app.blueprint(controller_bp)


@app.main_process_start
async def main_process_start(app):
    logger.info("on main_process_start")


@app.main_process_ready
async def main_process_ready(app):
    logger.info("on main_process_ready")

@app.after_server_start
async def after_server_start(app):
    logger.info("on after_server_start")
    logger.info(f"current work dir is: {conf.current_work_dir}")
    logger.info(f'current file dir is: {conf.current_file_dir}')
    pass

@app.after_reload_trigger
async def after_reload_trigger(app):
    logger.info("on after_reload_trigger")
    pass

@app.on_request
async def on_request(request: request.Request):
    logger.info(f"on-request:{request.url}")


if __name__ == '__main__':
    # 启动web
    app.run(host="0.0.0.0", port=8082, debug=False, auto_reload=True, access_log=False)