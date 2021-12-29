import requests
import pymysql
import sqlite3
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
                (name text, download text)''')
conn.commit()

film_url_list = []  # 存储二级子页面url
for i in range(1, 241):
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
            download = use_bs.find("span").find("a").get("href")    # 找磁力链
        except AttributeError:
            download = use_bs.find("span").find("p").find("a").get("href")  # 找磁力链
        except:
            continue
        if download is None or download[:4] == "http":
            try:
                pre_download = use_bs.find("td", style="WORD-WRAP: break-word").find("a")
                download = pre_download.text
            except:
                continue

        for tmp in name:
            print(tmp, "->的下载链接：", download)
            cursor.execute("INSERT INTO film_info values ('%s', '%s')" % (tmp, download))
            conn.commit()

        sleep(randint(1, 2))
    resp.close()
    film_url_list = []

conn.close()
