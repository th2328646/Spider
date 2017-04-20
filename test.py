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
    get_all = urllib2.urlopen(request_all)
    html = get_all.read()
    return html


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


# 生成疾病所有page页的url，并调用get_jbk_url方法
def spider():
    # 页码总数
    page_num = 2
    # 爬取指定数量的页面
    i = 1
    page_url_list = []
    url_list = []
    # 生成页码URL列表
    while i < page_num:
        url = 'http://jbk.39.net/'
        url = url + 'bw_p' + str(i) + "/"
        page_url_list.append(url)
        i += 1
    # 生产疾病URL列表
    for page in page_url_list:
        jbk_url_list = get_jbk_url(page)
        url_list.extend(jbk_url_list)
    # # 爬取疾病详情页面中首页的数据
    # for jb_url in url_list[0:1]:
    #     get_jbk_content(jb_url + "/")
    # 爬取疾病详情页面中首页的数据
    for jb_url in url_list[0:1]:
        get_jbk_knowledge(jb_url + "/")


# 获取分页下的疾病URL地址,并返回列表
def get_jbk_url(url):
    html = send_request(url)
    h3 = re.findall(r"<h3.*?>.*?</h3>", html)
    url_list = []
    for u in h3:
        pattern = re.compile('href=\"(.+?)\"')
        url = re.findall(pattern, u)
        if len(url) > 0:
            if url[0] != "http://ypk.39.net/":
                url_list.append(url[0])
    return url_list


# 获取疾病详情页面下的疾病首页数据,并插入数据库
def get_jbk_content(url):
    html = send_request(url)
    soup = BeautifulSoup(html, "lxml")

    # 获取文章标题 article_title
    jb_name = soup.h1.string

    # 获取疾病首页信息
    jbk_info = soup.find_all(class_='info')
    info_soup = BeautifulSoup(str(jbk_info[0]), "lxml")
    info_select = info_soup.select('li')
    k = 0
    v = 0
    lable_list = []
    content_list = []
    info_dict = {
        '别名': '',
        '是否属于医保': '',
        '发病部位': '',
        '挂号的科室': '',
        '传染性': '',
        '传播途径': '',
        '治疗方法': '',
        '治愈率': '',
        '治疗周期': '',
        '多发人群': '',
        '治疗费用': '',
        '典型症状': '',
        '临床检查': '',
        '并发症': '',
        '手术': ''
    }
    # 获取疾病信息表格中的label，并生成数组
    for lable in info_select:
        lable_soup = BeautifulSoup(str(lable), "lxml")
        lable = lable_soup.select("i")
        lable_list.append(lable[0].get_text())
        k += 1

    # 获取疾病信息表格中的内容，并生成数组
    for content in info_select:
        content_soup = BeautifulSoup(str(content), "lxml")
        content_soup.find('i').extract()
        content_del_lable = content_soup.select('li')
        # 去除结果中的"[详细]"和空格
        result = content_del_lable[0].get_text()
        result = result.replace("[详细]", "")
        result = result.strip()
        info_dict[lable_list[v]] = result
        # content_list.append(result)
        v += 1

    # 获取疾病首页用药信息
    drug_list = soup.select('.drug a[title]')
    rec_drug = ''
    for drug in drug_list:
        rec_drug = rec_drug + drug.get_text() + ' '


