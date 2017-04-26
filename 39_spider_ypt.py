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


# 获取分页下的URL地址,并返回列表
def get_page_url(url):
    html = send_request(url)
    if not html:
        return False
    soup = BeautifulSoup(html, "lxml")
    page_select = soup.select(".msgs strong a")
    pattern = re.compile(r'href="(.+?)"')
    page_url_list = pattern.findall(str(page_select))

    url_list = []
    i = 0
    for url in page_url_list:
        url_list.append(url)
        i += 1

    return url_list


# 生成药品通所有page页的url，并调用get_xinzhi_url方法
def get_url_list():
    # 获取药品通首页左侧分类中的URL
    html = send_request('http://ypk.39.net/')
    soup = BeautifulSoup(html, "lxml")
    suffix_list1 = soup.select(".ns_box dt a")
    url_list_zxy = []
    url_list_bjp = []
    for s in suffix_list1:
        # 去除疾病分类中的URL
        if 'search' in str(s):
            break
            # 获取疾病分类中的URL
            # pattern = re.compile(r'href="/search/(.+?)"')
            # href = pattern.findall(str(s))
            # suffix_url = href[0].encode('utf-8')
            # suffix_url = urllib2.quote(suffix_url)
            # url = 'http://ypk.39.net/search/%s' % suffix_url
            # url_list_category.append(url)
        # 获取中西药分类中的URL
        else:
            pattern = re.compile(r'href="(.+?)"')
            href = pattern.findall(str(s))
            url = 'http://ypk.39.net' + href[0]
            url_list_zxy.append(url)

    # 获取保健品分类中的URL
    suffix_list2 = soup.select(".ns")
    soup_bjp = BeautifulSoup(str(suffix_list2[1]), "lxml")
    bjp_select = soup_bjp.select("dd a")
    for a in bjp_select:
        pattern = re.compile(r'title="(.+?)"')
        title = pattern.findall(str(a))
        title_url = title[0].encode('utf-8')
        title_url = urllib2.quote(title_url)
        url = 'http://ypk.39.net/search/%s' % title_url
        url += "-c3"
        url_list_bjp.append(url)

    for url in url_list_zxy:
        spider_zxy(url)

    for url in url_list_bjp:
        spider_bjp(url)


def spider_zxy(url):
    # 页码总数
    html = send_request(url)
    soup = BeautifulSoup(html, "lxml")
    num_select = soup.select(".pgleft a")
    page_num = int(num_select[-3].get_text())
    # 爬取指定数量的页面
    i = 1
    page_url_list = []
    # 生成中西药页码URL列表
    while i <= page_num:
        url_page = url + "/p" + str(i) + "/"
        page_url_list.append(url_page)
        i += 1
    # 生成中西药药品URL列表
    x = 1
    for page in page_url_list:
        url_list = get_page_url(page)
        print page
        # 爬取保健品详情页面中的数据
        if url_list:
            for url in url_list:
                zxy_url = 'http://ypk.39.net' + url
                print x
                x += 1
                content_list = get_content(zxy_url)
                if not content_list:
                    continue
                data = tuple(content_list)
                sql = "INSERT INTO drug(drug_name, img_src, tag, specification) VALUES(%s, %s, %s, %s)"
                insert_mysql(data, sql)
                time.sleep(3)
        else:
            continue


def spider_bjp(url):
    # 页码总数
    html = send_request(url)
    soup = BeautifulSoup(html, "lxml")
    num_select = soup.select(".pgleft a")
    page_num = int(num_select[-3].get_text())
    # 爬取指定数量的页面
    i = 1
    page_url_list = []
    # 生成页码URL列表
    while i <= page_num:
        url_page = url + "-p" + str(i) + "/"
        page_url_list.append(url_page)
        i += 1
    # 生成保健品药品URL列表
    x = 1
    for page in page_url_list:
        url_list = get_page_url(page)
        # 爬取保健品详情页面中的数据
        if url_list:
            for url in url_list:
                bgp_url = 'http://ypk.39.net' + url
                print x
                x += 1
                content_list = get_content(bgp_url)
                if not content_list:
                    continue
                data = tuple(content_list)
                sql = "INSERT INTO drug(drug_name, img_src, tag, specification) VALUES(%s, %s, %s, %s)"
                insert_mysql(data, sql)
                time.sleep(3)
        else:
            continue


def get_content(url):
    html = send_request(url)
    if not html:
        return False
    # 判断是否为药品(非药品无详细说明书页)
    manual_url = url + 'manual'
    html_manual = send_request(manual_url)
    if not html_manual:
        return "Not drug"
    soup = BeautifulSoup(html, "lxml")
    # 获取药品名称
    name_select = soup.select(".t1 h1")
    if not name_select:
        return False
    result_name = name_select[0].get_text()
    # 获取药品缩略图URL
    img_select = soup.select(".imgbox img")
    if not img_select:
        result_img = ''
    else:
        pattern = re.compile(r'src="(.+?)"')
        result_img = re.findall(pattern, str(img_select))[0]

    # 获取绿色打勾标签
    tag_select = soup.select(".whatsthis li")
    result_tag = ''
    if not tag_select:
        result_tag = ''
    else:
        for tag in tag_select:
            result_tag += tag.get_text() + ","
        result_tag = result_tag[0:-1]

    # 获取详细说明书内容
    soup_manual = BeautifulSoup(html_manual, "lxml")
    content_select = soup_manual.select(".tab_box")
    if not content_select:
        result_content = ''
    else:
        result_content = del_a(str(content_select[0]))
        result_content = result_content.strip()

    result_list = [result_name, result_img, result_tag, result_content]
    return result_list


get_url_list()
