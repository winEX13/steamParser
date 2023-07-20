from seleniumwire import webdriver
# from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from urllib.parse import quote
from time import sleep
from datetime import datetime, timedelta
import requests
import json
import re
import holtWinters
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import pandas as pd

exchangeRate = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()['Valute']

def elementCatch(by, byEl: str, driver,  sleep: int=10):
    try:
        return WebDriverWait(driver, sleep).until(
            EC.presence_of_element_located((by, byEl))
        )
    except:
        pass

def test(url):
    driver = webdriver.Chrome()
    driver.get(url)
    while True:
        pass

def getPriceHistory(url: str, reverse: bool=False):
    try:
        return sorted([(datetime.strptime(re.sub(r': .+', '', time), '%b %d %Y %H'), float(price), int(quantity)) for time, price, quantity in json.loads(re.search(r'var line1=(.+);', requests.get(url).text).group(1))], key=lambda x: x[0], reverse=reverse)
    except:
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
    
def connect():
    options = Options()
    # options.add_argument('--headless')
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en, en_US'})
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(500, 500)
    return driver
    
def get(url: str, driver):
    sleep(40)
    driver.get(url)
    elementCatch(By.TAG_NAME, f'html', driver)
    return {
    'name': elementCatch(By.ID, 'largeiteminfo_item_name', driver).get_attribute('textContent').strip(),
    'type': elementCatch(By.ID, 'largeiteminfo_item_type', driver).get_attribute('textContent').strip(),
    'rarity': elementCatch(By.XPATH, "//div[@id='largeiteminfo_item_descriptors']/div[1]", driver).get_attribute('textContent').replace('Exterior: ', '').strip(),
    'description': ('').join([el.get_attribute('textContent') for el in driver.find_elements(by=By.XPATH, value="//div[@id='largeiteminfo_item_descriptors']/div")]).replace('\n\n', ' ').replace('\n', ' ').replace('\xa0', '. ').strip(),
    'img': elementCatch(By.XPATH, "//div[@class='market_listing_largeimage']/img", driver).get_attribute('src').strip(),
    'buyRequestsTotal': int(elementCatch(By.XPATH, "//div[@id='market_commodity_buyrequests']/span[1]", driver).get_attribute('textContent').replace(',', '').strip()),
    'buyRequests': int(elementCatch(By.XPATH, "//div[@id='market_commodity_buyreqeusts_table']/table/tbody/tr[2]/td[2]", driver).get_attribute('textContent').strip()),
    'buyPrice': float(elementCatch(By.XPATH, "//div[@id='market_commodity_buyrequests']/span[2]", driver).get_attribute('textContent').replace('$','').replace(',', '').strip()),
    'sellTotal': int(elementCatch(By.ID, 'searchResults_total', driver).get_attribute('textContent').replace('\xa0', '').strip()),
    'sellPrices': priceGeneralForm([el.get_attribute('textContent').replace('\n', '').replace('\t', '') for el in driver.find_elements(by=By.XPATH, value="//div[@id='searchResultsRows']/div/div/div[@class='market_listing_right_cell market_listing_their_price']/span[@class='market_table_value']/span[@class='market_listing_price market_listing_price_with_fee'][1]")]),
    # 'sellPrice': elementCatch(By.XPATH, "//div[@id='searchResultsRows']/div/div/div[@class='market_listing_right_cell market_listing_their_price']/span[@class='market_table_value']/span[@class='market_listing_price market_listing_price_with_fee'][1]", driver).get_attribute('textContent').replace(',', '').strip(),
    'date': datetime.now().strftime('%d.%m.%y'),
    'time': datetime.now().strftime('%H:%M:%S')
    }

def getImportant(url: str, driver):
    sleep(10)
    driver.get(url)
    elementCatch(By.TAG_NAME, f'html', driver)
    return {
    'buyRequestsTotal': int(elementCatch(By.XPATH, "//div[@id='market_commodity_buyrequests']/span[1]", driver).get_attribute('textContent').replace(',', '').strip()),
    'buyRequests': int(elementCatch(By.XPATH, "//div[@id='market_commodity_buyreqeusts_table']/table/tbody/tr[2]/td[2]", driver).get_attribute('textContent').strip()),
    'buyPrice': float(elementCatch(By.XPATH, "//div[@id='market_commodity_buyrequests']/span[2]", driver).get_attribute('textContent').replace('$','').replace(',', '').strip()),
    'sellTotal': int(elementCatch(By.ID, 'searchResults_total', driver).get_attribute('textContent').replace('\xa0', '').strip()),
    'sellPrices': priceGeneralForm([el.get_attribute('textContent').replace('\n', '').replace('\t', '') for el in driver.find_elements(by=By.XPATH, value="//div[@id='searchResultsRows']/div/div/div[@class='market_listing_right_cell market_listing_their_price']/span[@class='market_table_value']/span[@class='market_listing_price market_listing_price_with_fee'][1]")]),
    'date': datetime.now().strftime('%d.%m.%y'),
    'time': datetime.now().strftime('%H:%M:%S')
    }

