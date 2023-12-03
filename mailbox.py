import imaplib
import os.path
import smtplib
import email
import re
import logging
from datetime import datetime
from email.parser import BytesParser
from email.utils import parseaddr
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from models import MailInfo

log=logging.getLogger()

# __MAIL_ACCOUNT="409297393@qq.com"
# __MAIL_PWD="cxtemjxqfduobggc"

__MAIL_ACCOUNT="normi666@qq.com"
__MAIL_PWD='mbdgongyjlijcbhj'

_MAIL_IMAP_SERVER="imap.qq.com"
_MAIL_IMAP_PORT=993

_MAIL_SMTP_SERVER='smtp.qq.com'
_MAIL_SMTP_PORT=465




def select_mails():
    mails = []
    date_str=datetime.now().strftime('%m-%d-%Y')
    imap_server=imaplib.IMAP4_SSL(_MAIL_IMAP_SERVER,port=_MAIL_IMAP_PORT)
    try:
        imap_server.login(__MAIL_ACCOUNT,__MAIL_PWD)
        imap_server.select("INBOX")
        # query='ALL'
        # query='(FROM "normi666@qq.com")'
        # query='(FROM "xxxx@qq.com") UNSEEN SINCE "05-04-2023"'

        query=f'UNSEEN SINCE "{date_str}"'
        status, data = imap_server.search(None, query)
        email_ids = data[0].split()
        log.info("select-mail-count: %d",len(email_ids))

        for email_id in email_ids:
            try:
                mail_info=fetchmail(email_id,imap_server)
                mails.append(mail_info)
                imap_server.store(email_id, '+FLAGS', '\Seen')
            except Exception as e:
                log.error('fetch-email-error: %s',e)
    finally:
        imap_server.close()
        imap_server.logout()
    return mails

def decode(s):
    subject = email.header.decode_header(s)
    sub_bytes = subject[0][0]
    sub_charset = subject[0][1]
    if None == sub_charset:
        subject = sub_bytes
    elif 'unknown-8bit' == sub_charset:
        subject = str(sub_bytes, 'utf8')
    else:
        subject = str(sub_bytes, sub_charset)
    return subject

def decode_mime(msg):
    if msg.is_multipart():
        parts = msg.get_payload()
        for part in parts:
            decode_mime(part)
    else:
        str_content_type = msg.get_content_type()  # 当前数据块的Content-Type
        # print('str_content_type=%s'%str_content_type)
        str_charset = msg.get_content_charset(failobj=None)
        # print('str_charset=',str_charset)
        if str_content_type in ('text/plain', 'text/html'):
            bytes_content = msg.get_payload(decode=True)
            str_content = bytes_content.decode(str_charset)
            return str_content_type,str_content

def fetchmail(email_id,conn):
    status, content = conn.fetch(email_id, "(RFC822)")
    msg = BytesParser().parsebytes(content[0][1])
    mail_info=MailInfo()
    sub = msg.get('Subject')
    if sub is not None:
        mail_info.subject=decode(sub)
    from_info=msg.get('From')
    if from_info is not None:
        from_info=parseaddr(from_info)
        mail_info.from_mail=from_info[1]
        mail_info.from_name=decode(from_info[0])
    mail_date = msg.get("Date")
    if mail_date is not None:
        mail_date = re.search('\d+\s+\w{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}',mail_date).group(0)
        mail_info.mail_time=datetime.strptime(mail_date, '%d %b %Y %H:%M:%S')
        mail_info.mail_date = mail_info.mail_time.strftime('%Y-%m-%d-%H:%M:%S')
    # mail_info={
    #     'mail_id':email_id,
    #     'subject':sub,
    #     'from_name':from_name,
    #     'from_mail':from_mail,
    #     'mail_date':mail_date,
    #     'text_content':None,
    #     'html_content':None,
    #     'files':[]
    # }
    for part in msg.walk():
        content_type=part.get_content_type()
        content_charset=part.get_content_charset(failobj=None)
        file_name = part.get_filename()
        if content_type in ('text/plain', 'text/html'):
            bytes_content = part.get_payload(decode=True)
            str_content = bytes_content.decode(content_charset)
            if content_type=='text/plain':
                mail_info.text_content=str_content
            else:
                mail_info.html_content = str_content
        elif file_name is not None:
            file_name = decode(file_name)
            mail_info.files.append({'file_name': file_name,'type':content_type})
        else:
            if content_type not in ('multipart/mixed','multipart/alternative','multipart/alternative'):
                log.warning('un-parse-part: %s %s', content_type, content_charset)
    log.info('fetch-mail-ok: %s %s', mail_info.from_mail, mail_info.subject)
    return mail_info

def send_mail(to_addr,subject,text_content,html_content,files):
    # 消息对象
    msg = MIMEMultipart()
    # 邮件头
    msg['From'] = Header(__MAIL_ACCOUNT)
    msg['To'] = Header(to_addr)
    msg['Subject'] = Header(subject)
    # 正文
    if text_content is not None:
        msg_text_content = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(msg_text_content)
    if html_content is not None:
        msg_html_content = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(msg_html_content)
    # 附件
    for file in files:
        path = file['path']
        with open(path, 'rb') as f:
            bytes = f.read()
        file_name = file.get('name')
        if file_name is None:
            file_name = os.path.basename(path)
        annex = MIMEApplication(bytes)
        annex['Content-Type'] = 'application/octet-stream'
        annex.add_header('Content-Disposition', 'attachment', filename=file_name)
        msg.attach(annex)
    # 发送邮件
    smtp_conn=smtplib.SMTP_SSL(_MAIL_SMTP_SERVER,_MAIL_SMTP_PORT)
    try:
        smtp_conn.login(__MAIL_ACCOUNT,__MAIL_PWD)
        smtp_conn.sendmail(__MAIL_ACCOUNT,[to_addr],msg.as_string())
        log.info('send-mail-ok: %s %s',to_addr,subject)
        # print("------------------")
    except Exception as e:
        log.error(f'send-mail-fail:{to_addr} {subject} {e}')
        raise e
    finally:
        smtp_conn.quit()
        smtp_conn.close()


def reply_mail(org_mail,subject,text_content,html_content,files):
    to_addr=org_mail.from_mail
    if subject is None:
        subject='Re:'+org_mail.subject
    send_mail(to_addr,subject,text_content,html_content,files)

def list_mail(mail_info):
    print('mail_id:', mail_info.mail_id)
    print('subject:', mail_info.subject)
    print('from:', mail_info.from_name, mail_info.from_mail)
    print('date:', mail_info.mail_date)
    text_content = mail_info.text_content
    html_content = mail_info.html_content
    print('text_content_len:', 0 if text_content == None else len(text_content))
    if text_content is not None:
        print('\t', text_content)
    print('html_content_len:', 0 if html_content == None else len(html_content))
    files = mail_info.files
    if len(files) > 0:
        print('files:', len(files))
        for file in files:
            print('\t', file.get('type'), file.get('file_name'))


if __name__ == '__main__':
    mails=select_mails()
    mail=mails[0]
    files=[{'path':'videos/01e4d6556fa933380103730389e53f8559_258.mp4'}]
    reply_mail(mail,None,'已收到，感谢。',None,files)
