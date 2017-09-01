# 获取 杭州市二手房交易监管服务平台 关于二手房的数据
# 网站地址：http://jjhygl.hzfc.gov.cn/webty/gpfy/gpfySelectlist.jsp
# 截取到的 API 地址：http://jjhygl.hzfc.gov.cn/webty/WebFyAction_getGpxxSelectList.jspx?page=
# API 里面能获取的信息不全，若通过 requests 获取房源详细信息又容易出问题，暂时那部分不全的数据先不管
# 房源详细页面为：http://jjhygl.hzfc.gov.cn/webty/WebFyAction_toGpxxInfo.jspx?gpfyid=
# 户型图地址：http://jjhygl.hzfc.gov.cn/memty/MemAction_selectFwytxxList.jspx?gpfyid=
# 数据表结构见 TableStructure.py

import pymysql
import requests
import json
import datetime
import time
from bs4 import BeautifulSoup


# 判断是否有户型图
def haspic(gpid):
    pic_url = 'http://jjhygl.hzfc.gov.cn/memty/MemAction_selectFwytxxList.jspx?gpfyid=' + str(gpid)
    html = session.get(pic_url, headers=headers, data=params).text
    json_data = json.loads(html)['list']
    if len(json_data) > 0:
        has_pic = 1
    else:
        has_pic = 0
    return has_pic


# POST 信息
session = requests.session()
headers = {
    "Accept": "text/html, */*; q=0.01",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.8",
    "Connection": "keep-alive",
    "Content-Length": "95",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Host": "jjhygl.hzfc.gov.cn",
    "Origin": "http://jjhygl.hzfc.gov.cn",
    "Referer": "http://jjhygl.hzfc.gov.cn/webty/gpfy/gpfySelectlist.jsp",
    "User-Agent": "Baiduspider+(+http://www.baidu.com/search/spider.htm)",
    "X-Requested-With": "XMLHttpRequest"
}
params = {
    "gply": "",
    "wtcsjg": "",
    "jzmj": "",
    "ordertype": "1",
    "fwyt": "",
    "hxs": "",
    "havepic": "",
    "starttime": "",
    "endtime": "",
    "keywords": "",
    "page": "1",
    "xqid": "0"
}

# API 地址
origin_url = 'http://jjhygl.hzfc.gov.cn/webty/WebFyAction_getGpxxSelectList.jspx?page='

# 获取最大页数 max_page
page_html = session.get(origin_url, headers=headers, data=params).text
page_data = json.loads(page_html)
pageinfo = BeautifulSoup(page_data['pageinfo'], 'html.parser')
max_page = pageinfo.find('font', {'class': 'color-blue09'}).get_text()
max_page = int(max_page)

# 连接数据库
print('连接数据库中……')
conn = pymysql.connect(host='localhost', port=3306, user='root', password='123456')
cur = conn.cursor()
cur.execute('USE scraping')
print('数据库已连接.\n')

# INSERT INTO MYSQL 需要用到的信息
cols = [
    'gpID', 'fczID', 'fyID', 'block', 'district', 'area',
    'price', 'gp_date', 'org_name', 'person', 'has_pic'
]
sstr = [
    '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'
]
col_join = ','.join(cols)
sstr_join = ','.join(sstr)

# 获取当前数据库房源的最新日期
# 比如数据库里最大的日期是 2017-08-31 ，其实只要获取到 2017-8-30 这天的就可以完成了
# 后面没有必要进行下去了，都是已经采集过的
# 为了保险期间，可以多往前推一天时间，到 2017-8-29
cur.execute('SELECT max(gp_date) FROM hz_esf_saling')
max_data = cur.fetchone()[0]
# 退出信号
exit_code = ''

# 通过 API 获取 JSON 解析后存储到 MYSQL
print('获取房源信息中……')
# 存储错误的挂牌房源编号
error_gpid = []
for i in range(1, max_page + 1):
    # 处理跳出循环信号
    if exit_code == 'EXIT_NOW':
        break
    print('当前进度为：   ' + str(i) + '/' + str(max_page) + '   '
          + str('%.2f%%' % (i / max_page * 100)) + '   ' + str(datetime.datetime.now()))
    # 获取 JSON 数据
    json_url = origin_url + str(i)
    json_html = session.get(json_url, headers=headers, data=params).text
    json_data = json.loads(json_html)["list"]
    for data in json_data:
        # 发出退出循环信号
        if data['scgpshsj'] < str(max_data - datetime.timedelta(days=2)):
            exit_code = 'EXIT_NOW'
            break
        # 重复性校验
        cur.execute('SELECT * FROM hz_esf_saling WHERE gpID = %s', (data['gpfyid']))
        if cur.rowcount > 0:
            continue
        # 存储数据
        try:
            cur.execute('INSERT INTO hz_esf_saling (' + col_join + ') VALUES (' + sstr_join + ')', (
                data['gpfyid'],
                data['fczsh'].encode('utf8'),
                data['fwtybh'],
                data['xqmc'].encode('utf8'),
                data['cqmc'].encode('utf8'),
                data['jzmj'],
                data['wtcsjg'],
                data['scgpshsj'],
                data['mdmc'].encode('utf8'),
                data['gplxrxm'].encode('utf8'),
                haspic(data['gpfyid'])
            ))
            conn.commit()
        except:
            error_gpid.append(data['gpfyid'])
    time.sleep(10)

print('所有房源信息已抓取完成.\n')
print('错误的挂牌房源编号有： ' + ', '.join(error_gpid))

# 关闭数据库连接
cur.close()
conn.close()