def getMany(url: str, driver, mode: str='popular_desc', limit: int=10):
    driver.get(url)
    sleep(10)
    # elementCatch(By.TAG_NAME, f'html', driver)

    answer = []
    # for page in range(1, max([int(el.get_attribute('textContent').strip()) for el in driver.find_elements(by=By.XPATH, value="//div[@id='searchResults_controls']/span/span")]))[:limit]:
    page = 1
    counter = 0
    status = True
    total = int(elementCatch(By.ID, 'searchResults_total', driver).get_attribute('textContent').replace('\xa0', '').strip())
    while len(answer) < limit and page < total and status:
        urlPage = f'{url}#p{page}_{mode}'
        driver.get(urlPage)
        sleep(5)
        elementCatch(By.TAG_NAME, f'html', driver)
        for resultId in range(10):
            while True:
                try:
                    nameEl = elementCatch(By.ID, f'result_{resultId}_name', driver)
                    name = nameEl.get_attribute('textContent').strip()
                    if name not in [d['name'] for d in answer] and len(answer) < limit:
                        start = int(elementCatch(By.ID, 'searchResults_start', driver).get_attribute('textContent').replace('\xa0', '').strip())
                        end = int(elementCatch(By.ID, 'searchResults_end', driver).get_attribute('textContent').replace('\xa0', '').strip())
                        total = int(elementCatch(By.ID, 'searchResults_total', driver).get_attribute('textContent').replace('\xa0', '').strip())
                        print(f'[{start + resultId}/{total}]({limit})-> {name}', end='')
                        answer.append(
                            {
                            'name': name,
                            'tag': elementCatch(By.ID, f'result_{resultId}', driver).get_attribute('data-hash-name').strip(),
                            'url': elementCatch(By.ID, f'resultlink_{resultId}', driver).get_attribute('href').strip(),
                            'img': elementCatch(By.ID, f'result_{resultId}_image', driver).get_attribute('srcset').strip(),
                            'rarityColor': nameEl.get_attribute('style')[11:-2],
                            'quantity': int(elementCatch(By.XPATH, f"//div[@id='searchResultsRows']/a[@id='resultlink_{resultId}']/div/div/div/span[@class='market_table_value']/span", driver).get_attribute('textContent').replace(',', '')),
                            'price': float(elementCatch(By.XPATH, f"//div[@id='searchResultsRows']/a[@id='resultlink_{resultId}']/div/div/div/span[@class='market_table_value normal_price']/span[@class='normal_price']", driver).get_attribute('textContent').replace('$','').replace(' USD', '').replace(',', '')),
                            'date': datetime.now().strftime('%d.%m.%y'),
                            'time': datetime.now().strftime('%H:%M:%S')
                            }
                        )
                    else:
                        print(f'-![{counter}] {name}', end='')
                        if counter > 1000:
                            break
                        counter += 1
                except Exception as e:
                    print(f'-![{counter}] {e}')
                    if counter > 1000:
                        driver.refresh()
                        try:
                            elementCatch(By.ID, f'message', driver)
                        except:
                            break
                            # counter = 0
                        else:
                            status = False
                            return(answer)
                    counter += 1
                else:
                    print(' <-')
                    break
        page += 1
    return(answer)

    # print(driver.find_element(by=By.XPATH, value="//div[@id='searchResultsRows']/a[@id='resultlink_0']/div/div/div/span[@class='market_table_value']/span").get_attribute('textContent'))
    # print([el for el in driver.find_elements(by=By.XPATH, value="//div[@id='searchResultsRows']")])
    # print([float(el.get_attribute('textContent').replace('\n', '').replace('\t', '').replace(' pуб.', '').replace(',', '.')) for el in driver.find_elements(by=By.XPATH, value="//div[@id='searchResultsRows']/div/div/div/span/span[@class='market_listing_price market_listing_price_with_fee']")])
    # print(('').join([el.get_attribute('textContent') for el in driver.find_elements(by=By.XPATH, value="//div[@id='searchResultsRows']/div/div/div/span[@class='market_listing_price market_listing_price_with_fee']")]).replace('\t', '').split('\n'))
    # print([el.get_attribute('textContent') for el in driver.find_elements(by=By.XPATH, value="//div[@id='searchResultsRows']/div/div/div/span/span[@class='market_listing_price market_listing_price_with_fee']")])
    # while True:
    #     pass

