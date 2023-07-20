# import requests
# from bs4 import BeautifulSoup
# import json
# import re



# url = 'https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/' #Ссылка на игру


# r = requests.get(url)
# soup = BeautifulSoup(r.text, 'html.parser') #Берет из html страницы

# price = soup.find('div', class_='discount_final_price').text


# rs = requests.get('https://steamcommunity.com/market/listings/730/Falchion%20Case')

# print(rs.text)

# m = re.search(r'var line1=(.+);', rs.text)
# data_str = m.group(1)

# data = json.loads(data_str)
# print(data)

from steam_community_market import Market, AppID, ESteamCurrency
from steam_community_market.request import request
from time import sleep
from datetime import datetime
from database import db

def getPrices(item: str, data: dict, mode: str = 'USD'):
    marketUSD = Market('USD')
    marketRUS = Market('RUB')
    print(item, data)
    if data:
        if data['success']:
            if mode == 'RUB':
                print(marketRUS.has_invalid_name(item))
                prices = {
                    'lowestPrice': float(marketRUS.get_lowest_price(item, AppID.CSGO).replace(' pуб.', '').replace(',', '.')),
                    'medianPrice': float(marketRUS.get_median_price(item, AppID.CSGO).replace(' pуб.', '').replace(',', '.')),
                }
            elif mode == 'USD':
                prices = {
                    'lowestPrice': marketUSD.price_to_float(data['lowest_price']),
                    'medianPrice': marketUSD.price_to_float(data['median_price']),
                }
            prices['volume'] = float(data['volume'].replace(',', ''))
            prices['difference'] = prices['medianPrice'] - prices['lowestPrice']
            prices['ratio'] = prices['lowestPrice'] / prices['medianPrice'] * 100
            prices['score'] = prices['difference'] * prices['volume']
            prices['date'] = datetime.now().strftime('%d.%m.%y'),
            prices['time'] = datetime.now().strftime('%H:%M:%S')
            return(prices)
        else:
            return None
    else:
        return None

def itemPrice(item: str, skin: str, quality: str, rarity: str = ''):
    marketUSD = Market('USD')
    marketRUS = Market('RUB')
    item = f'{rarity} {item} | {skin} ({quality})'.strip()
    itemData = marketUSD.get_overview(item, AppID.CSGO)
    if itemData:
        if itemData['success']:
            prices = {
                'regionLowestPrice': marketRUS.get_lowest_price(item, AppID.CSGO),
                'regionMedianPrice': marketRUS.get_median_price(item, AppID.CSGO),
                'lowestPrice': marketUSD.price_to_float(itemData['lowest_price']),
                'medianPrice': marketUSD.price_to_float(itemData['median_price']),
            }
            prices['difference'] = prices['lowestPrice'] / prices['medianPrice'] * 100
            prices['score'] = prices['medianPrice'] / prices['lowestPrice'] * float(itemData['volume'])
            return(prices, itemData['volume'])
        else:
            return None
    else:
        return None

def nameBuilder(item: str, skin: str, quality: str = 'Factory New', rarity: str = 'StatTrak™'):
    return f'{rarity} {item} | {skin} ({quality})'.strip()

def itemsPrices(items: list, mode: str = 'RUB'):
    market = Market()
    answer = []
    n = 20
    [items[i * n:(i + 1) * n] for i in range((len(items) + n - 1) // n )]
    for slice in [items[i * n:(i + 1) * n] for i in range((len(items) + n - 1) // n)]:
        itemsData = market.get_overviews(slice, AppID.CSGO)
        answer.extend([{'name': key, 'prices': getPrices(key, value, mode=mode)} for key, value in itemsData.items()])
        # sleep(2)
    return answer
    # if itemData:
    #     if itemData['success']:
    #         prices = {
    #             'regionLowestPrice': marketRUS.get_lowest_price(item, AppID.CSGO),
    #             'regionMedianPrice': marketRUS.get_median_price(item, AppID.CSGO),
    #             'lowestPrice': marketUSD.price_to_float(itemData['lowest_price']),
    #             'medianPrice': marketUSD.price_to_float(itemData['median_price']),
    #         }
    #         prices['difference'] = prices['lowestPrice'] / prices['medianPrice'] * 100
    #         prices['score'] = prices['medianPrice'] / prices['lowestPrice'] * float(itemData['volume'])
    #         return(prices, itemData['volume'])
    #     else:
    #         return None
    # else:
    #     return None

# print(itemPrice('MAC-10', 'Heat', 'Minimal Wear', 'StatTrak™'))
# print(itemsPrices(cases, 'USD'))
# print(market.get_lowest_price("Falchion Case", AppID.CSGO))
# itemData['']
# print(market.get_overview("Falchion Case", AppID.CSGO))
cases = '''Spectrum 2 Case
Chroma 3 Case
Gamma 2 Case
Revolver Case
Horizon Case
CS20 Case
Gamma Case
Spectrum Case
Chroma 2 Case
Glove Case
Shadow Case
Operation Breakout Weapon Case
Falchion Case
Operation Wildfire Case
Operation Phoenix Weapon Case
Operation Broken Fang Case
Chroma Case
Operation Riptide Case
Shattered Web Case
Operation Vanguard Weapon Case
Huntsman Weapon Case
CS:GO Weapon Case 3
eSports 2013 Winter Case
eSports 2014 Summer Case
Winter Offensive Weapon Case
Operation Hydra Case
CS:GO Weapon Case 2
Operation Bravo Case
CS:GO Weapon Case
eSports 2013 Case
X-Ray P250 Package
Recoil Case
Dreams & Nightmares Case
Snakebite Case
Fracture Case
Prisma 2 Case
Prisma Case
Danger Zone Case
Clutch Case'''

prices = '''55,05 pуб.
59,29 pуб.
76,93 pуб.
43,05 pуб.
17,64 pуб.
14,82 pуб.
78,34 pуб.
89,64 pуб.
74,11 pуб.
237,16 pуб.
24,70 pуб.
316,92 pуб.
23,99 pуб.
52,23 pуб.
141,17 pуб.
151,05 pуб.
105,87 pуб.
184,93 pуб.
100,23 pуб.
83,99 pуб.
488,44 pуб.
431,27 pуб.
386,10 pуб.
343,04 pуб.
354,33 pуб.
1 149,12 pуб.
568,20 pуб.
3 215,14 pуб.
4 849,89 pуб.
2 419,65 pуб.
252,69 pуб.
50,11 pуб.
50,11 pуб.
10,58 pуб.
13,41 pуб.
12,70 pуб.
13,41 pуб.
16,23 pуб.
23,99 pуб.'''

# print(len(cases.split('\n')))
l = list(zip(range(39), cases.split('\n'), ('None',)*39, ('None',)*39, prices.split('\n'), ('None',)*39))
# sum(regular_list, [])

db('main').action('insert', 'cases', [item for sublist in l for item in sublist])