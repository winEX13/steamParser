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

exchangeRate = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()['Valute']

xpathDict = {
    'name': "//h1[@id='largeiteminfo_item_name']",
    'type': "//div[@id='largeiteminfo_item_type']",
    'rarity': "//div[@id='largeiteminfo_item_descriptors']/div[1]",
    'description': "//div[@id='largeiteminfo_item_descriptors']/div",
    'img': "//div[@class='market_listing_largeimage']/img",
    'buyRequestsTotal': "//div[@id='market_commodity_buyrequests']/span[1]",
    'buyRequests': "//div[@id='market_commodity_buyreqeusts_table']/table/tbody/tr[2]/td[2]",
    'buyPrice': "//div[@id='market_commodity_buyrequests']/span[2]",
    'sellTotal': "//span[@id='searchResults_total']",
    'sellPrices': "//div[@id='searchResultsRows']/div/div/div[@class='market_listing_right_cell market_listing_their_price']/span[@class='market_table_value']/span[@class='market_listing_price market_listing_price_with_fee'][1]",

    'names': "//div[@class='market_listing_item_name_block']/span[@class='market_listing_item_name']",
    'imgs': "//div[@id='searchResultsRows']/a/div/img",
    'urls': "//div[@id='searchResultsRows']/a",
    'quantity': "//span[@class='market_listing_num_listings_qty']",
    'prices': "//span[@class='normal_price']"
}

