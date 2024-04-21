# coding:utf-8
# pip3 install sanic
# pip3 install sanic.ext
# pip3 install sanic-jinja2
# pip3 install sanic_cors

import logging
import os
from web_app_config import web_template_dir,current_file_dir,current_work_dir,web_static_dir,web_favicon_path,web_wxscan_file
from sanic import Sanic
from sanic import request
from sanic.log import logger
from sanic_jinja2 import SanicJinja2 as sj,FileSystemLoader
from webController import controller_bp

app= Sanic('videoSniffer-web')
app.static(uri='/static', file_or_directory=web_static_dir,directory_view=True)
app.static(name='favicon.ico',uri='/favicon.ico',file_or_directory=web_favicon_path)
app.static(name='jplYnoJ9k8.txt',uri='/jplYnoJ9k8.txt',file_or_directory=web_wxscan_file)
tp_loader = FileSystemLoader(web_template_dir)
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
    logger.info(f"current work dir is: {current_work_dir}")
    logger.info(f'current file dir is: {current_file_dir}')
    logger.info(f'current web-view-template dir is: {web_template_dir}')
    logger.info(f'current static dir is: {web_static_dir}')
    pass

@app.after_reload_trigger
async def after_reload_trigger(app):
    logger.info("on after_reload_trigger")
    pass

@app.on_request
async def on_request(request: request.Request):
    logger.info(f"on-request:{request.url}")

def run():
    # 启动web
    app.run(host="0.0.0.0", port=8082, debug=False, auto_reload=True, access_log=False)


if __name__ == '__main__':
    run()