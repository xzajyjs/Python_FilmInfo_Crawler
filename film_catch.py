import requests
import pymysql
import sqlite3
import re
from random import randint
from bs4 import BeautifulSoup
from lxml import etree
from time import sleep

agent = {
    "User-Agent": "Mozilla/5.0 (iPad; CPU OS 11_0) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1"
}

conn = pymysql.connect(host='xxxxx',
                       user='xxxxx',
                       password='xxxxx',
                       database='xxxxx')
cursor = conn.cursor()
# cursor.execute('''DROP TABLE film_info;''')       # 每次清空数据表
# conn.commit()
cursor.execute('''CREATE TABLE if not exists film_info
                (`电影名` text, 
                `上映年份` int,
                `地区/产地` text,
                `类别` text,
                `字幕类型` text,
                `下载链接` text)''')
conn.commit()

film_url_list = []  # 存储二级子页面url
obj_year = re.compile(r'◎年　　代　(?P<film_year>.*?)<br />', re.S) # 年份
obj_region = re.compile(r'(◎产　　地　|◎国　　家　)(?P<film_region>.*?)<br />', re.S)   # 产地
obj_category = re.compile(r'◎类　　别　(?P<film_category>.*?)<br />', re.S) # 类别
obj_subtitle = re.compile(r'◎字　　幕　(?P<film_subtitle>.*?)<br />', re.S) # 字幕

for i in range(3, 241):
    print("进入第",str(i),"页")
    url = "https://www.dydytt.net/html/gndy/dyzz/list_23_"+str(i)+".html"    # 一级页面
    resp = requests.get(url, headers=agent, verify=False)
    resp.encoding = 'gb2312'
    html = etree.HTML(resp.text)
    content = html.xpath('//table[@class="tbspan"]')    # 找到每个子页面入口

    # print(content)
    for each in content:
        film_url_list.append("https://www.dydytt.net"+each.xpath("./tr[2]/td[2]/b/a/@href")[0])

    for sec_url in film_url_list:
        sec_resp = requests.get(sec_url, headers=agent, verify=False)
        sec_resp.encoding='gb2312'
        # 解析
        use_bs = BeautifulSoup(sec_resp.text, 'html.parser')
        sec_html = etree.HTML(sec_resp.text)
        name = sec_html.xpath('//div[@class="title_all"]/h1/font/text()')    # 找电影名
        try:
            year = obj_year.search(sec_resp.text).group('film_year')   # 找上映年份
        except AttributeError:
            year = ""
        try:
            region = obj_region.search(sec_resp.text).group('film_region')   # 找产地
        except AttributeError:
            region = ""
        try:
            category = obj_category.search(sec_resp.text).group('film_category') # 类别
        except AttributeError:
            category = ""
        try:
            subtitle = obj_subtitle.search(sec_resp.text).group('film_subtitle')   # 字幕
        except AttributeError:
            subtitle = ""

        try:
            download_url = use_bs.find("span").find("a").get("href")    # 找磁力链
        except AttributeError:
            download_url = use_bs.find("span").find("p").find("a").get("href")  # 找磁力链
        except:
            continue
        if download_url is None or download_url[:4] == "http":
            try:
                pre_download = use_bs.find("td", style="WORD-WRAP: break-word").find("a")
                download_url = pre_download.text
            except:
                continue

        for name_tmp in name:
            print(name_tmp)
            cursor.execute("INSERT INTO film_info values ('%s','%s','%s','%s','%s','%s')" 
                            % (name_tmp, year, region, category, subtitle, download_url))
            conn.commit()

        sleep(randint(1, 2))
    resp.close()
    film_url_list = []

conn.close()
