import asyncio
from pyppeteer import launch
from pyppeteer.errors import TimeoutError
import proxy as xy
from database import db
from random import choice
from datetime import datetime
import requests
import json
import re
import pandas as pd
import holtWinters
from scipy.optimize import minimize
from datetime import datetime

exchangeRate = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()['Valute']

xpathDict = {
    # 'name': "//h1[@id='largeiteminfo_item_name']",
    # 'type': "//div[@id='largeiteminfo_item_type']",
    # 'rarity': "//div[@id='largeiteminfo_item_descriptors']/div[1]",
    # 'description': "//div[@id='largeiteminfo_item_descriptors']/div",
    # 'img': "//div[@class='market_listing_largeimage']/img",
    'buyRequestsTotal': "//div[@id='market_commodity_buyrequests']/span[1]",
    'buyRequests': "//div[@id='market_commodity_buyreqeusts_table']/table/tbody/tr[2]/td[2]",
    'buyPrice': "//div[@id='market_commodity_buyrequests']/span[2]",
    'sellTotal': "//span[@id='searchResults_total']",
    'sellPrices': "//div[@id='searchResultsRows']/div/div/div[@class='market_listing_right_cell market_listing_their_price']/span[@class='market_table_value']/span[@class='market_listing_price market_listing_price_with_fee'][1]",

    # 'names': "//div[@class='market_listing_item_name_block']/span[@class='market_listing_item_name']",
    # 'imgs': "//div[@id='searchResultsRows']/a/div/img",
    # 'urls': "//div[@id='searchResultsRows']/a",
    # 'quantity': "//span[@class='market_listing_num_listings_qty']",
    # 'prices': "//span[@class='normal_price']",
    
    'type': "//div[@class='full-item ng-star-inserted']/div/app-full-item-info/div/div[1]",
    'name': "//div[@class='full-item ng-star-inserted']/div/app-full-item-info/div/div[2]",
    'rarity': "//div[@class='full-item ng-star-inserted']/div/app-full-item-info/div/div[3]/div[1]",
    'collection': "//div[@class='full-item ng-star-inserted']/div/app-full-item-info/div/div[3]/div[2]",
    'stickers': "//div[@class='full-item ng-star-inserted']/div/app-full-item-info/div/div[3]/div[3]/a",
    'category': "//div[@class='full-item ng-star-inserted']/div/app-full-item-info/div/div[4]/div[1]/div",
    'amount': "//div[@class='full-item ng-star-inserted']/div/app-full-item-info/div/div[4]/div[2]/div",
    'float': "//div[@class='full-item ng-star-inserted']/div/app-full-item-info/div/div[5]/div[2]",
    'description': "//div[@class='full-item ng-star-inserted']/div[2]/app-item-description/div/div",
    'img': "//div[@class='full-item ng-star-inserted']/div/div/div/div/img",
    'sellPrices': "//div[@class='full-item ng-star-inserted']/div[3]/div/app-related-items/div/div/div/a",
    'sellMin': "//history-chart/div/div[1]/span[1]/span[1]",
    'sellMax': "//history-chart/div/div[2]/span[1]/span[1]",
    'quantity': "//history-chart/div/div[3]",
    # 'history': 
    
    'names': "//div[@class='cdk-virtual-scroll-content-wrapper']/a/app-base-item/div/div/div/div/div[3]",
    'urls': "//div[@class='cdk-virtual-scroll-content-wrapper']/a",
    'imgs': "//div[@class='cdk-virtual-scroll-content-wrapper']/a/app-base-item/div/div/div/div/img",
    'rarity+status': "//div[@class='cdk-virtual-scroll-content-wrapper']/a/app-base-item/div/div/div/div/div[1]",
    'prices': "//div[@class='cdk-virtual-scroll-content-wrapper']/a/app-base-item/div/div/div/div/div[2]",
    
}

async def connect(userAgent: str, proxy: str):
    return await launch({
        'executablePath': 'D:/Program Files/Google/Chrome/Application/chrome.exe',
        'headless': False,
        'devtools': True,
        'autoClose': False,
        'args': [
            # '--lang=en',
            '--disable-infobars',
            # '--start-maximized',
            # '--no-sandbox',
            # f'--proxy-server="https={proxy}"',
            f'--user-agent={userAgent}'
        ]
    })

