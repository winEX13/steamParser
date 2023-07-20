from database import db
import market as mr
import random
import requests
import base64
import proxy as xy
from sqlite3 import IntegrityError
from random import choice
from multiprocessing import Process
from tqdm import tqdm
import asyncio
import timeit

url = 'https://steamcommunity.com/market/search?q=&category_730_ItemSet%5B%5D=any&category_730_ProPlayer%5B%5D=any&category_730_StickerCapsule%5B%5D=any&category_730_TournamentTeam%5B%5D=any&category_730_Weapon%5B%5D=any&category_730_Exterior%5B%5D=tag_WearCategory0&category_730_Quality%5B%5D=tag_normal&category_730_Quality%5B%5D=tag_strange&category_730_Rarity%5B%5D=tag_Rarity_Rare_Weapon&category_730_Rarity%5B%5D=tag_Rarity_Uncommon_Weapon&category_730_Rarity%5B%5D=tag_Rarity_Mythical_Weapon&category_730_Type%5B%5D=tag_CSGO_Type_Pistol&category_730_Type%5B%5D=tag_CSGO_Type_SMG&category_730_Type%5B%5D=tag_CSGO_Type_Rifle&category_730_Type%5B%5D=tag_CSGO_Type_Shotgun&category_730_Type%5B%5D=tag_CSGO_Type_SniperRifle&category_730_Type%5B%5D=tag_CSGO_Type_Machinegun&appid=730'

async def market(url: str, page: int=1, mode: str='popular_desc'):
    global db
    dbW = db('main')
    rub = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()['Valute']['USD']['Value']
    userAgent, proxy = getConnection()
    for item in await mr.get(userAgent=userAgent, proxy=proxy, request='items', url=url, pageIdx=page, mode=mode):
        # print(item)
        name = item['name']
        # tag = item['tag']
        random.seed(name)
        url = item['url']
        img = item['img']
        try:
            img = await requests.get(img[img.find('1x,')+4:-3], proxies={'https': proxy}, headers={'User-Agent': userAgent}).content
        except:
            pass
        quantity = item['quantity']
        price = item['price']
        date = item['date']
        time = item['time']
        itemId = random.randint(0, 999999)
        find = dbW.action('find', 'market', f'id|id = "{itemId}"')
        # print(tag, tagId, find)
        # lastId = db.action('find', 'realTime', f'id|id != ""')
        # print(lastId, type(lastId))
        # lastId = lastId[-1] + 1 if len(lastId) != 0 else 0
        # lastId = lastId[-1] + 1 if isinstance(lastId, list) and len(lastId) != 0 else 1 if isinstance(lastId, int) else 0
        if not find:
            dbW.action('insert', 'market', 
                [
                    itemId,
                    name,
                    time,
                    date,
                    quantity,
                    price * rub,
                    price,
                    url,
                    None
                ]
            )
            dbW.action('update item', 'market', {'img': img, 'WHERE': f'id = "{itemId}"'})
        else:
            dbW.action('update', 'market', 
            f'''
            name = "{name}",
            url = "{url}",
            quantity = "{quantity}",
            priceRUB = "{price * rub}",
            priceUSD = "{price}",
            date = "{date}",
            time = "{time}"
            |sep|
            id = "{itemId}"'''.replace('\n', ''))
            dbW.action('update item', 'market', {'img': img, 'WHERE': f'id = "{itemId}"'})

def item(itemId: int, driver):
    global db
    dbW = db('main')
    rub = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()['Valute']['USD']['Value']
    url = dbW.action('find', 'market', f'url|id = "{itemId}"')
    item = mr.get(url, driver)
    # print(item)
    name = item['name']
    type = item['type']
    rarity = item['rarity']
    description = item['description'].replace(f'Exterior: {rarity}. ', '')
    img = requests.get(item['img']).content
    # print(img)
    buyRequestsTotal = item['buyRequestsTotal']
    buyRequests = item['buyRequests']
    buyPrice = item['buyPrice'] * rub
    sellTotal = item['sellTotal']
    sellPrices = str(item['sellPrices'])
    # € zł --€
    date = item['date']
    time = item['time']
    capacity = mr.capacityTrend(url)
    if capacity:
        scoreWeek, scorePreviousWeek, scoreMonth, scoreTotal = [_ * buyRequestsTotal for _ in capacity]
    else:
        scoreWeek, scorePreviousWeek, scoreMonth, scoreTotal = None, None, None, None
    scoreStart = mr.priceTrendStart(url)
    find = dbW.action('find', 'items', f'id|id = "{itemId}"')
    if not find:
            dbW.action('insert', 'items', 
                [
                    itemId,
                    name,
                    scoreWeek,
                    scorePreviousWeek,
                    scoreMonth,
                    scoreTotal,
                    scoreStart,
                    sellPrices,
                    buyPrice,
                    sellTotal,
                    buyRequests,
                    time,
                    date,
                    type,
                    rarity,
                    description,
                    url,
                    None
                ]
            )
            dbW.action('update item', 'items', {'img': img, 'WHERE': f'id = "{itemId}"'})
    else:
        dbW.action('update', 'items', 
        f'''
        name = "{name}",
        scoreWeek = "{scoreWeek}",
        scorePreviousWeek = "{scorePreviousWeek}",
        scoreMonth = "{scoreMonth}",
        scoreTotal = "{scoreTotal}",
        scoreStart = "{scoreStart}",
        sellPrices = "{sellPrices}",
        buyPrice = "{buyPrice}",
        sellTotal = "{sellTotal}",
        buyRequests = "{buyRequests}",
        time = "{time}",
        date = "{date}",
        type = "{type}",
        rarity = "{rarity}",
        description = "{description}",
        url = "{url}"
        |sep|
        id = "{itemId}"'''.replace('\n', ''))
        dbW.action('update item', 'items', {'img': img, 'WHERE': f'id = "{itemId}"'})

