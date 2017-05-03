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
    result1 = re.sub(pattern1, '', str(html))
    pattern2 = re.compile(r'</a>')
    result2 = re.sub(pattern2, '', str(result1))
    return result2


# 获取URL
def get_href(text):
    pattern = re.compile(r'href="(.+?)"')
    url = pattern.findall(text)
    return url


# 去除网页中的无效图片
def del_hzh(text):
    pattern = re.compile(r'<div class="hzh_botleft">')
    result = re.sub(pattern, '<div class="hzh_botleft" style="display:none;">', str(text))
    return result


# 爬虫主函数
def spider():
    url = "http://www.39.net/"
    html = send_request(url)
    if not html:
        return False
    soup = BeautifulSoup(html, "lxml")
    select1 = soup.select("#homeheadlines .item ul")
    for s in select1:
        soup1 = BeautifulSoup(str(s), "lxml")
        select2 = soup1.select("li")
        for s1 in select2:
            soup2 = BeautifulSoup(str(s1), "lxml")
            select3 = soup2.select("a")
            if len(select3) < 3:
                continue
            tag = select3[0].get_text()
            print tag
            href1 = get_href(str(select3[1]))
            print href1
            href2 = get_href(str(select3[2]))
            article1 = get_article_content(href1[0])
            time.sleep(3)
            article2 = get_article_content(href2[0])
            sql = "INSERT INTO resource_article (title, img_url, content, modify_time, tag) VALUE (%s, %s, %s, %s, %s)"
            if article1:
                article1.append(tag)
                data1 = tuple(article1)
                insert_mysql(data1, sql)
            if article2:
                article2.append(tag)
                data2 = tuple(article2)
                insert_mysql(data2, sql)
            else:
                continue


def get_article_content(url):
    html1 = send_request(url)
    html = del_hzh(html1)
    if not html:
        return False
    soup = BeautifulSoup(html, "lxml")
    [s.extract() for s in soup('script')]
    [s.extract() for s in soup('center')]
    article_title_select = soup.select(".art_box h1")
    if article_title_select:
        # 文章标题
        article_title = article_title_select[0].get_text()
        # 爬取时间
        article_time = time.strftime("%Y-%m-%d", time.localtime())
        # 文章内容
        article_content_select = soup.select("#contentText")
        article_content = del_a(str(article_content_select[0]))
        # 文章图片链接（首张）
        article_image_select = soup.select("#contentText img")
        if article_image_select:
            pattern = re.compile(r'src="(.+?)"')
            img_url_list = pattern.findall(str(article_image_select[0]))
            img_url = img_url_list[0]
        else:
            img_url = ''
        # 结果列表
        article_list = [article_title, img_url, article_content, article_time]
    else:
        return False
    return article_list


spider()
