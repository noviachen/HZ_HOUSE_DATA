# 获取 杭州市二手房交易监管服务平台 关于二手房的数据
# 网站地址：http://jjhygl.hzfc.gov.cn/webty/gpfy/gpfySelectlist.jsp
# 截取到的 API 地址：http://jjhygl.hzfc.gov.cn/webty/WebFyAction_getGpxxSelectList.jspx?page=
# API 里面能获取的信息不全，若通过 requests 获取房源详细信息又容易出问题，暂时那部分不全的数据先不管
# 房源详细页面为：http://jjhygl.hzfc.gov.cn/webty/WebFyAction_toGpxxInfo.jspx?gpfyid=
# 户型图地址：http://jjhygl.hzfc.gov.cn/memty/MemAction_selectFwytxxList.jspx?gpfyid=
# 数据表结构见 TableStructure.py

# 项目地址： https://github.com/noviachen/HZ_HOUSE_DATA
# 作者： uznEnehC
# 使用 Python 3 编译



import pymysql
import requests
import json
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


# 获取需要存储的挂牌房源信息，以在下一步中存储
def get_fydata():
    # 存储房源信息的列表
    data_list = []
    # 获取当前数据库房源的最新日期
    # 比如数据库里最大的日期是 2017-08-31 ，其实只要获取到 2017-8-30 这天的就可以完成了
    cur.execute('SELECT max(gp_date) FROM hz_esf_saling')
    max_date = cur.fetchone()[0]
    # 退出信号
    exit_code = ''
    for page in range(1, maxpage + 1):
        # 接收跳出循环信号
        if exit_code == 'EXIT_NOW':
            return data_list
        # 获取 JSON 数据
        json_url = origin_url + str(page)
        json_html = session.get(json_url, headers=headers, data=params).text
        json_data = json.loads(json_html)["list"]
        for data in json_data:
            # 发出退出循环信号
            if data['scgpshsj'] < str(max_date):
                exit_code = 'EXIT_NOW'
                break
            # 挂牌房源编号重复性校验
            cur.execute('SELECT * FROM hz_esf_saling WHERE gpID = ' + str(data['gpfyid']))
            if cur.rowcount > 0:
                continue
            fy_data = [
                data['gpfyid'],
                data['fczsh'],
                data['fwtybh'],
                data['xqmc'],
                data['cqmc'],
                data['jzmj'],
                data['wtcsjg'],
                data['scgpshsj'],
                data['mdmc'],
                data['gplxrxm'],
                haspic(data['gpfyid']),
            ]
            data_list.append(fy_data)
        time.sleep(30)
    return data_list


# 存储到数据库
def save2db(data_list):
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
    for data in data_list:
        cur.execute('INSERT INTO hz_esf_saling (' + col_join + ') VALUES (' + sstr_join + ')', (
            data[0],
            data[1],
            data[2],
            data[3],
            data[4],
            data[5],
            data[6],
            data[7],
            data[8],
            data[9],
            data[10]
        ))
        conn.commit()


# 推送到微信（SERVER酱）
def send2wx(text, desp):
    SCKEY = ''
    send_url = 'https://sc.ftqq.com/' + SCKEY + '.send?text=' + str(text) + '&desp=' + str(desp)
    session.get(send_url)


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

# 获取最大页数
page_html = session.get(origin_url, headers=headers, data=params).text
page_data = json.loads(page_html)
pageinfo = BeautifulSoup(page_data['pageinfo'], 'html.parser')
maxpage = pageinfo.find('font', {'class': 'color-blue09'}).get_text()
maxpage = int(maxpage)

# 连接数据库
conn = pymysql.connect(host='localhost', port=3306, user='root', password='123456', charset='utf8')
cur = conn.cursor()
cur.execute('USE scraping')

# 获取待存储的数据列表
data_list = get_fydata()

# 列表长度，用来计算数量
data_len = len(data_list)
if data_len == 0:
    # 没有新增的房源
    text = '房源信息抓取完成'
    desp = '没有新增的房源信息'
    send2wx(text, desp)
    cur.close()
    conn.close()
    exit()

# 存储数据
save2db(data_list)

# 微信通知
text = '房源信息抓取完成'
desp = '成功抓取到 ' + str(data_len) + ' 条房源信息'
send2wx(text, desp)

# 关闭数据库连接
cur.close()
conn.close()