# def search(text: str):
#     # options = Options()
#     # options.add_argument('--headless')
#     # driver = webdriver.Chrome(options=options)
#     driver = webdriver.Chrome()
#     driver.set_window_size(500, 500)
#     driver.get('https://www.centrmag.ru/')
#     inputEl = elementCatch('searchMobHeader', driver)
#     inputEl.clear()
#     inputEl.send_keys(text)
#     elementCatch('button-addon3Mob', driver).click()
#     Select(elementCatch('kol_tov', driver)).select_by_value('100')
#     imgs = [el.get_attribute('data-original') for el in driver.find_elements(by=By.XPATH, value="//div[@id='tovars']/div/div/p/a/img")]
#     names = [el.get_attribute('textContent') for el in driver.find_elements(by=By.XPATH, value="//div[@id='tovars']/div/div/a/h2")]
#     prices = [el.get_attribute('textContent') for el in driver.find_elements(by=By.XPATH, value="//div[@id='tovars']/div/div/div/h4")]
#     links = [el.get_attribute('href') for el in driver.find_elements(by=By.XPATH, value="//div[@id='tovars']/div/div/a")]

#     if len(imgs) == len(names) == len(links):
#         return [{'name': name, 'price': price, 'link': link, 'img': img} for name, price, link, img in zip(names, prices, links, imgs)]

# print(search('бумага'))
# while True:
# url = 'https://steamcommunity.com/market/search?appid=730'
# url = 'https://steamcommunity.com/market/search?q=&category_730_ItemSet%5B%5D=any&category_730_ProPlayer%5B%5D=any&category_730_StickerCapsule%5B%5D=any&category_730_TournamentTeam%5B%5D=any&category_730_Weapon%5B%5D=any&category_730_Quality%5B%5D=tag_normal&category_730_Quality%5B%5D=tag_strange&category_730_Rarity%5B%5D=tag_Rarity_Rare_Weapon&category_730_Rarity%5B%5D=tag_Rarity_Uncommon_Weapon&category_730_Rarity%5B%5D=tag_Rarity_Mythical_Weapon&category_730_Rarity%5B%5D=tag_Rarity_Legendary_Weapon&category_730_Rarity%5B%5D=tag_Rarity_Ancient_Weapon&category_730_Rarity%5B%5D=tag_Rarity_Common&category_730_Rarity%5B%5D=tag_Rarity_Ancient&category_730_Rarity%5B%5D=tag_Rarity_Rare_Character&category_730_Rarity%5B%5D=tag_Rarity_Mythical_Character&category_730_Rarity%5B%5D=tag_Rarity_Legendary_Character&category_730_Rarity%5B%5D=tag_Rarity_Rare&category_730_Rarity%5B%5D=tag_Rarity_Ancient_Character&category_730_Rarity%5B%5D=tag_Rarity_Mythical&category_730_Rarity%5B%5D=tag_Rarity_Legendary&category_730_Rarity%5B%5D=tag_Rarity_Contraband&category_730_Type%5B%5D=tag_CSGO_Type_Pistol&category_730_Type%5B%5D=tag_CSGO_Type_SMG&category_730_Type%5B%5D=tag_CSGO_Type_Rifle&category_730_Type%5B%5D=tag_CSGO_Type_Shotgun&category_730_Type%5B%5D=tag_CSGO_Type_SniperRifle&category_730_Type%5B%5D=tag_CSGO_Type_Machinegun&appid=730'
# print(search(url))
# history = getPriceHistory('https://steamcommunity.com/market/listings/730/%E2%98%85%20Broken%20Fang%20Gloves%20%7C%20Yellow-banded%20%28Battle-Scarred%29')
# rub = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()['Valute']['USD']['Value']
# print([round(el[1] * rub) for el in history])
# exit()
# priceTrend([el[1] for el in history], 24*7, 1)
# print([el[1] for el in history], [el[0].strftime('%d.%m.%y') for el in history])
# print(priceTrendShow([el[1] for el in history], [el[0].strftime('%d.%m.%y') for el in history], 100, 24))
# url = 'https://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20SCAR-20%20%7C%20Blueprint%20%28Factory%20New%29'
# print(priceTrendShow(url, 6, 7))
# print(sorted(list(exchangeRate.keys())))
# print(exchangeRate['JPY']['Value'])
# print(exchangeRate['THB']['Value'])
# print(get(url)['sellPrices'])
# print(test('https://steamcommunity.com/market/listings/730/Desert%20Eagle%20%7C%20Urban%20DDPAT%20%28Factory%20New%29'))