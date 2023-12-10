# coding:utf-8
import os
import logging
from sanic.log import logger


current_work_dir = os.getcwd()
current_file_dir = os.path.dirname(os.path.abspath(__file__))
template_dir=f'{current_file_dir}/templates'
