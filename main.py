import asyncio
from config import Addcode, Domcode, ajaxcode
from pyppeteer import launch
from datetime import datetime
from threadpool import makeRequests, ThreadPool
from queue import Queue
from threading import Thread
from threading import Condition
from threading import Lock
from urllib import parse
import sys
import time
import os
import argparse
from datetime import datetime
import re
import json
import hashlib


class Topspider(object):
    """爬取类"""
    def __init__(self, url, depth, threadNum, file):
        """Initialization parameters"""
        """Operating status"""
        self.status = False
        """管理线程池数量唤醒及等待"""
        self.processcondition = Condition()
        """当前运行的线程数量"""
        self.currentrun = 0
        """url等待队列"""
        self.urlQue = Queue()
        """已经请求过的url"""
        self.visitedurl = []
        """线程数"""
        self.threadNum = threadNum
        """设定了线程数的线程池"""
        self.pool = ThreadPool(self.threadNum)
        """预期爬行深度"""
        self.depth = depth
        """初始化浏览器"""
        self.browser = ''
        self.tasksall=[]
        """打开json文件"""
        self.re_json = json.load(open('patten.json', 'r', encoding='utf-8'))
        self.resfile = 'resault.txt'
        """初始化队列"""
        for url in urllist:
            self.urlQue.put({'url': url, "depth": int(depth)})
        """当前爬取的url"""
        self.spiderdomain = 'start'

    def urlparser(self, url):
        """区别url是不是可以直接访问"""
        if url.startswith('http://') or url.startswith('https://'):
            url=url
        else:
            url = self.spiderdomain+'/'+url
        return url

    def Deduplication(self, u):
        """ 根据返回的数据类型来判断存储 """
        if type(u) == dict:
            urls = u['urls']
            depth = u['depth']
            for url in urls:
                if url!='':
                    url2= self.urlparser(url)
                    url1 = url2.encode(encoding='utf-8')
                    url_md5 = hashlib.md5(url1).hexdigest()
                    if url_md5 not in self.visitedurl:
                        with open('file.txt', 'a') as f:
                            f.write(str(url) + '\n')
                        self.urlQue.put({'url': url, "depth": depth})
        if type(u) == list:
            for t in u:
                with open(self.resfile, 'a') as f:
                    f.write(str(t) + '\n')
    def start(self):
        """开始爬取"""
        self.status = True
        print('\n[-] Spider Starting ...........Domain is %s' %self.spiderdomain)
        self.urlmanagement()
        self.stop()

    def spider(self, urls, loop):
        """主要爬虫函数"""
        s = 0
        print(urls)

        try:
            tasks = []
            urllist = []
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.get_browser())
            for x in urls:
                url = x['url']
                depth = x['depth']
                print(type(depth))
                if depth == 0:
                    print(222)
                    tasks.append(asyncio.ensure_future(
                        self.Identify_content(url)))
                else:
                    print(444)
                    tasks.append(asyncio.ensure_future(
                        self.get_url(url, depth)))
            future = asyncio.wait(tasks)
            loop.run_until_complete(future)
            for task in tasks:
                self.Deduplication(task.result())
            loop.run_until_complete(self.close_browser())
        except Exception as e:
            self.processcondition.acquire()
            self.currentrun = self.currentrun - 1
            s = s + 1
            self.processcondition.release()
            if s == len(urls):
                self.processcondition.notify()
                return None
        self.processcondition.acquire()
        self.currentrun = self.currentrun - (len(urls) - s)
        self.processcondition.notify()
        self.processcondition.release()

    def urlmanagement(self):
        """处理url，分批进行爬取内容。采用线程池"""
        self.processcondition.acquire()
        while True:
            if not (self.urlQue.empty() and self.currentrun == 0):
                urls = []
                spiderlist = []
                while not self.urlQue.empty():
                    item = self.urlQue.get()
                    if item not in self.visitedurl:
                        urls.append(item)
                        murl = item['url'].encode(encoding='utf-8')
                        url_md = hashlib.md5(murl).hexdigest()
                        self.visitedurl.append(url_md)
                threadn = len(urls)
                step = 5
                for i in range(0, len(urls), step):
                    ulist = urls[i:i + step]
                    i = asyncio.new_event_loop()
                    x = ([ulist, i], None)
                    spiderlist.append(x)
                request = makeRequests(self.spider, spiderlist)
                self.currentrun = self.currentrun + threadn
                [self.pool.putRequest(g) for g in request]
                self.processcondition.wait()
            else:
                break
    def stop(self):
        """结束函数,现在还没有作用。可当作判断是否结束爬取"""
        # self.urlfile.close()
        self.status = False

    async def get_browser(self):
        """打开浏览器"""
        self.browser = await launch({'headless': True,'handleSIGINT': False,'handleSIGTERM': False,'handleSIGHUP': False})

    async def close_browser(self):
        """关闭浏览器"""
        await self.browser.close()

    async def get_url(self, url, depth):
        """只获取页面中的url,依据深度来判断。深度为0时不进行此函数，返回字典"""
        if depth >= int(self.depth):
            dep = 0
        else:
            dep = depth + 1
        # print(dep)
        page = await self.browser.newPage()
        await page.evaluate(ajaxcode)
        await page.evaluate(Addcode)
        await page.goto(url)
        await page.waitFor(5000)
        Domcode1 = await page.evaluate(Domcode)
        ls = Domcode1.split('***')
        elementsj = await page.querySelectorAll('script')
        for  elementj in elementsj:
            url2 =await page.evaluate('(elementj) => elementj.src', elementj)
            ls.append(url2)
        lls = {'depth': dep, 'urls': set(ls)}
        print(55555)
        return lls

    async def Identify_content(self, url):
        """深度为0时，进行此函数。依靠正则爬取页面内容，可自定义。返回列表"""
        re_list = []
        page = await self.browser.newPage()
        await page.goto(url)
        await page.waitFor(5000)
        if parse.urlparse(url).path.split('.')[-1].startswith('js'):
            mm=[]
            html = await page.content()
            print(html)
            # for keys in self.re_json.keys():
            #     pattern = r'([a-z]+(/[0-9a-z]+)+/?)+'
            #     pattern2 = r'\"[^"]*\"'
            #     m = re.compile(pattern2, re.S).findall(html)
            #     # print(m)
            #     text=[]
            #     for l in m:
            #         # print(l+'111111')
            #         # print(l)
            #         m2 = re.search(pattern,l.strip('\"'),re.I)
            #         if m2:
            #             text.append(m2.group(1))
            #             print(m2.group(1))
            regex_str = r"""
              (?:"|')                               # Start newline delimiter
              (
                ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
                [^"'/]{1,}\.                        # Match a domainname (any character + dot)
                [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
                |
                ((?:/|\.\./|\./)                    # Start with /,../,./
                [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
                [^"'><,;|()]{1,})                   # Rest of the characters can't be
                |
                ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
                [a-zA-Z0-9_\-/]{1,}                 # Resource name
                \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
                (?:[\?|/][^"|']{0,}|))              # ? mark with parameters
                |
                ([a-zA-Z0-9_\-]{1,}                 # filename
                \.(?:php|asp|aspx|jsp|json|
                     action|html|js|txt|xml)             # . + extension
                (?:\?[^"|']{0,}|))                  # ? mark with parameters
              )
              (?:"|')                               # End newline delimiter
            """
            regex=re.compile(regex_str, re.VERBOSE)
            print(html)
            for m in re.finditer(regex,html):
                mm.append(m.group(1))
                print(m.group(1))
        else:
            mm = await page.title()
        re_list = [{url: mm}]
        await asyncio.sleep(3)
        return re_list


