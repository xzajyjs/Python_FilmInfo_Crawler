# -*-encoding: UTF-8-*-
# !/usr/bin/python3
import random
import time
import requests
import pymysql
import sqlite3
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from lxml import etree

all_film_info = []

agent = [
    "Mozilla/5.0 (iPad; CPU OS 11_0) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11"
]

lock = threading.Lock()

conn = pymysql.connect(host='xxxxx',
                       user='xxxxx',
                       password='xxxxx',
                       database='xxxxx')
cursor = conn.cursor()
# cursor.execute('''DROP TABLE film_info;''')       # 每次清空数据表
# conn.commit()
cursor.execute('''CREATE TABLE if not exists film_info
                (`名称` text, 
                `年份` int,
                `地区` text,
                `类型` text,
                `字幕` text,
                `下载链接` text)''')
conn.commit()

obj_year = re.compile(r'◎年　　代　(?P<film_year>.*?)<br />', re.S)  # 年份
obj_region = re.compile(r'(◎产　　地　|◎国　　家　)(?P<film_region>.*?)<br />', re.S)  # 产地
obj_category = re.compile(r'◎类　　别　(?P<film_category>.*?)<br />', re.S)  # 类别
obj_subtitle = re.compile(r'◎字　　幕　(?P<film_subtitle>.*?)<br />', re.S)  # 字幕

def download(i):
    headers = {
        "User-Agent": random.choice(agent)
    }
    film_url_list = []
    print("进入第", str(i), "页")
    url = "https://www.dydytt.net/html/gndy/dyzz/list_23_" + str(i) + ".html"  # 一级页面
    resp = requests.get(url, headers=headers, verify=False)
    resp.encoding = 'gb2312'
    html = etree.HTML(resp.text)
    content = html.xpath('//table[@class="tbspan"]')  # 找到每个子页面入口
    resp.close()
    for each in content:
        film_url_list.append("https://www.dydytt.net" + each.xpath("./tr[2]/td[2]/b/a/@href")[0])

    for sec_url in film_url_list:
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
            continue
        if dic['download_url'] is None or dic['download_url'][:4] == "http":
            try:
                pre_download = use_bs.find("td", style="WORD-WRAP: break-word").find("a")
                dic['download_url'] = pre_download.text
            except:
                continue

        print(dic["name"])
        lock.acquire()
        try:
            all_film_info.append(dic)
        except:
            lock.release()
            continue
        lock.release()
        time.sleep(random.randint(2,4))

if __name__ == "__main__":
    start_time = time.time()
    with ThreadPoolExecutor(30) as t:
        for _ in range(1, 241):
            t.submit(download, i=_)
    print(f"Over! total_num is {len(all_film_info)},consume_time {str(time.time()-start_time)[:5]}s"
          f"\nNow it's inserting into database....wait.....")
    for each in all_film_info:
        try:
            cursor.execute(f'''INSERT INTO film_info values ('{each["name"]}','{each["year"]}','{each["region"]}','{each["category"]}','{each["subtitle"]}','{each["download_url"]}')''')
            conn.commit()
        except:
            continue
    print(f"All over! Total size is {len(all_film_info)}, total_time is {str(time.time()-start_time)[:5]}s")

conn.close()