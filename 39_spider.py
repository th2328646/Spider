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
import re
import MySQLdb
import time


# 数据插入函数
def insert_mysql(data):
    # 连接数据库
    # conn = MySQLdb.connect(host='115.28.37.145', user='Test_User_0', passwd='J2K0B1a5oEnjoyor*', port=3306, charset='utf8')
    conn = MySQLdb.connect(host='localhost', user='root', passwd='123456', port=3306, charset='utf8')
    cur = conn.cursor()
    # 访问库
    conn.select_db('healthstation')
    # 执行数据插入语句
    cur.execute("insert into t_resources_article(title, content, modifytime, classify) values(%s, %s, %s, %s)", data)
    # 保存结果
    conn.commit()
    cur.close()
    conn.close()


# 将文章保存到本地txt文件
# def to_file(title, article):
#     file_name = 'F:\\Article\\'+title+'.txt'
#     f = open(file_name, 'a')
#     f.write(article)
#     f.close()


# 编码转换函数(gbk->utf8)
def coding_change(data):
    to_unicode = data.decode('gbk')
    to_utf8 = to_unicode.encode('utf8')
    return to_utf8


# 爬虫函数
def spider(in_url, in_href, classify):
    url = in_url
    request_all = urllib2.Request(url)
    get_all = urllib2.urlopen(request_all)
    html = get_all.read()
    href = in_href
    url_list = re.findall(href, html)
    url_seen = []
    for url_article in url_list:
        if url_article in url_seen:
            pass
        else:
            req = urllib2.Request(url_article)
            get = urllib2.urlopen(req)
            html_all = get.read()
            # 获取文章标题 article_title
            article_title = re.findall("<h1>(.+?)</h1>", html_all)
            # print article_title[0]

            # 获取文章核心提示 article_tips
            article_tips = re.findall('<p class="summary">(.*?)</p>', html_all)
            # print article_tips[0]

            # 获取文章正文内容 article_content
            html_content = re.findall('<div class="art_con" id="contentText">(.*?)</div>',
                                      html_all, re.S)
            # print html_content
            html_p = re.findall('<p>(.*?)</p>', html_content[0])
            # print html_p
            content_list = []
            for p in html_p[0:len(html_p)-1]:
                # content = re.sub('<span.*?>|</span>|<strong>|</strong>|<a.*?>', '', p) + '\n'
                content = re.sub('<.*?>|&nbsp;', '', p) + '\n'
                content_list.append(content)
            article_content = ''.join(content_list)
            # print(article_content)
            # to_file(article_title[0], article_content)

            # 获取文章图片链接 article_img
            article_img = re.findall('<img src="(.*?)"', html_content[0])
            # print article_img

            # 获取文章爬取时间
            modifytime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            # 将爬取过的链接加入已查看链接列表
            url_seen.append(url_article)

            # 格式化数据
            if not article_content == '':
                data = (coding_change(article_title[0]), coding_change(article_content), modifytime, classify)
            # 插入数据库
                insert_mysql(data)


def execute_spider():
    # 初始化疾病和对应url的字典
    url_dic = {'fitness': ['http://fitness.39.net/', 'http://fitness\.39\.net/a/\d{6}/\d{7}\.html', '1'],
               'gxy': ['http://heart.39.net/gxy/', 'http://heart\.39\.net/a/\d{6}/\d{7}\.html', '2'],
               'gxz': ['http://heart.39.net/gxz/', 'http://heart\.39\.net/a/\d{6}/\d{7}\.html', '3'],
               'tnb': ['http://tnb.39.net/', 'http://tnb\.39\.net/snxty/\d{6}/\d{7}\.html', '4'],
               'js': ['http://sports.39.net/', 'http://sports\.39\.net/a/\d{6}/\d{7}\.html', '5'],
               'ys': ['http://care.39.net/ys/', 'http://care\.39\.net/a/\d{6}/\d{7}\.html', '6'],
               }
    for key in url_dic:
        spider(url_dic[key][0], url_dic[key][1], url_dic[key][2])


execute_spider()

