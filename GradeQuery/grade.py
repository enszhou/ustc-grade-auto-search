from bs4 import BeautifulSoup
import requests
import time
import _thread
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
}
url_login = 'https://passport.ustc.edu.cn/login?service=http%3A%2F%2Fmis.teach.ustc.edu.cn%2FcasLogin.do'
url_query = 'http://mis.teach.ustc.edu.cn/querycjxx.do'
num = 0


def login():
    session = requests.session()
    while True:
        print('Trying to login...')
        response = session.get(url=url_login)
        content = response.content
        html = content.decode('utf-8')
        html = BeautifulSoup(html, 'html.parser')
        token = html.find(type='hidden')['value']
        post_data = {
            '_token': token,
            'login': student_id,
            'password': password_jwc,
            'button': '登录'
        }
        response = session.post(url_login, post_data)
        head = response.headers
        if 'Set-Cookie' in head:
            if 'JSESSIONID=' in head['Set-Cookie']:
                print('Login successfully!')
                break
            else:
                print("Username or Password is wrong")
                break
    return session


def query(session):
    global num
    times = 0
    while True:
        print("\nWaiting for 5 seconds...\n")
        time.sleep(5)
        times += 1
        print('The %d times in searching>>>' % times)
        post_data = {
            'xuenian': '20181',
            'chaxun': '+%B2%E9++%D1%AF+',
            'px': 1,
            'zd': 0
        }
        response = session.post(url_query, post_data)
        content = response.content
        html = content.decode('GBK')
        html = BeautifulSoup(html, 'html.parser')
        table = html.find_all('table')[2]
        tr_arr = table.find_all('tr')
        grade_arr = tr_arr[0:-1]
        msg = ""
        for grade in grade_arr:
            td_arr = grade.find_all('td')
            msg = msg + ("%-5s %-5s %s\n" % (td_arr[4].text, td_arr[6].text, td_arr[2].text))
        if len(grade_arr) > num:
            num = len(grade_arr)
            _thread.start_new_thread(send_mail, (msg,))
        '''
        for grade in grade_arr:
            td_arr = grade.find_all('td')
            print("%-5s %-5s %s" % (td_arr[4].text, td_arr[6].text, td_arr[2].text))
        '''


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
    student_id = input("学号：")
    password_jwc = input("教务系统密码：")
    from_addr_mail = input("发件账号：")
    password_mail = input("发件密码：")
    to_addr_mail = input("收件账号：")
    while True:
        session_o = login()
        try:
            query(session_o)
        finally:
            print('Trying to reLogin...')
