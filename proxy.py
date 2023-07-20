import requests
from bs4 import BeautifulSoup
from lxml.html import fromstring
from lxml import etree
from itertools import cycle
from fake_useragent import UserAgent
from random import choice

def getProxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr'):
        if i.xpath(".//td[7][contains(text(),'yes')]"):
            proxy = (':').join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

def getProxiesPool():
    proxies = getProxies()
    return cycle(proxies)

def randomProxy():
    return choice(list(getProxies()))

def randomUserAgent():
    return UserAgent().random

def checkProxy(url: str, proxy: str):
    try:
        requests.get(url, proxies={'https': proxy})
    except:
        return False
    else:
        return True

def checkConnection(url: str, proxy: str=randomProxy(), userAgent: str=randomUserAgent(), timeout: int=10):
    seconds = None
    try:
        response = requests.get(url, proxies={'https': proxy}, headers={'User-Agent': userAgent}, timeout=timeout)
        # print(response.status_code)
        # try:
        #     el = etree.HTML(str(BeautifulSoup(response.content, 'html.parser'))).xpath("//div[@id='message']/h1").text
        #     print(el)
        # except:
        #     print('no')
        seconds = response.elapsed.total_seconds()
    except:
        return False, (proxy, userAgent, seconds)
    else:
        return True, (proxy, userAgent, seconds)

# userAgent = UserAgent().random

# print(getProxiesPool()[3])
# print (checkProxy('https://steamcommunity.com/market'))