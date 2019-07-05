import requests
import time
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
import configparser
import qrcode
import matplotlib.pyplot as plt
import pickle
import json
import traceback

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
}
url_uuid = 'https://passport.ustc.edu.cn/CodeServlet?service=https://jw.ustc.edu.cn/ucas-sso/login&cd='
url_qrcode1 = r'https://open.weixin.qq.com/connect/oauth2/authorize?' \
              r'appid=wx68a5870622ecbbcf&redirect_uri=https://ucas1.ustc.edu.cn/login&' \
              r'response_type=code&scope=SCOPE&agentid=44&state=fromWeiXinQR-uuidStart@'
url_qrcode2 = r'uuidEnd@https://jw.ustc.edu.cn/ucas-sso/login#wechat_redirect'
# url_login = 'https://passport.ustc.edu.cn/login?service=https%3A%2F%2Fjw.ustc.edu.cn%2Fucas-sso%2Flogin'
url_login1 = 'https://passport.ustc.edu.cn/LongConnectionCheckServlet?uuid='
url_login2 = '&service=https%3A%2F%2Fjw.ustc.edu.cn%2Fucas-sso%2Flogin&_='
url_check_ticket = 'https://jw.ustc.edu.cn/ucas-sso/login'
url_query = 'https://jw.ustc.edu.cn/for-std/grade/sheet/getGradeList?trainTypeId=1&semesterIds=81'
num = 0


def login_qrcode():
    global url_uuid
    session = requests.session()
    print('Trying to login...')
    url_uuid = url_uuid + str(int(time.time() * 1000))
    # print(url_uuid)
    response = session.get(url=url_uuid)
    content = response.content.decode('utf-8')
    uuid = content.split('&', maxsplit=2)[0]
    # print(uuid)
    url_qrcode = url_qrcode1 + uuid + url_qrcode2
    # print(url_qrcode)
    # qr = QRCode(url_qrcode)
    # show_cmd_qrcode(qr.text())
    qr_img = qrcode.make(data=url_qrcode)
    plt.imshow(qr_img)
    plt.axis('off')
    plt.show()
    url_login = url_login1 + uuid + url_login2 + str(int(time.time() * 1000))
    print(url_login)
    while True:
        response = session.get(url_login)
        content = response.content.decode('utf-8')
        content = eval(content)
        print(content)
        if 'isFollow' in content:
            print('>', end=' ')
        else:
            ticket = content['ticket']
            print(ticket)
            break
        time.sleep(3)
    session.get(url=url_check_ticket, data={'ticket': ticket})
    session_file = open('session.plk', 'wb')
    pickle.dump(session, session_file)
    session_file.close()
    return session


def show_cmd_qrcode(qr_text):
    white = '\u2588'
    black = '  '
    qr_text = qr_text.replace('0', white).replace('1', black)
    print(qr_text)


def query(session):
    global num
    times = 0
    while True:
        print("\nWaiting for 600 seconds...")
        if times > 0:
            time.sleep(600)
        times += 1
        print('The %d times in searching>>>' % times)
        response = session.get(url=url_query)
        content = response.content.decode('utf-8')
        try:
            data = json.loads(content)
        except Exception:
            raise
        courses = data['semesters'][0]['scores']
        message = ''
        for course in courses:
            message += '>%s %s %s\n' % (course['courseNameCh'], course['score'], course['gp'])
        print(message, end='')
        if len(courses) > num:
            num = len(courses)
            print("New grade released")
            send_mail(message)
        else:
            print('No new grade released')


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send_mail(message):
    from_addr = from_addr_mail
    password = password_mail
    to_addr = to_addr_mail
    smtp_server = 'smtp.sina.com'
    msg = MIMEText(message, 'plain', 'utf-8')
    msg['From'] = _format_addr('GradeScript <%s>' % from_addr)
    msg['To'] = _format_addr('Ens <%s>' % to_addr)
    msg['Subject'] = Header('New grade released', 'utf-8').encode()
    server = smtplib.SMTP(smtp_server, 25)
    server.login(from_addr, password)
    server.sendmail(from_addr, [to_addr], msg.as_string())
    server.quit()


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('./config.ini')
    from_addr_mail = config.get('info', 'from_addr_mail')
    password_mail = config.get('info', 'password_mail')
    to_addr_mail = config.get('info', 'to_addr_mail')
    try:
        session_file = open('session.plk', 'rb')
        session_o = pickle.load(session_file)
        session_file.close()
        print("Old Session>>>")
        query(session_o)
    except Exception as e:
        traceback.print_exc()
        session_o = login_qrcode()
        print('New Session>>>')
        query(session_o)
