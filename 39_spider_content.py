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


# 数据插入函数
def insert_mysql(data, sql):
    # 连接数据库
    # conn = MySQLdb.connect(host='115.28.37.145', user='Test_User_0', passwd='J2K0B1a5oEnjoyor*', port=3306,
    #                        charset='utf8')
    conn = MySQLdb.connect(host='localhost', user='root', passwd='123456', port=3306, charset='utf8')
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


# 编码转换函数(gbk->utf8)
def coding_change(data):
    to_unicode = data.decode('gbk')
    to_utf8 = to_unicode.encode('utf8')
    return to_utf8


# 下载图片
def save_img(url, name):
    if url == '':
        return
    img = urllib.urlopen(url)
    data = img.read()
    img_dir = 'F:\\download' + time.strftime("%Y-%m-%d", time.localtime())
    filename = img_dir + '\\' + name
    if not os.path.isdir(img_dir):
        os.mkdir(img_dir)
    f = open(filename, 'wb')
    f.write(data)
    f.close()


#  返回默认图片
def default_img(a):
    img_name = ''
    if a == '1':
        img_name = 'jianfei@3x.png'
    elif a == '2':
        img_name = 'xueya@3x.png'
    elif a == '3':
        img_name = 'xuezhi@3x.png'
    elif a == '4':
        img_name = 'xuetang@3x.png'
    elif a == '5':
        img_name = 'jainshen@3x.png'
    elif a == '6':
        img_name = 'yangsheng@3x.png'
    return img_name


# 图片信息插入数据库
def insert_imginfo(get_id, name):
    img_path = 'files/res/app/start/' + name
    create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    article_id = get_id
    data = (img_path, article_id, create_time)
    sql = "insert into t_article_imgs(path, article_id, createtime) values(%s, %s, %s)"
    insert_mysql(data, sql)


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

            # 获取文章正文内容 article_content
            html_content = re.findall('<div class="art_con" id="contentText">(.*?)<div class="hzh_botleft">',
                                      html_all, re.S)

            # 获取文章爬取时间
            modifytime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            # 将爬取过的链接加入已查看链接列表
            url_seen.append(url_article)

            # 格式化数据
            if html_content:
                # 获取文章图片链接 url_img
                url_img = re.findall('<img src="(.*?)"', html_content[0])

                # 去除<a>标签
                pattern1 = re.compile(r'<a.*?>|</a>')
                filter1 = re.sub(pattern1, '', html_content[0])

                # 给<img>标签加上style="width:100%"
                pattern2 = re.compile('<img|<IMG')
                filter2 = re.sub(pattern2, r'<img style="width:100%"', filter1)
                # print filter2

                data = (coding_change(article_title[0]), coding_change(filter2), modifytime, classify)
                # 插入数据库
                sql = "insert into t_resources_article(title, content, pageViews, modifytime, classify) values" \
                      "(%s, %s, '0', %s, %s)"
                article_id = insert_mysql(data, sql)
                # 获取article_id,将抓取的图片绑定至对应文章下
                num = len(url_img)
                # 若文章中没有图片，则将对应的默认图片存储地址插入数据库中
                if num == 0:
                    insert_imginfo(article_id, default_img(classify))
                # 若文章中有且仅有1张图片
                elif num == 1:
                    url = url_img[0]
                    img_name = url.split('/')[-1]
                    # 该图片为广告图片，则将对应的默认图片存储地址插入数据库中
                    if img_name == 'org_628811.jpg':
                        insert_imginfo(article_id, default_img(classify))
                    else:
                        save_img(url, img_name)
                        insert_imginfo(article_id, img_name)
                elif num <= 3:
                    for url in url_img:
                        img_name = url.split('/')[-1]
                        if not img_name == 'org_628811.jpg':
                            save_img(url, img_name)
                            insert_imginfo(article_id, img_name)
                # 若文章中的图片大于3张，则仅保存前3张图片
                else:
                    for url in url_img[0:3]:
                        img_name = url.split('/')[-1]
                        save_img(url, img_name)
                        insert_imginfo(article_id, img_name)


def execute_spider():
    # 初始化疾病和对应url的字典
    url_dic = {
        'fitness': ['http://fitness.39.net/', 'http://fitness\.39\.net/a/\d{6}/\d{7}\.html', '1'],
        'gxy': ['http://heart.39.net/gxy/', 'http://heart\.39\.net/a/\d{6}/\d{7}\.html', '2'],
        'gxz': ['http://heart.39.net/gxz/', 'http://heart\.39\.net/a/\d{6}/\d{7}\.html', '3'],
        'tnb': ['http://tnb.39.net/', 'http://tnb\.39\.net/snxty/\d{6}/\d{7}\.html', '4'],
        'js': ['http://sports.39.net/', 'http://sports\.39\.net/a/\d{6}/\d{7}\.html', '5'],
        'ys': ['http://care.39.net/ys/', 'http://care\.39\.net/a/\d{6}/\d{7}\.html', '6'],
    }
    for key in url_dic:
        spider(url_dic[key][0], url_dic[key][1], url_dic[key][2])


execute_spider()