async def getElement(page, xpath: str, property: str):
    try:
        await page.waitForXPath(xpath, timeout=3*1000)
    except TimeoutError:
        return ['']
    else:
        return [await (await _.getProperty(property)).jsonValue() for _ in (await page.xpath(xpath))]
    
async def getItem(page, url: str):
    await page.goto(url)
    await page.waitFor(1000)
    try:
        float_ = (await getElement(page, xpathDict['float'], 'textContent'))[0].strip()
        return {
            'type': (await getElement(page, xpathDict['type'], 'textContent'))[0].strip(),
            'name': (await getElement(page, xpathDict['name'], 'textContent'))[0].strip(),
            'rarity': (await getElement(page, xpathDict['rarity'], 'textContent'))[0].strip(),
            'amount': (await getElement(page, xpathDict['amount'], 'textContent'))[0].strip(),
            'category': (await getElement(page, xpathDict['category'], 'textContent'))[0].strip(),
            'collection': (await getElement(page, xpathDict['collection'], 'textContent'))[0].strip(),
            'float': float_[:float_.rfind(' (')],
            'stickers': (await getElement(page, xpathDict['stickers'], 'href')),
            'img': (await getElement(page, xpathDict['img'], 'src'))[0].strip(),
            
            'sellMin': float((await getElement(page, xpathDict['sellMin'], 'textContent'))[0].strip()),
            'sellMax': float((await getElement(page, xpathDict['sellMax'], 'textContent'))[0].strip()),
            'quantity': (await getElement(page, xpathDict['quantity'], 'textContent'))[0].strip(),
            'sellPricesUrls':(await getElement(page, xpathDict['sellPrices'], 'href')),
            'sellPrices': [([float(_) for _ in  _[1].split('-')][0], float(_[2].replace('₽', ''))) for _ in [_.replace('\n', '').split() for _ in (await getElement(page, xpathDict['sellPrices'], 'textContent'))]],
    #         'sellTotal': int((await getElement(page, xpathDict['sellTotal'], 'textContent'))[0].replace('\xa0', '').strip()),
    #         'name': (await getElement(page, xpathDict['name'], 'textContent'))[0].strip(),
    #         'type': (await getElement(page, xpathDict['type'], 'textContent'))[0].strip(),
    #         'rarity': (await getElement(page, xpathDict['rarity'], 'textContent'))[0].replace('Exterior: ', '').strip(),
    #         'description': ('').join(await getElement(page, xpathDict['description'], 'textContent')).replace('\n\n', ' ').replace('\n', ' ').replace('\xa0', '. ').strip(),
    #         'img': (await getElement(page, xpathDict['img'], 'src'))[0].strip(),
    #         'buyRequestsTotal': int((await getElement(page, xpathDict['buyRequestsTotal'], 'textContent'))[0].replace(',', '').strip()),
    #         'buyRequests': int((await getElement(page, xpathDict['buyRequests'], 'textContent'))[0].strip()),
    #         'buyPrice': float((await getElement(page, xpathDict['buyPrice'], 'textContent'))[0].replace('$','').replace(',', '').strip()),
            
    #         'sellPrices': [_.replace('\n', '').replace('\t', '') for _ in (await getElement(page, xpathDict['sellPrices'], 'textContent'))],
    #         'date': datetime.now().strftime('%d.%m.%y'),
    #         'time': datetime.now().strftime('%H:%M:%S')
        }
    except Exception as e:
        print(e)
        return None

# async def autoScroll(page):
#     await page.evaluate('''() => {
#         await new Promise((resolve) => {
#             var totalHeight = 0;
#             var distance = 100;
#             var timer = setInterval(() => {
#                 var scrollHeight = document.body.scrollHeight;
#                 window.scrollBy(0, distance);
#                 totalHeight += distance;

#                 if(totalHeight >= scrollHeight - window.innerHeight){
#                     clearInterval(timer);
#                     resolve();
#                 }
#             }, 100);
#         });
#     }''')


