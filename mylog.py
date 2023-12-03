# pip install colorlog
import logging
import colorlog
from logging import Logger

__logger:Logger=None
def get_logger(level=logging.INFO):
    global __logger
    if __logger  is not None:
        return __logger
    logger=logging.getLogger()
    logger.setLevel(level)
    console_handler=logging.StreamHandler()
    console_handler.setLevel(level)

    color_formatter=colorlog.ColoredFormatter(
        fmt='%(asctime)s [%(name)s] [%(process)d] [%(thread)d] %(levelname)s - (%(module)s.%(funcName)s) -> %(message)s',
        log_colors={
            'DEBUG':'cyan',
            'INFO':'white',
            'WARNING':'yellow',
            'ERROR':'red',
            'CRITICAL':'red,bg_white'
        }
    )
    console_handler.setFormatter(color_formatter)
    # 移除默认的handler
    for handler in logger.handlers:
        logger.removeHandler(handler)
        # 将控制台日志处理器添加到logger对象
    logger.addHandler(console_handler)
    __logger=logger
    return logger
