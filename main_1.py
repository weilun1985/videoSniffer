# pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyOfficeRobot -U
# pip install playwright -U
# playwright install

import time,re,os
import mailbox
import asyncio
import logging
import multiprocessing
import thief_router
from thiefs.thiefBase import ThiefBase
from multiprocessing import Queue
from datetime import datetime


logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(name)s] [%(process)d] [%(thread)d] %(levelname)s - (%(funcName)s) -> %(message)s')
log=logging.getLogger()
def mail_daemon_run(mail_queue:Queue):
    log.info('mail_daemon_run: %s', datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))
    while True:
        try:
            mails=mailbox.select_mails()
            for mail_info in mails:
                mail_queue.put(mail_info)
            time.sleep(5)
        except Exception as e:
            log.error(e)
            time.sleep(5)

def worker_daemon_run(mail_queue:Queue):
    log.info('worker_daemon_run: %s', datetime.now().strftime('%Y-%m-%d-%H:%M:%S'))
    while True:
        mail_info=mail_queue.get()
        shared_text = mail_info.text_content
        if shared_text is None:
            continue
        try:
            thief=thief_router.do_route(shared_text)
            if thief is None:
                continue
            # 启动多进程
            thief_go(thief,mail_info)
        except Exception as e:
            log.error(e)


def thief_go(thief,mail_info):
    log.info(f'thief-go-run: from={mail_info.from_mail} date={mail_info.mail_date} thief={thief.name} target={thief.target_url}')
    info = thief.go()
    # 附件回信
    if info is None:
        return
    subject=f'Re:{info.name}'
    content=info.content
    files=[]
    m1=info.__dict__.get('res_file')
    m2=info.__dict__.get('res_file_list')
    t_size = 0
    if m1 is not None:
        file_size = os.stat(m1).st_size
        t_size+=file_size
        files.append({'path':m1,'size':file_size,'url':info.res_url})
    elif m2 is not None:
        for i in range(len(m2)):
            itm=m2[i]
            res_url=info.res_url_list[i]
            file_size = os.stat(itm).st_size
            t_size+=file_size
            files.append({'path':itm,'size':file_size,'url':res_url})
    content+=f'\r\n找到{len(files)}个文件，共计{round(t_size/1024/1024,2)}MB。'
    if len(files)>0:
        for i in range(len(files)):
            content += f"\r\n{i+1}. {files[i]['url']}"
        if t_size > 50*1024*1024: # 50MB附件
            content +=f'\r\n附件过大无法发送，请拷贝上面的URL在浏览器中打开自行下载'
            mailbox.reply_mail(mail_info, subject, content, None, None)
        else:
            content += f'\r\n相关资源在附件中，请查收'
            mailbox.reply_mail(mail_info,subject,content,None,files)


def run():
    print('start...')
    mail_queue=Queue()
    process=multiprocessing.Process(target=mail_daemon_run,args=[mail_queue])
    process.start()
    worker_daemon_run(mail_queue)
    print('compleated!')


def test_mail_thief(shared_text):
    thief = thief_router.do_route(shared_text)
    info=thief.go()
    print(info.name)
    m1 = info.__dict__.get('res_file')
    m2 = info.__dict__.get('res_file_list')




if __name__ == '__main__':
    run()
    # test_mail_thief('6 空天影视发布了一篇小红书笔记，快来看吧！ 😆 PlmuUl44jJMSkkb 😆 http://xhslink.com/0mVXRw，复制本条信息，打开【小红书】App查看精彩内容！')
    pass