class printInfo(Thread):
    """信息打印类"""
    def __init__(self, Topspider):
        Thread.__init__(self)
        """开始时间"""
        self.startTime = datetime.now()
        """设置为守护线程"""
        self.daemon = True
        """爬虫类"""
        self.topspider = Topspider
        """开启线程，相当于调用了run"""
        self.start()

    def printEnd(self):
        """信息结束"""
        self.endTime = datetime.now()
        print ('Crawl Depth:%d, Totally visited %d links.\n' % (self.topspider.depth, len(self.topspider.visitedurl)))
        print('Start at: '+self.startTime.strftime("%Y-%m-%d %H:%M:%S"))
        print ('End at: '+self.endTime.strftime("%Y-%m-%d %H:%M:%S"))
        print ('Spend time: '+str((self.endTime - self.startTime).seconds)+'s')
        print ('[-] Finished......')

    def run(self):
        while True:
            if self.topspider.status is True:
                time.sleep(10)
                print('[+] Now totally visited %s links , %s Coroutines is running .\n' % (int(len(self.topspider.visitedurl)), int(self.topspider.currentrun)))


if __name__ == '__main__':
    print('[+] Run current process pid:%s...' % os.getpid())
    parser = argparse.ArgumentParser(description="Spider URL Informations")
    group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "-d", "--depth", help="set spider depth,default 1", default=1)
    group.add_argument(
        "-u", "--url", help="set spider url")
    group.add_argument(
        "-us", "--urls", help="set spider urls")
    parser.add_argument(
        "-t", "--threadNum", help="set threads num,default 3", default=1)
    parser.add_argument(
        '-f', '--file', help='set save path', default='file.txt')
    parser.add_argument(
        "-v", '--version', action='version', version='version 1.0')
    args = parser.parse_args()
    urllist = []
    if args.urls:
        with open(args.urls, 'r') as f:
            for i in  f.read().split('\n'):
                print(i)
                if i.startswith('http://') or i.startswith('https://'):
                    urllist.append(i)
                else:
                    urllist.append('http://'+i)
    print(urllist)
    if args.url is None and urllist == ['']:
        print(parser.print_help())
    else:
        if args.url:
            urllist.append(args.url)

        spider = Topspider(urllist, args.depth, args.threadNum, args.file)
        # info = printInfo(spider)
        spider.start()
        # info.printEnd()