# -*-encoding: UTF-8-*-
# !/usr/bin/python3
import random
import time
import requests
import pymysql
import sqlite3
import re
import threading
from tkinter import *
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from lxml import etree

agent = [
    "Mozilla/5.0 (iPad; CPU OS 11_0) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"
]

obj_year = re.compile(r'◎年　　代　(?P<film_year>.*?)<br />', re.S)  # 年份
obj_region = re.compile(r'(◎产　　地　|◎国　　家　)(?P<film_region>.*?)<br />', re.S)  # 产地
obj_category = re.compile(r'◎类　　别　(?P<film_category>.*?)<br />', re.S)  # 类别
obj_subtitle = re.compile(r'◎字　　幕　(?P<film_subtitle>.*?)<br />', re.S)  # 字幕
obj_total_page = re.compile(r'共(?P<total_page>.*?)页', re.S)

lock = threading.Lock()
all_film_info = []

class Application(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master=master
        self.grid()
        self.createWidget()

    def createWidget(self):
        self.host_label = Label(self,text='Host').grid(row=0, column=0)
        self.database_label = Label(self, text='Database').grid(row=1, column=0)
        self.HOST = Entry(self, width=15)
        self.HOST.grid(row=0, column=1)
        self.DATABASE = Entry(self, width=15)
        self.DATABASE.grid(row=1, column=1)
        self.port_label = Label(self,text='Port').grid(row=0,column=2)
        self.PORT = Entry(self, width=4)
        self.PORT.grid(row=1,column=2)
        self.username_label = Label(self,text='Username').grid(row=0,column=3)
        self.password_label = Label(self,text='Password').grid(row=1,column=3)
        self.USERNAME = Entry(self, width=15)
        self.USERNAME.grid(row=0, column=4)
        self.PASSWORD = Entry(self, width=15, show='*')
        self.PASSWORD.grid(row=1, column=4)
        self.connect = Button(self, text='连接',command=self.connect)
        self.connect.grid(row=0, column=5)
        self.start = Button(self, text='开始', command=self.thread_start)
        self.start.grid(row=1, column=5)
        self.log_label = Label(self, text='Log').grid(row=2,column=2)
        self.LOG = Text(self, height=30, width=65,relief=SOLID,borderwidth=1)
        self.LOG.grid(row=3,column=0,columnspan=6)

    def connect(self):
        host = self.HOST.get().strip()
        database = self.DATABASE.get().strip()
        username = self.USERNAME.get().strip()
        password = self.PASSWORD.get().strip()
        port = int(self.PORT.get().strip())
        print(host, port, database, username, password)
        try:
            self.conn = pymysql.connect(host=host, port=port, database=database, user=username, password=password)
        except:
            messagebox.showerror(title='Error',message='连接失败')
        else:
            messagebox.showinfo(title='Success',message='连接成功')
            self.cursor = self.conn.cursor()
            # self.cursor.execute('DROP TABLE film_info;')
            # self.conn.commit()
            self.cursor.execute('''CREATE TABLE if not exists film_info
                    (`名称` text, 
                    `年份` int,
                    `地区` text,
                    `类型` text,
                    `字幕` text,
                    `下载链接` text)''')
            self.conn.commit()

    def thread_start(self):
        try:
            print(self.conn.thread_id)
        except:
            messagebox.showerror(title='Error',message='服务器未连接或连接失败')
        else:
            T = threading.Thread(target=self.main, daemon=True)
            T.start()
        pass

    def main(self):        # 每一页中获取电影的子域名
        start_time = time.time()
        tmp_resp = requests.get("https://www.dydytt.net/html/gndy/dyzz/list_23_1.html")
        tmp_resp.encoding = 'gb2312'
        print(tmp_resp.text)
        self.total_page = obj_total_page.search(tmp_resp.text).group('total_page')
        for i in range(1, int(self.total_page)+1):
            headers = {
                "User-Agent": random.choice(agent)
            }
            film_url_list = []
            print("进入第", str(i), "页")
            self.LOG.insert(END, chars=f'进入到第{str(i)}页\n')
            url = "https://www.dydytt.net/html/gndy/dyzz/list_23_" + str(i) + ".html"  # 一级页面
            resp = requests.get(url, headers=headers, verify=False)
            resp.encoding = 'gb2312'
            html = etree.HTML(resp.text)
            content = html.xpath('//table[@class="tbspan"]')  # 找到每个子页面入口
            resp.close()
            for each in content:
                film_url_list.append("https://www.dydytt.net" + each.xpath("./tr[2]/td[2]/b/a/@href")[0])
            with ThreadPoolExecutor(25) as t:
                for sec_url in film_url_list:
                    t.submit(self.get_details, sec_url=sec_url)
                    time.sleep(0.1)
            
            time.sleep(random.randint(1,2))

        self.LOG.insert(END, '信息获取完毕，正在插入数据库...\n')
        self.LOG.see(END)
        for each in all_film_info:
            try:
                self.cursor.execute(f'''INSERT INTO film_info values ('{each["name"]}','{each["year"]}','{each["region"]}','{each["category"]}','{each["subtitle"]}','{each["download_url"]}')''')
                self.conn.commit()
            except:
                continue
        end_time = time.time()
        self.LOG.insert(END, f'存储完毕。共获取{len(all_film_info)}条资源，耗时{str(end_time-start_time)[:5]}s\n')
        self.LOG.see(END)
        self.conn.close()
    

    def get_details(self, sec_url):
        headers = {
            "User-Agent": random.choice(agent)
        }
        dic = {}
        sec_resp = requests.get(sec_url, headers=headers, verify=False)
        sec_resp.encoding = 'gb2312'
        # 解析
        use_bs = BeautifulSoup(sec_resp.text, 'html.parser')
        sec_html = etree.HTML(sec_resp.text)
        name = sec_html.xpath('//div[@class="title_all"]/h1/font/text()')  # 找电影名
        dic['name'] = name[0]
        try:
            dic['year'] = obj_year.search(sec_resp.text).group('film_year')  # 找上映年份
        except AttributeError:
            dic['year'] = ""
        try:
            dic['region'] = obj_region.search(sec_resp.text).group('film_region')  # 找产地
        except AttributeError:
            dic['region'] = ""
        try:
            dic['category'] = obj_category.search(sec_resp.text).group('film_category')  # 类别
        except AttributeError:
            dic['category'] = ""
        try:
            dic['subtitle'] = obj_subtitle.search(sec_resp.text).group('film_subtitle')  # 字幕
        except AttributeError:
            dic['subtitle'] = ""
        try:
            dic['download_url'] = use_bs.find("span").find("a").get("href")  # 找磁力链
        except AttributeError:
            dic['download_url'] = use_bs.find("span").find("p").find("a").get("href")  # 找磁力链
        except:
            messagebox.showerror(title='Error', message='查找出错!运行继续(错误代码:001)')
        if dic['download_url'] is None or dic['download_url'][:4] == "http":
            try:
                pre_download = use_bs.find("td", style="WORD-WRAP: break-word").find("a")
                dic['download_url'] = pre_download.text
            except:
                messagebox.showerror(title='Error', message='查找出错!运行继续(错误代码:002)')

        print(dic["name"])
        self.LOG.insert(END,chars=dic['name']+'\n')
        self.LOG.see(END)
        try:
            lock.acquire()
            all_film_info.append(dic)
            lock.release()
        except:
            messagebox.showerror(title='Error', message='致命错误(错误代码:003)')


if __name__=="__main__":
    root = Tk()
    root.title('屠戮盗版天堂v3.0')
    root.geometry('520x488+450+100')
    Application(root)
    root.mainloop()
