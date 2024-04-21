# coding:utf-8
import os
import logging
from sanic.log import logger


current_work_dir = os.getcwd()
current_file_dir = os.path.dirname(os.path.abspath(__file__))
web_template_dir=os.path.join(current_file_dir, "templates")
web_static_dir=os.path.join(current_file_dir,"static")
web_favicon_path=os.path.join(web_static_dir,"favicon.ico")
web_wxscan_file=os.path.join(web_static_dir,"jplYnoJ9k8.txt")