# 获取疾病详情页面下的疾病知识数据,并插入数据库
def get_jbk_knowledge(url):
    # 疾病知识页面左侧标签url后缀列表
    knowledge_url_list = ['jbzs', 'zztz', 'blby', 'yfhl', 'jcjb', 'jb', 'yyzl', 'hl', 'ysbj', 'bfbz']
    knowledge_url_dict = {
        '疾病简介': 'jbzs',
        '典型症状': 'zztz',
        '发病原因': 'blby',
        '预防': 'yfhl',
        '临床检查': 'jcjb',
        '鉴别': 'jb',
        '治疗方法': 'yyzl',
        '护理': 'hl',
        '饮食保健': 'ysbj',
        '并发症': 'bfbz',
    }

    # 获取疾病简介页面内容
    url_jbzs = url + "jbzs"
    html = send_request(url_jbzs)
    soup_jbzs = BeautifulSoup(html, "lxml")
    jb_summary = soup_jbzs.select('.intro')[0].get_text()

    # 获取典型症状页面内容
    url_zztz = url + "zztz"
    html = send_request(url_zztz)
    soup_zztz = BeautifulSoup(html, "lxml")
    jb_zztz_links = soup_zztz.select('.links')
    content_all_links = ''
    for links in jb_zztz_links:
        content_all_links += str(links)
    result_zztz_links = del_a(content_all_links)
    jb_zztz_artbox = soup_zztz.select('.art-box')
    content_all_artbox = ''
    for artbox in jb_zztz_artbox:
        content_all_artbox += str(artbox)
    result_zztz_artbox = del_a(content_all_artbox)
    result_zztz = result_zztz_links + result_zztz_artbox

    # 获取发病原因页面内容
    url_blby = url + "blby"
    html = send_request(url_blby)
    soup_blby = BeautifulSoup(html, "lxml")
    jb_blby_artbox = soup_blby.select('.art-box')
    content_all_artbox = ''
    for artbox in jb_blby_artbox:
        content_all_artbox += str(artbox)
    result_blby_artbox = del_a(content_all_artbox)
    result_blby = result_blby_artbox

    # 获取预防页面内容
    url_yfhl = url + "yfhl"
    html = send_request(url_yfhl)
    soup_yfhl = BeautifulSoup(html, "lxml")
    jb_yfhl_artbox = soup_yfhl.select('.art-box')
    content_all_artbox = ''
    for artbox in jb_yfhl_artbox:
        content_all_artbox += str(artbox)
    result_yfhl_artbox = del_a(content_all_artbox)
    result_yfhl = result_yfhl_artbox

    # 获取临床检查内容
    url_jcjb = url + "jcjb"
    html = send_request(url_jcjb)
    soup_jcjb = BeautifulSoup(html, "lxml")
    jb_jcjb_artbox = soup_jcjb.select('.art-box')
    content_all_artbox = ''
    for artbox in jb_jcjb_artbox:
        content_all_artbox += str(artbox)
    result_jcjb_artbox = del_a(content_all_artbox)
    jb_jcjb_checkbox = soup_jcjb.select('.checkbox')
    content_all_checkbox = ''
    for checkbox in jb_jcjb_checkbox:
        content_all_checkbox += str(checkbox)
    result_jcjb_checkbox = del_a(content_all_checkbox)
    result_jcjb = result_jcjb_checkbox + result_jcjb_artbox

    # 获取鉴别页面内容
    url_jb = url + "jb"
    html = send_request(url_jb)
    soup_jb = BeautifulSoup(html, "lxml")
    jb_jb_artbox = soup_jb.select('.art-box')
    content_all_artbox = ''
    for artbox in jb_jb_artbox:
        content_all_artbox += str(artbox)
    result_yfhl_artbox = del_a(content_all_artbox)
    result_jb = result_yfhl_artbox

    # 获取治疗方法内容
    url_yyzl = url + "yyzl"
    html = send_request(url_yyzl)
    soup_yyzl = BeautifulSoup(html, "lxml")
    jb_yyzl_artbox = soup_yyzl.select('.art-box')
    content_all_artbox = ''
    for artbox in jb_yyzl_artbox:
        content_all_artbox += str(artbox)
    result_yyzl_artbox = del_a(content_all_artbox)
    jb_yyzl_info = soup_yyzl.select('.info')
    content_all_info = ''
    for info in jb_yyzl_info:
        content_all_info += str(info)
    result_yyzl_info = del_a(content_all_info)
    result_yyzl = result_yyzl_info + result_yyzl_artbox

    # 获取并发症页面内容
    url_bfbz = url + "bfbz"
    html = send_request(url_bfbz)
    soup_bfbz = BeautifulSoup(html, "lxml")
    jb_bfbz_links = soup_bfbz.select('.links')
    content_all_links = ''
    for links in jb_bfbz_links:
        content_all_links += str(links)
    result_bfbz_links = del_a(content_all_links)
    jb_bfbz_artbox = soup_bfbz.select('.art-box')
    content_all_artbox = ''
    for artbox in jb_bfbz_artbox:
        content_all_artbox += str(artbox)
    result_bfbz_artbox = del_a(content_all_artbox)
    result_bfbz = result_bfbz_links + result_bfbz_artbox


# 获取饮食宜忌数据,并插入数据库
def get_food(url):
    usefood_text = ''
    unusefood_text = ''
    food_text = ''
    usefood_list = {
        'name': '',
        'reason': '',
        'suggest': '',
    }
    unusefood_list = {
        'name': '',
        'reason': '',
        'suggest': '',
    }

    # 获取饮食保健页面内容
    url_ysbj = url + "ysbj"
    html = send_request(url_ysbj)
    soup_ysbj = BeautifulSoup(html, "lxml")

spider()