liner = lambda x: int(x[1].replace('%', '')) if len(x) != 1 else 0
async def getItems(page, url: str, pageIdx: int=1, mode: str='popular_desc'):
    print()
    # urlPage = f'{url}#p{pageIdx}_{mode}'
    
    # await page.setJavaScriptEnabled(True)
    # await page.continue_(method='GET /ru/ HTTP/1.1')
    # await page.setExtraHTTPHeaders(headers={
    #     'Host': 'market-new.csgo.com',
    #     'Accept': '*/*',
    # })
    # await page.setCookie({
    #     'name': 'PHPSESSID',
    #     # 'value': '842061923%3Ac93315448faa011216b5fb6c6d2f5bcc',
    #     'value': '842061923:c93315448faa011216b5fb6c6d2f5bcc',
    #     'domain': 'market-new.csgo.com',
    #     'path': '/',
    #     # 'expires': float(datetime.utcnow().timestamp()),
    #     'httpOnly': True,
    #     'secure': True,
    # })
    
    # await page.setBypassCSP(True)
    # await page.setJavaScriptEnabled(True)
    # await page.setOfflineMode(True)
    # await page.setRequestInterception(True)
    # await page.waitFor(1000)
    response = await page.goto(url)
    # response.setRequestInterception(True)
    await page.waitFor(1000)
    # print(type((await page.cookies())[0]['expires']))
    # print(await page.cookies())
    print(await page.cookies(), response.request.method, response.request.headers, response.headers, sep='\n\n')
    # print([_.strip() for _ in (await getElement(page, xpathDict['nameN'], 'src'))])
    # await response.request.continue_(overrides={'method': 'GET /ru/ HTTP/1.1'})
    # print(dir(page))
#     try:



    # await page.keyboard.press('End')
    # with await page.keyboard.down('Control'): await page.keyboard.press('Minus')
    # [await page.keyboard.type('[Control+-]') for _ in range(10)]
    # await page.setViewport({
    #     'width': 0,
    #     'height': 0,
    #     # 'deviceScaleFactor': 1.0 / 64
    # })
    
    # await page.waitFor(1000)
    
    slicer = await page.evaluate('''() => {
        return {
            height: document.documentElement.clientHeight,
            allHeight: document.documentElement.scrollHeight
        }
    }''')
    print(slicer)
    all = []
    for i, _ in enumerate(range(0, slicer['allHeight'], int(slicer['height'] * 0.25))):
        await page.evaluate(f'() => window.scrollTo(0, {_})')
        statusCase = [_ for _ in (await getElement(page, xpathDict['rarity+status'], 'textContent'))]
        priceCase = [_ for _ in (await getElement(page, xpathDict['prices'], 'textContent'))]
        zipper = zip(
            # [int(_.strip().replace(',', '')) for _ in (await getElement(page, xpathDict['quantity'], 'textContent'))],
            # [float(_.strip().replace('$','').replace(' USD', '').replace(',', '')) for _ in (await getElement(page, xpathDict['prices'], 'textContent'))],
            # [float(_.strip().replace('₽', '').split('-')[0]) for _ in (await getElement(page, xpathDict['prices'], 'textContent'))],
            [float(_.strip().replace('₽', '').split('-')[0]) for _ in priceCase],
            [liner(_.strip().replace('₽', '').split('-')) for _ in priceCase],
            [_ for _ in statusCase],
            [_.strip() for _ in (await getElement(page, xpathDict['names'], 'textContent'))],
            [_.strip() for _ in (await getElement(page, xpathDict['urls'], 'href'))],
            [_.strip() for _ in (await getElement(page, xpathDict['imgs'], 'src'))]
        )
        all.extend(zipper)
        print(i + 1, _, len(list(zipper)), slicer)
    print(len(all))
    [all.remove(_) for _ in all if all.count(_) > 1]
    print(len(all))
#         return [{'name': name, 'url': url, 'img': img, 'quantity': quantity, 'price': price, 'date': datetime.now().strftime('%d.%m.%y'), 'time': datetime.now().strftime('%H:%M:%S')} for quantity, price, name, url, img in zipper]
#     except Exception as e:
#         print(e)
#         return None

async def get(userAgent: str, proxy: str, request: str='items', **config):
    browser = await connect(userAgent=userAgent, proxy=proxy)
    page = (await browser.pages())[0]
    if request == 'items': elements = await getItems(page, **config)
    if request == 'item': elements = await getItem(page, **config)
    # await browser.close()
    return(elements if elements else [])

from fake_useragent import UserAgent
print(asyncio.run(get(UserAgent().random, '46.4.242.214:1337', 'item', url='https://market-new.csgo.com/ru/P90/P90%20%7C%20Asiimov%20%28Battle-Scarred%29')))
url='https://market-new.csgo.com/ru/?priceMax=20000&other=csp&rarity=Consumer%20Grade&rarity=Industrial%20Grade&rarity=Mil-Spec%20Grade&rarity=Restricted&rarity=Classified&rarity=Covert&rarity=Contraband'