def setProxies():
    global db
    dbW = db('main')
    proxies = dbW.action('find', 'proxies', 'proxy|proxy != ""')
    for proxy in xy.getProxies():
        if proxy not in proxies:
            try:
                dbW.action('insert', 'proxies', [proxy, ])
                # print(f'add {proxy}')
            except IntegrityError:
                pass
        
# def checkProxies(url: str):
#     global db
#     dbW = db('main')
#     for proxy in dbW.action('find', 'proxies', 'proxy|proxy != ""'):
#         if not xy.checkProxy(url, proxy):
#             dbW.action('delete', 'proxies', f'proxy = "{proxy}"')
            
def checkProxies(url: str):
    global db
    dbW = db('main')
    for proxy in tqdm(dbW.action('find', 'proxies', 'proxy|proxy != ""')):
        if not xy.checkProxy(url, proxy):
            dbW.action('delete', 'proxies', f'proxy = "{proxy}"')
            # print(f'del {proxy}\n')
            
def tryConnection(url: str):
    global db
    dbW = db('main')
    while True:
        connection = xy.checkConnection(url, proxy=choice(dbW.action('find', 'proxies', 'proxy|proxy != ""')))
        if connection[0]:
            dbW.action('insert', 'goodProxies', [*connection[1]])
            print(f'add {connection[1]}\n')
        else:
            dbW.action('delete', 'goodProxies', f'proxy = "{connection[1][0]}" AND userAgent = "{connection[1][1]}"')
            print(f'del {connection[1]}\n')
            
def checkConnection(url: str):
    global db
    dbW = db('main')
    for connectionData in dbW.action('find', 'goodProxies', 'proxy, userAgent|proxy != ""'):
        connection = xy.checkConnection(url, proxy=connectionData[0], userAgent=connectionData[1])
        if not connection[0]:
            dbW.action('delete', 'goodProxies', f'proxy = "{connection[1][0]}" AND userAgent = "{connection[1][1]}"')
            print(f'del {connection[1]}\n')
    
def getConnection():
    return choice(db('main').action('find', 'goodProxies', 'userAgent, proxy|proxy != ""'))

def runInParallel(*fns):
  proc = []
  for fn in fns:
    p = Process(target=fn)
    p.start()
    proc.append(p)
  for p in proc:
    p.join()

def startScraping(url: str, page: int, i: int):
    """ Starts an async process for requesting and scraping Wikipedia pages """
    print(f"Process {i} starting...")
    asyncio.run(market(url, page))
    print(f"Process {i} finished.")

import concurrent.futures
import time
from math import floor
from multiprocessing import cpu_count

def main():
    # tasks = [loop.create_task(market('https://steamcommunity.com/market/search?appid=730', _)) for _ in range(1, 10)]
    # await asyncio.wait(tasks)
    
    NUM_PAGES = 100 # Number of pages to scrape altogether
    NUM_CORES = cpu_count() # Our number of CPU cores (including logical cores)
    print(NUM_CORES)
    PAGES_PER_CORE = floor(NUM_PAGES / NUM_CORES)
    PAGES_FOR_FINAL_CORE = PAGES_PER_CORE + NUM_PAGES % PAGES_PER_CORE # For our final core
    
    futures = []

    with concurrent.futures.ProcessPoolExecutor(NUM_CORES) as executor:
        for i in range(NUM_CORES):
            new_future = executor.submit(
                startScraping, # Function to perform
                # v Arguments v
                url='https://steamcommunity.com/market/search?appid=730',
                page=i + 1,
                i=i
            )
            futures.append(new_future)

        # futures.append(
        #     executor.submit(
        #         startScraping,
        #         url='https://steamcommunity.com/market/search?appid=730', 
        #         page=NUM_CORES,
        #         i=NUM_CORES-1
        #     )
        # )

    concurrent.futures.wait(futures)

# market(url)
# print(db('main').action('find', 'market', f'id|id not in (select id from items)'))
# exit()
# driver = mr.connect()
# [item(_, driver) for _ in db('main').action('find', 'market', f'id|id != ""')]
# for _ in db('main').action('find', 'market', f'id|id not in (select id from items)'):
    # driver = mr.connect()
    # item(_, driver)
# db.action('insert', 'realTime'
# tag = 'AK-47 | Baroque Purple (Factory New)'
# db = db('main')
# print(db.action('find', 'realTime', f'*|name = "AK-47 | Baroque Purple (Factory New)"'))
# print(db.tableColumns('realTime'))
# time = '123'
# id = 347586
# print(db.action(f'update items set time = "{time}" where id = "{id}"'))
url = 'https://steamcommunity.com/market'
# runInParallel(setProxies(), checkProxies(url))#, checkConnection(url), tryConnection(url))
# checkConnection(url)
# setProxies()
# checkProxies(url)

# loop = asyncio.get_event_loop()
if __name__ == '__main__':
    start_time = timeit.default_timer()
    main()

# loop.run_until_complete(main())
    print(timeit.default_timer() - start_time)