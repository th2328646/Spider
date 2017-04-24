# -*- coding: utf-8 -*-
# ---------------------------------------
#   程序：39健康网爬虫
#   版本：0.1
#   作者：th2328646
#   日期：2016-05-23
#   语言：Python 2.7
#   功能：爬取相关文章。
# ---------------------------------------


import urllib2
from urllib2 import HTTPError
import urllib
import re
import MySQLdb
import time
import os
from bs4 import BeautifulSoup
import sys

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)


# 数据插入函数
def insert_mysql(data, sql):
    # 连接数据库
    # conn = MySQLdb.connect(host='115.28.37.145', user='Test_User_0', passwd='J2K0B1a5oEnjoyor*', port=3306,
    #                        charset='utf8')
    conn = MySQLdb.connect(host='localhost', user='root', passwd='morpx', port=3306, charset='utf8')
    # 创建游标
    cur = conn.cursor()
    # 访问库
    conn.select_db('healthstation')
    # 执行数据插入语句
    cur.execute(sql, data)
    # 保存结果
    conn.commit()
    # 获取当前插入数据的id
    get_id = int(cur.lastrowid)
    # 关闭数据库连接
    cur.close()
    conn.close()
    # 返回文章的article_id
    return get_id


# 发送html请求
def send_request(url):
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    headers = {'User-Agent': user_agent}
    request_all = urllib2.Request(url, headers=headers)
    try:
        get_all = urllib2.urlopen(request_all)
        html = get_all.read()
        return html
    except HTTPError, e:
        print ('Error code', e.code)
        return False


# 编码转换函数(gbk->utf8)
def coding_change(data):
    to_unicode = data.decode('gbk')
    to_utf8 = to_unicode.encode('utf8')
    return to_utf8


# 去除html文本中的<a>标签
def del_a(html):
    pattern1 = re.compile(r'<a.*?>')
    result1 = re.sub(pattern1, '<p>', str(html))
    pattern2 = re.compile(r'</a>')
    result2 = re.sub(pattern2, '</p>', str(result1))
    return result2


# 生成新知所有page页的url，并调用get_xinzhi_url方法
def spider():
    # 页码总数
    page_num = 0
    # 爬取指定数量的页面
    i = 0
    page_url_list = []
    # 生成页码URL列表
    while i <= page_num:
        if i == 0:
            url = 'http://news.39.net/xinzhi/'
            page_url_list.append(url)
        else:
            url = 'http://news.39.net/xinzhi/'
            url = url + 'index_' + str(i) + ".html"
            page_url_list.append(url)
        i += 1
    # 生成新知URL列表
    for page in page_url_list:
        url_list = get_xinzhi_url(page)
        # 爬取新知详情页面中首页的数据
        for url in url_list:
            xinzhi_url = url[0]
            xinzhiimg_url = url[1]
            content_list = get_xinzhi_content(xinzhi_url)
            if not content_list:
                continue
            content_list[0] = xinzhiimg_url
            data = tuple(content_list)
            sql = "INSERT INTO xinzhi(summary_img, title, publish_time, content) VALUES(%s, %s, %s, %s)"
            insert_mysql(data, sql)
            time.sleep(3)


# 获取分页下的新知文章URL地址,并返回列表
def get_xinzhi_url(url):
    html = send_request(url)
    if not html:
        return False
    soup = BeautifulSoup(html, "lxml")
    xinzhi_select = soup.select(".center_left li strong a")
    pattern = re.compile(r'href="(.+?)"')
    xinzhi_url_list = pattern.findall(str(xinzhi_select))

    # 获取分页下的新知图片URL地址
    xinzhi_img_select = soup.select(".center_left li img")
    pattern = re.compile(r'src="(.+?)"')
    xinzhiimg_url_list = pattern.findall(str(xinzhi_img_select))

    url_list = []
    i = 0
    for xinzhi_url in xinzhi_url_list:
        url_tuple = (xinzhi_url_list[i], xinzhiimg_url_list[i])
        url_list.append(url_tuple)
        i += 1
    return url_list


def get_xinzhi_content(url):
    xinzhi_list = []
    html = send_request(url)
    if not html:
        return False
    soup = BeautifulSoup(html, "lxml")
    [s.extract() for s in soup('script')]
    [s.extract() for s in soup('center')]
    xinzhi_title_select = soup.select(".sweetening_title h1")
    if xinzhi_title_select:
        xinzhi_title = xinzhi_title_select[0].get_text()
        xinzhi_time_select = soup.select(".sweetening_title span")[1]
        xinzhi_time = xinzhi_time_select.get_text()
        xinzhi_content_select = soup.select("#contentText")
        result_xinzhi_content = del_a(str(xinzhi_content_select[0]))
        xinzhi_list = ['', xinzhi_title, xinzhi_time, result_xinzhi_content]
    else:
        xinzhi_title_select = soup.select(".main_con h2")
        if not xinzhi_title_select:
            return False
        xinzhi_title = xinzhi_title_select[0].get_text()
        xinzhi_time = ''
        xinzhi_content_select = soup.select(".main_con")
        result_xinzhi_content = ''
        for content_select in xinzhi_content_select:
            result_xinzhi_content += del_a(str(content_select))
        pattern = re.compile(r'<strong style="text-align:right">.*?</strong>')
        result_xinzhi_content = re.sub(pattern, '', result_xinzhi_content)
        xinzhi_list = ['', xinzhi_title, xinzhi_time, result_xinzhi_content]
    return xinzhi_list


spider()
