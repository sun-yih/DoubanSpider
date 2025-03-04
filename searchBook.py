from lxml import etree
import json
import random
import requests
import time
import proxy
import user
import logging
from urllib.parse import quote


# 获取网页数据
def get_web_data(url, headers, proxies=[]):
    try:
        data = requests.get(url, proxies=proxies, timeout=3, headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error("请求错误，url:", url)
        logging.error("错误详情：", e)
        data = None
    except:
        logging.error("未知错误，url:", url)
        data = None
    return data


def getRequest(category, tag):
    tag_utf8 = tag.encode("utf-8")
    tag_url = quote(tag_utf8)
    urls = ["https://book.douban.com/tag/{}?start={}".format(tag_url, (i)) for i in
            range(0, 100, 20)]  # 豆瓣分类图书每页20本，搜索一百本，每次搜索完一页，数字加20表示跳转到下一页继续搜索
    for url in urls:
        # 每搜索1页20本书更换一次请求头信息和代理ip
        # 动态设置请求头信息
        headers = {'User-Agent': user.getuser()}
        # 动态设置代理ip信息
        List = proxy.get_proxies("https://www.kuaidaili.com/free/intr/", url, 5)
        proxies = random.choice(List)
        # 打印搜索时代理ip信息
        print(proxies)
        data = get_web_data(url, headers, proxy.get_random_ip(proxies))

        # data = requests.get(url, headers=headers, proxies=proxies)  # 此处是请求
        html = etree.HTML(data.text)  # 网页的解析
        count = html.xpath("//li[@class='subject-item']")
        for info in count:
            # 把页面获取的详情页面的信息转化成字符串link作为下面请求的url，有些网页比如京东在转化成字符串的同时需要在前面拼接"https://"
            link = ''.join(info.xpath("div[2]/h2/a/@href"))
            # 每爬取一本书线程休息随机时间，模拟人类行为
            time.sleep(random.random())
            # 控制台输出书籍详情页地址，便于观察爬取过程中的bug
            print('url of the book:' + link)
            # author_name在类别页获取，因为详情页每个页面的作者对应的块位置不同，存在获取不到作者情况，导致书籍信息获取失败
            # author_name =''.join(info.xpath("div[2]/div[1]/text()")[0].split('/')[0]).replace(" ","")
            # print(author_name)
            # author_name = author_name.split()

            # link_data = requests.get(link, headers=headers, proxies=proxies)
            link_data = get_web_data(link, headers, proxy.get_random_ip(proxies))
            # 获取到html
            html = etree.HTML(link_data.text)
            # 接下来对获取到的html进行处理
            # 书名
            book_name = html.xpath("//*[@id='mainpic']/a/@title")
            # 图片url
            book_img = html.xpath("//*[@id='mainpic']/a/img/@src")
            # 作者信息，因为不同页面位置不同做判断
            author_name = html.xpath("//*[@id='info']/span[1]/a/text()")
            temp = ''.join(html.xpath("//*[@id='info']/span[1]/a/text()"))
            if temp is None or len(temp) == 0:
                author_name = html.xpath("//*[@id='info']/a[1]/text()")
            # 作者人数大于1时候用/分隔，并去除多余空格和换行符
            sum = ""
            if len(author_name) > 1:
                for item in author_name:
                    sum += (str(item) + "/")
                    author_name = sum
            else:
                author_name = author_name
            author_name = "".join(author_name)
            author_name = author_name.replace(" ", "")
            author_name = author_name.replace("\n", "")
            author_name = author_name.split()

            # 出版社
            press = html.xpath(u'//span[./text()="出版社:"]/following::text()[1]')
            press = html.xpath('//span[contains(., "出版社:")]/following-sibling::a[1]/text()')
            # 出版年
            press_year = html.xpath(u'//span[./text()="出版年:"]/following::text()[1]')
            # 页数
            pages = html.xpath(u'//span[./text()="页数:"]/following::text()[1]')
            # 价格
            price = html.xpath(u'//span[./text()="定价:"]/following::text()[1]')
            # 图书ISBN
            ISBN = html.xpath(u'//span[./text()="ISBN:"]/following::text()[1]')
            # 评分
            score = html.xpath("//*[@id='interest_sectl']/div/div[2]/strong/text()")
            # 评价人数
            number_reviewers = html.xpath("//*[@id='interest_sectl']/div/div[2]/div/div[2]/span/a/span/text()")
            # 图书简介
            introduction = html.xpath("//*[@class='intro']/p/text()")

            for book_name, book_img, author_name, press, press_year, pages, price, ISBN, score, number_reviewers, introduction in zip(
                    book_name, book_img, author_name, press, press_year, pages, price, ISBN, score, number_reviewers,
                    introduction):
                result = {
                    "book_name": book_name,
                    "book_img": book_img,
                    "author_name": author_name,
                    "press": press,
                    "press_year": press_year,
                    "pages": pages,
                    "price": price,
                    "ISBN": ISBN,
                    "score": score,
                    "number_reviewers": number_reviewers,
                    "introduction": introduction
                }
                print(result)
                # 以json形式保存输出结果
                with open('books/{}/{}.json'.format(category, tag), 'a', encoding='utf-8') as file:
                    file.write(json.dumps(result, ensure_ascii=False) + ',\n')


if __name__ == '__main__':
    category_require = "流行"
    tags = ["余秋雨","东野圭吾","言情","推理小说","日本漫画","科幻小说","三毛"]
    fail_tags = []
    for tag in tags:
        try:
            tag_require = tag
            getRequest(category_require, tag_require)
        except Exception as e:
            print("Exception {} happens for tag: {}".format(e, tag))
            fail_tags.append(tag)
            pass

    if fail_tags:
        print("Failed tags:", fail_tags)
