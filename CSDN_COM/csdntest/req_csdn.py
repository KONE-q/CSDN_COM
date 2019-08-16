from selenium.webdriver.support.wait import WebDriverWait
import selenium.webdriver
import lxml.etree
import requests
import re,json
import time
import threading
import urllib3

urllib3.disable_warnings() #防止https报错

'''
1.通过selenium模拟滑动滚条获得数据（由于csdn的ajax加载的数据的url有时并不会改变参数，直接通过url获取数据有一定的麻烦，所以通过每次滑动滚条获取数据）
2.通过多线程爬取csdn首页不同分类的数据（由于’关注‘栏需要登录才能获得，所以不爬取，而’人工智能‘和’区块链‘的url与其他的规律不同，也不爬取）
3.通过requests获得文章数据
4.再通过获取到的文章的url获取文章内容
5.保存数据
'''


class selenium_thread(threading.Thread):
    def __init__(self,url,sort_type,sort_name):
        super(selenium_thread,self).__init__()
        self.url = url
        self.sort_type = sort_type
        self.sort_name = sort_name
        # options = selenium.webdriver.ChromeOptions()
        # options.add_argument('--headless')
        self.driver = selenium.webdriver.Chrome('E:/gugedriver/chromedriver.exe') #启动浏览器

    '''通过模拟人为滑动滚条置底部，触发ajax文件发送代码'''
    def scor_window(self):
        self.driver.get(self.url)   #获取csdn分类数据的首页
        time.sleep(2)
        # print(self.sort_type)
        check_height = self.driver.execute_script("return document.body.scrollHeight;")  #获得网页body的高度
        run_times = 0
        while True:
            # time.sleep(1)
            if run_times <= 100:    #通过run_times控制获得数据
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                try:
                    WebDriverWait(self.driver, 10).until(
                        lambda driver: self.driver.execute_script("return document.body.scrollHeight;") > check_height)
                    check_height = self.driver.execute_script("return document.body.scrollHeight;")
                    url = 'https://www.csdn.net/api/articles?type=more&category=%s&shown_offset=0' % (self.sort_type)
                    print(self.sort_name[0]+ '-run_times:' + str(run_times))
                    run_times += 1
                    self.get_data(url)
                except Exception as e:
                    print(e)
                    continue

    def get_data(self,url):   #获取json数据
        # print(1)
        try:
            content = requests.get(url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60'},verify=False).content
            data = json.loads(content,encoding='utf-8')
            data = str(data)
            article_title = re.compile("'title': '(.*?)'").findall(data)
            article_url = re.compile("'url': '(.*?)'").findall(data)
            article_createtime = re.compile("'created_at': '(.*?)'").findall(data)
            user_name = re.compile("'user_name': '(.*?)'").findall(data)
            nickname = re.compile("'nickname': '(.*?)'").findall(data)
            for i in range(0,len(article_url)):
                title = title = re.sub('(\s|/|\\\\|\||\?)','_',article_title[i])
                art_url = article_url[i]
                c_time = article_createtime[i]
                u_name = user_name[i]
                n_name = nickname[i]
                self.articles(art_url,title,c_time,u_name,n_name)
        except Exception as e:
            print(1)
            print(e)


    def articles(self,art_url,title,c_time,u_name,n_name):  #获得文章内容
        # print(2)
        try:
            content = requests.get(art_url,headers={'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60'},verify=False).content
            content = lxml.etree.HTML(content)
            article = content.xpath('//div[@id="content_views"]')[0]
            art_content = article.xpath('string(.)')
            art_content = re.sub(' ','',str(art_content))
            # print(art_content)
            read_num = content.xpath('//span[@class="read-count"]/text()')
            # print(read_num)
            self.save_data(art_url,title,c_time,u_name,n_name,read_num)
            self.save_art(title,art_content)
            # time.sleep(2)
        except Exception as e:
            print(2)
            print(e)


    def save_data(self,art_url,title,c_time,u_name,n_name,read_num):
        # print(3)
        t = re.sub('/','_',self.sort_name[0])
        with open('D:\\SCRAPY_FILES\\CSDN_COM\\CSDN_COM\\data_file\\%s.txt'%t,'a+',encoding='utf-8') as f :
            f.write(art_url+' '+ title + ' '+c_time+' '+u_name+' '+n_name+' '+read_num[0]+'\n')


    def save_art(self,title,art_content):
        # print(4)
        with open('D:\\SCRAPY_FILES\\CSDN_COM\\CSDN_COM\\data_file\\html_files\\{}.txt'.format(title),
                  'w', encoding='utf-8') as f1:
            f1.write(art_content.strip())

    def run(self):
        self.scor_window()




if __name__ == '__main__':
    page = requests.get('https://www.csdn.net/',headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36'},verify=False).content
    page = lxml.etree.HTML(page)
    list_sort = page.xpath('//div[@class="nav_com"]/ul/li')
    url_list = []
    name_list = []
    type_list= []
    thread_list = []
    for sort_li in list_sort:
        sort_name = sort_li.xpath('./a/text()')
        sort_href = sort_li.xpath('./a/@href')
        # print(sort_name)
        sort_type = re.split('/', str(sort_href[0]))
        # print(sort_type)
        if len(sort_type) < 3 or sort_type[0] == 'https:' or sort_type[2] == 'watchers':
            continue
        a_type = sort_type[2]
        sort_url = "https://www.csdn.net" + sort_href[0]
        url_list.append(sort_url)
        name_list.append(sort_name)
        type_list.append(a_type)

    for i in range(0,len(url_list)):  #启动线程
        # print(url_list[i])
        T1 = selenium_thread(url_list[i],type_list[i],name_list[i])
        T1.start()
        thread_list.append(T1)

    for t in thread_list:     #保护线程执行
        t.join()