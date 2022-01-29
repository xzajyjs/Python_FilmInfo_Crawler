# Python爬虫 多线程爬取盗版天堂6000部电影

- [x] 命令行  
- [x] GUI

---

## 使用方式

### 1.[**命令行模式**](film_catch(v2.0).py)

>  首先安装包依赖：  
>  ```pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple```

---

#### mysql存储

需配置mysql环境。  
使用方式`-h`查看帮助
```
usage: film_catch_v2.3.py [-h] -l HOST -u USER [-p PASSWORD] -d DATABASE
                          [-c CLEAR]

盗版天堂电影资源爬取机v2.3 --xzajyjs

optional arguments:
  -h, --help            show this help message and exit
  -l HOST, --host HOST  数据库host
  -u USER, --user USER  数据库用户名
  -p PASSWORD, --password PASSWORD
                        数据库连接密码
  -d DATABASE, --database DATABASE
                        数据库名
  -c CLEAR, --clear CLEAR
                        清空当前数据表,默认为False
```
**运行前需手动创建数据库**
```
$ mysql -uroot -p -h [localhost]
>>>
mysql> CREATE DATABASE xxxxx;
```

默认每次不会清空数据表内容。如需要则需要加上参数`-c True`

---

### **Notice**:

- 运行过程中会有warning，不要慌，是关闭了https验证的缘故。
- 虽然是多线程，但为了防止被封ip全过程跑完大概仍需要接近20分钟
- 盗版天堂的资源会经常更新，可设置crontab定时器每个月爬一次


---

### 2.[**GUI模式**](film_catch_GUI(v3.0).py)

- 暂时只支持Mysql数据库
- 较v2.0修改了多线程逻辑
- 注意：如果使用MySQL则`Database`必须预先手动创建，否则会报错


![](pic/show3.png)

![](pic/show.png)

![](pic/show2.png)