async def connect(userAgent: str, proxy: str):
    return await launch({
        'headless': False,
        'devtools': True,
        'autoClose': True,
        'args': [
            '--lang=en',
            '--disable-infobars',
            # '--no-sandbox',
            f'--proxy-server="https={proxy}"',
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
    try:
        return {
            'sellTotal': int((await getElement(page, xpathDict['sellTotal'], 'textContent'))[0].replace('\xa0', '').strip()),
            'name': (await getElement(page, xpathDict['name'], 'textContent'))[0].strip(),
            'type': (await getElement(page, xpathDict['type'], 'textContent'))[0].strip(),
            'rarity': (await getElement(page, xpathDict['rarity'], 'textContent'))[0].replace('Exterior: ', '').strip(),
            'description': ('').join(await getElement(page, xpathDict['description'], 'textContent')).replace('\n\n', ' ').replace('\n', ' ').replace('\xa0', '. ').strip(),
            'img': (await getElement(page, xpathDict['img'], 'src'))[0].strip(),
            'buyRequestsTotal': int((await getElement(page, xpathDict['buyRequestsTotal'], 'textContent'))[0].replace(',', '').strip()),
            'buyRequests': int((await getElement(page, xpathDict['buyRequests'], 'textContent'))[0].strip()),
            'buyPrice': float((await getElement(page, xpathDict['buyPrice'], 'textContent'))[0].replace('$','').replace(',', '').strip()),
            
            'sellPrices': [_.replace('\n', '').replace('\t', '') for _ in (await getElement(page, xpathDict['sellPrices'], 'textContent'))],
            'date': datetime.now().strftime('%d.%m.%y'),
            'time': datetime.now().strftime('%H:%M:%S')
        }
    except Exception as e:
        print(e)
        return None

async def getItems(page, url: str, pageIdx: int=1, mode: str='popular_desc'):
    urlPage = f'{url}#p{pageIdx}_{mode}'
    await page.goto(urlPage)
    try:
        zipper = zip(
            [int(_.strip().replace(',', '')) for _ in (await getElement(page, xpathDict['quantity'], 'textContent'))],
            [float(_.strip().replace('$','').replace(' USD', '').replace(',', '')) for _ in (await getElement(page, xpathDict['prices'], 'textContent'))],
            [_.strip() for _ in (await getElement(page, xpathDict['names'], 'textContent'))],
            [_.strip() for _ in (await getElement(page, xpathDict['urls'], 'href'))],
            [_.strip() for _ in (await getElement(page, xpathDict['imgs'], 'srcset'))]
        )
        return [{'name': name, 'url': url, 'img': img, 'quantity': quantity, 'price': price, 'date': datetime.now().strftime('%d.%m.%y'), 'time': datetime.now().strftime('%H:%M:%S')} for quantity, price, name, url, img in zipper]
    except Exception as e:
        print(e)
        return None

async def get(userAgent: str, proxy: str, request: str='items', **config):
    browser = await connect(userAgent=userAgent, proxy=proxy)
    page = (await browser.pages())[0]
    if request == 'items': elements = await getItems(page, **config)
    if request == 'item': elements = await getItem(page, **config)
    await browser.close()
    return(elements if elements else [])
    
    
def getPriceHistory(url: str, reverse: bool=False):
    try:
        return sorted([(datetime.strptime(re.sub(r': .+', '', time), '%b %d %Y %H'), float(price), int(quantity)) for time, price, quantity in json.loads(re.search(r'var line1=(.+);', requests.get(url).text).group(1))], key=lambda x: x[0], reverse=reverse)
    except Exception as e:
        print(e)
        return None

def priceTrend(data: list, slice: int, accuracy: int=1):
    data = pd.Series(data)
    modelData = data[:-500]
    x = [0, 0, 0]
    setattr(holtWinters, 'data', modelData)
    opt = minimize(holtWinters.timeseriesCVscore, x0=x, method="TNC", bounds = ((0, 1), (0, 1), (0, 1)))
    alpha_final, beta_final, gamma_final = opt.x
    
    model = holtWinters.HoltWinters(data[:-1*slice], slen = 24*7, alpha = alpha_final, beta = beta_final, gamma = gamma_final, n_preds = 128, scaling_factor = 2.56)
    model.triple_exponential_smoothing()
    result = model.result
    dataFlow = data.rolling(window=24*7).mean().reset_index().values.tolist()
    resultFlow = pd.Series(result).rolling(window=24*7).mean().reset_index().values.tolist()
    dataFlowWR = [(round(_[1], accuracy), _[0]) for _ in dataFlow]
    resultFlowWR = [(round(_[1], accuracy), _[0]) for _ in resultFlow]
    intersection = int(sorted(list(set(dataFlowWR).intersection(resultFlowWR)), key = lambda x: x[1])[-1][1]) - 3
    # plt.plot(*zip(*dataFlow[intersection:]))
    # plt.plot(*zip(*resultFlow[intersection:]))
    # plt.show()
    return list(zip(*dataFlow))[1], list(zip(*resultFlow))[1], intersection

def priceTrendShow(data: list, time: list, step: str, slice: int, accuracy: int=1):
    dataFlow, resultFlow, intersection = priceTrend(data, slice, accuracy)
    plt.subplot(211)
    plt.plot(dataFlow)
    step = len(time) // 9
    plt.gca().set_xticks(range(len(time))[::step])
    plt.gca().set_xticklabels(time[::step], ha='left', fontsize=6)
    plt.subplot(212)
    plt.plot(dataFlow[intersection:])
    plt.plot(resultFlow[intersection:])
    plt.show()
    
def priceTrendScore(url: str):
    history = getPriceHistory(url)
    weekScore = [_[1] for _ in history if datetime.now() - timedelta(days=7, hours=23) <= _[0]]
    # weekScoreDifference = max(weekScore) - min(weekScore)
    monthScore = [_[1] for _ in history if datetime.now() - timedelta(days=30, hours=23) <= _[0]]
    # monthScoreDifference = max(monthScore) - min(monthScore)
    totalScore = [_[1] for _ in history]
    # totalScorexDifference = max(totalScore) - min(totalScore)
    # plt.plot(pd.Series(monthScore).rolling(window=30).mean())
    # plt.show()
    return max(weekScore), max(monthScore), max(totalScore)

def mean(l: list):
    if len(l) != 0:
        return sum(l)/len(l)
    else:
        return 1

def getListIdx(l: list, idx: str):
    return [_[idx] for _ in l]

def trendHistory(url: str):
    history = getPriceHistory(url)
    if history:
        weekScore = [_ for _ in history if (datetime.now() - timedelta(days=7, hours=23)) <= _[0]]
        previousWeekScore = [_ for _ in history if (datetime.now() - timedelta(days=14, hours=23)) <= _[0] <= (datetime.now() - timedelta(days=7, hours=23))]
        monthScore = [_ for _ in history if datetime.now() - timedelta(days=30, hours=23) <= _[0]]
        totalScore = [_ for _ in history]
        
        weekScorePrice = getListIdx(weekScore, 1)
        weekScorePriceMean = mean(weekScorePrice)
        previousWeekScorePrice = getListIdx(previousWeekScore, 1)
        previousWeekScorePriceMean = mean(previousWeekScorePrice)
        monthScorePrice = getListIdx(monthScore, 1)
        monthScorePriceMean = mean(monthScorePrice)
        totalScorePrice = getListIdx(totalScore, 1)
        totalScorePriceMean = mean(totalScorePrice)
        
        weekScoreQuantity = sum(getListIdx(weekScore, 2))
        previousWeekScoreQuantity = sum(getListIdx(previousWeekScore, 2))
        monthScoreQuantity = sum(getListIdx(monthScore, 2))
        totalScoreQuantity = sum(getListIdx(totalScore, 2))
        return (weekScorePriceMean, weekScoreQuantity), (previousWeekScorePriceMean, previousWeekScoreQuantity), (monthScorePriceMean, monthScoreQuantity), (totalScorePriceMean, totalScoreQuantity)

def priceTrendStart(url: str):
    history = getPriceHistory(url)
    if history:
        return (datetime.now() - history[0][0]).total_seconds()

def capacityTrend(url: str):
    # buyers = getImportant(url)['buyRequestsTotal']
    history = trendHistory(url)
    if history:
        return [mean_ * quantity for mean_, quantity in history]

def priceGeneralForm(prices: list):
    fixedPrices = []
    for price in prices:
        print(repr(price))
        if ' pуб.' in price:
            price = price.replace(' pуб.', '').replace(',', '.')
            try:
                price = float(price)
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif price.startswith('$') or ' USD' in price:
            price = price.replace('$', '').replace(' USD', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['USD']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
        
        elif '€' in price:
            price = price.replace('€', '').replace(',--', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['EUR']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif '¥' in price:
            price = price.replace('¥ ', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['CNY']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif 'zł' in price:
            price = price.replace('zł', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['PLN']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif '฿' in price:
            price = price.replace('฿', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['THB']['Value'] / 10
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif '£' in price:
            price = price.replace('£', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['GBP']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif ' kr' in price:
            price = price.replace(' kr', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['SEK']['Value'] / 10
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif 'CDN ' in price:
            price = price.replace('CDN ', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['CAD']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif 'R$' in price:
            price = price.replace('R$', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['BRL']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif '₸' in price:
            price = price.replace('₸', '').replace(',', '.').replace(' ', '')
            try:
                price = float(price) * exchangeRate['KZT']['Value'] / 10
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif 'S$' in price:
            price = price.replace('S$', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['SGD']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif ',00 TL' in price:
            price = price.replace(',00 TL', '').replace('.', '')
            try:
                price = float(price) * exchangeRate['TRY']['Value'] / 10
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif '₴' in price:
            price = price.replace('₴', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['UAH']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif 'A$' in price:
            price = price.replace('A$', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['AUD']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
                
        elif 'CDN$' in price:
            price = price.replace('CDN$', '').replace(',', '.')
            try:
                price = float(price) * exchangeRate['CAD']['Value']
            except ValueError:
                fixedPrices.append(price)
            else:
                fixedPrices.append(price)
    
        else:
            print(price)
            fixedPrices.append(price)
    return fixedPrices
    # dbW = db('main')
    # for i in range(1, 100):
    #     connection = choice(dbW.action('find', 'goodProxies', 'userAgent, proxy|proxy != ""'))
    #     # print (connection)
    #     browser = await connect(userAgent=userAgent, proxy=proxy)
    #     page = (await browser.pages())[0]
    #     # elements = await getItem(page, 'https://steamcommunity.com/market/listings/730/Desert%20Eagle%20%7C%20Urban%20DDPAT%20%28Factory%20New%29')
    #     elements = await getItems(page, 'https://steamcommunity.com/market/search?appid=730', 1)
    #     if elements:
    #         print('ok', i)
    #     else:
    #         dbW.action('delete', 'goodProxies', f'proxy = "{connection[1][0]}" AND userAgent = "{connection[1][1]}"')
    #         print(f'del {connection[1]}\n')
    #     await browser.close()
    # return elements

# print(asyncio.get_event_loop().run_until_complete(main()))

# 'type': elementCatch(By.ID, 'largeiteminfo_item_type', driver).get_attribute('textContent').strip(),
#     'rarity': elementCatch(By.XPATH, "//div[@id='largeiteminfo_item_descriptors']/div[1]", driver).get_attribute('textContent').replace('Exterior: ', '').strip(),
#     'description': ('').join([el.get_attribute('textContent') for el in driver.find_elements(by=By.XPATH, value="//div[@id='largeiteminfo_item_descriptors']/div")]).replace('\n\n', ' ').replace('\n', ' ').replace('\xa0', '. ').strip(),
#     'img': elementCatch(By.XPATH, "//div[@class='market_listing_largeimage']/img", driver).get_attribute('src').strip(),
#     'buyRequestsTotal': int(elementCatch(By.XPATH, "//div[@id='market_commodity_buyrequests']/span[1]", driver).get_attribute('textContent').replace(',', '').strip()),
#     'buyRequests': int(elementCatch(By.XPATH, "//div[@id='market_commodity_buyreqeusts_table']/table/tbody/tr[2]/td[2]", driver).get_attribute('textContent').strip()),
#     'buyPrice': float(elementCatch(By.XPATH, "//div[@id='market_commodity_buyrequests']/span[2]", driver).get_attribute('textContent').replace('$','').replace(',', '').strip()),
#     'sellTotal': int(elementCatch(By.ID, 'searchResults_total', driver).get_attribute('textContent').replace('\xa0', '').strip()),
#     'sellPrices': priceGeneralForm([el.get_attribute('textContent').replace('\n', '').replace('\t', '') for el in driver.find_elements(by=By.XPATH, value="//div[@id='searchResultsRows']/div/div/div[@class='market_listing_right_cell market_listing_their_price']/span[@class='market_table_value']/span[@class='market_listing_price market_listing_price_with_fee'][1]")]),
# priceTrendShow('https://steamcommunity.com/market/listings/730/%E2%98%85%20Broken%20Fang%20Gloves%20%7C%20Yellow-banded%20%28Battle-Scarred%29', 100, 24)
# history = getPriceHistory('https://steamcommunity.com/market/listings/730/%E2%98%85%20Broken%20Fang%20Gloves%20%7C%20Yellow-banded%20%28Battle-Scarred%29')
# print(history)
# print(priceTrendShow([el[1] for el in history], [el[0].strftime('%d.%m.%y') for el in history], 100, 24*7))