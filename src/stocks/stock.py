from stocks.connectdb import Database
import yfinance as yf

import concurrent.futures
import time
from datetime import datetime

import configparser
import pathlib

# settings
config = configparser.ConfigParser()
file = pathlib.Path(__file__).parent / "settings.ini"
config.read(file)

# DB connection
HOST = config.get("StockDatabase", "Host")
DATABASE = config.get("StockDatabase", "Database")
DB_USER = config.get("StockDatabase", "User")
DB_USER_PASSWORD = config.get("StockDatabase", "Password")

# delays
UPDATE_STOCK_DELAY_MIN = config.get("UpdateDelays", "StockMin")
UPDATE_STOCK_DELAY_MAX = config.get("UpdateDelays", "StockMax")
UPDATE_ETF_DELAY_MIN = config.get("UpdateDelays", "ETFMin")
UPDATE_ETF_DELAY_MAX = config.get("UpdateDelays", "ETFMax")

# alarms
GAP_THRESHOLD = int(config.get("Alarms", "GapThreshold"))
EMAIL = config.get("Alarms", "EMail")
EMAIL_MASK = config.get("Alarms", "EMailMask")
ALARM_TYPE_GAP_UP = 1
ALARM_TYPE_GAP_DOWN = 2
ALARM_TYPE_BUY = 3
ALARM_TYPE_SELL = 4

database = Database(HOST, DATABASE, DB_USER, DB_USER_PASSWORD)


class Stock:
    def __init__(self, code="") -> None:
        self.code = code
        self.name = ""
        self.currency = ""
        self.exchange = ""
        self.last_price = 0.01
        self.timestamp = None
        self.active = True
        self.nb = 0
        self.sell_price = 0.0
        self.buy_price = 0.0
        self.id = 0
        self.is_etf = False
        self.link = ""
        self.trend_percent = 0

    @property
    def total_price(self):
        return self.last_price * self.nb

    @property
    def buy_price_gap(self):
        if not self.buy_price:
            return -.999
        if self.last_price > 0:
            return self.buy_price / self.last_price - 1

    @property
    def buy_price_gap_percent(self):
        if not self.buy_price:
            return -100
        if self.last_price > 0:
            return (self.buy_price / self.last_price - 1) * 100

    @property
    def sell_price_gap(self):
        if not self.sell_price:
            return .999
        if self.last_price > 0:
            return self.sell_price / self.last_price - 1

    @property
    def sell_price_gap_percent(self):
        if not self.sell_price:
            return 100
        if self.last_price > 0:
            return (self.sell_price / self.last_price - 1) * 100

    def __str__(self) -> str:
        return f"""{self.name:<20.20s} | {self.buy_price or 0:>7.2f} ({abs(self.buy_price_gap * 100):>4.1f}%) | {self.last_price:>10.2f} | {self.sell_price or 0:>7.2f} ({abs(self.sell_price_gap * 100):>4.1f}%) | {self.nb:>4} | {self.total_price:>7.2f}"""

    def load(self, data=None, online=True):
        tic = time.perf_counter()
        if data is None:
            cursor = database.conn.cursor()
            cursor.execute(f"""
                select code, name, currency, exchange, last_price, timestamp, active, 
                    nb, sell_price, buy_price, id, etf, link 
                from stocks where code='{self.code}' and active=true
                """)
            s = cursor.fetchone()
            cursor.close()
        else:
            s = data

        if s is not None:
            self.code = s[0]
            self.name = s[1]
            self.currency = s[2]
            self.exchange = s[3]
            self.last_price = s[4]
            self.timestamp = s[5]
            self.active = s[6]
            self.nb = s[7]
            self.sell_price = s[8]
            self.buy_price = s[9]
            self.id = s[10]
            self.is_etf = s[11]
            self.link = s[12]

        if online:
            try:
                infos = yf.Ticker(self.code)
                self.currency = infos.fast_info.currency
                self.exchange = infos.fast_info.exchange
                self.last_price = infos.fast_info.last_price
                self.timestamp = datetime.now()
                self.trend_percent = (infos.fast_info.last_price / infos.fast_info.previous_close - 1) * 100
            except (NameError, KeyError):
                print(f"Error : {self.name} online load failed")

        toc = time.perf_counter()
        print(f"{self.name} load time: {toc - tic:0.4f} seconds")

    def store(self):
        if len(self.code) < 2:
            return

        query = f"select count(*) from stocks where id={self.id}"
        cursor = database.conn.cursor()
        cursor.execute(query)
        if cursor.fetchone()[0] > 0:
            cursor.execute(f"""
                update stocks
                set 
                    code = '{self.code}',
                    name = '{self.name}',
                    currency = '{self.currency}',
                    exchange = '{self.exchange}',
                    last_price = {self.last_price},
                    timestamp = '{self.timestamp}',
                    active = {self.active},
                    nb = {self.nb},
                    sell_price = {self.sell_price or "Null"},
                    buy_price = {self.buy_price or "Null"},
                    etf = {self.is_etf},
                    link = '{self.link}'
                where id={self.id}""")
        else:
            cursor.execute(f"""
                insert into stocks (code, name, currency, exchange, last_price, timestamp, 
                    active, nb, sell_price, buy_price, etf, link)
                VALUES ('{self.code}', '{self.name}', '{self.currency}', '{self.exchange}', {self.last_price},
                    now(), {self.active}, {self.nb}, {self.sell_price or "Null"}, {self.buy_price or "Null"},
                    {self.is_etf}, '{self.link}')
            """)
        database.conn.commit()
        cursor.close()

    def update(self):
        self.load()
        self.store()
        self.set_alarm()

    def set_alarm(self):
        query = insert_query = ""
        cursor = database.conn.cursor()
        alarm_type = []

        # gap alarm up
        if self.trend_percent > GAP_THRESHOLD:
            query = f"""select count(id) from alerts a 
                where a.stock_id = {self.id} and alarm_type = {ALARM_TYPE_GAP_UP}
                and (acknowledgement = false or DATE(a.acknowledgement_timestamp) = CURRENT_DATE) """
            cursor.execute(query)
            if cursor.fetchone()[0] == 0:
                alarm_type.append(ALARM_TYPE_GAP_UP)
        # gap alarm up
        elif self.trend_percent < - GAP_THRESHOLD:
            query = f"""select count(id) from alerts a 
                where a.stock_id = {self.id} and alarm_type = {ALARM_TYPE_GAP_DOWN}
                and (acknowledgement = false or DATE(a.acknowledgement_timestamp) = CURRENT_DATE) """
            cursor.execute(query)
            if cursor.fetchone()[0] == 0:
                alarm_type.append(ALARM_TYPE_GAP_DOWN)
        # buy alarm
        if self.buy_price_gap > 0:
            query = f"""select count(id) from alerts a 
                where a.stock_id = {self.id} and alarm_type = {ALARM_TYPE_BUY}
                and (acknowledgement = false or DATE(a.acknowledgement_timestamp) = CURRENT_DATE) """
            cursor.execute(query)
            if cursor.fetchone()[0] == 0:
                alarm_type.append(ALARM_TYPE_BUY)
        # sell alarm
        elif self.sell_price_gap < 0:
            query = f"""select count(id) from alerts a 
                where a.stock_id = {self.id} and alarm_type = {ALARM_TYPE_SELL}
                and (acknowledgement = false or DATE(a.acknowledgement_timestamp) = CURRENT_DATE) """
            cursor.execute(query)
            if cursor.fetchone()[0] == 0:
                alarm_type.append(ALARM_TYPE_SELL)

        if len(alarm_type) > 0:
            for at in alarm_type:
                query = f"""insert into alerts (alarm_type, stock_id) 
                VALUES ( {alarm_type.pop()}, {self.id})"""
                cursor.execute(query)
            database.conn.commit()

        cursor.close()


def load_stocks(online=True, limit=None) -> list:
    stocks = []
    if not limit:
        query = """
                select code, name, currency, exchange, last_price, timestamp, active, nb, sell_price, buy_price, 
                    id, etf, link, least(abs(buy_price / last_price -1), abs(sell_price / last_price - 1)) as gap 
                from stocks where active=true and last_price > 0
                union
                select code, name, currency, exchange, last_price, timestamp, active, nb, sell_price, buy_price, 
                    id, etf, link, 1 as gap
                from stocks where active=true and last_price is null or last_price = 0
                order by gap asc
            """
    else:
        query = f"""
                select code, name, currency, exchange, last_price, timestamp, active, nb, sell_price, buy_price, 
                    id, etf, link, least(abs(buy_price / last_price -1), 
                    abs(sell_price / last_price - 1)) as gap, random() as rank
                from stocks where active=true and last_price > 0
                union
                select code, name, currency, exchange, last_price, timestamp, active, nb, sell_price, buy_price, 
                    id, etf, link,1 as gap, random() as rank
                from stocks where active=true and last_price is null or last_price = 0
                order by rank asc limit {limit}
            """

    cursor = database.conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()

    tic = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for row in rows:
            s = Stock()
            stocks.append(s)
            futures.append(
                executor.submit(s.load, row, online)
            )

    if online:
        for s in stocks:
            s.store()

    toc = time.perf_counter()
    print(f"Total time: {toc - tic:0.4f} seconds")

    return stocks


if __name__ == "__main__":
    #    init()
    # stock = Stock("FR0000051732")
    # stock.load()
    # print(stock)
    # stock.store()
    #
    # stocks = load_stocks()
    # print(f"""{"Name":<20.20s} | buy_price       | Last_price | sell_price      | nb   | total_price""")
    # print("-" * 100)
    # for s in stocks:
    #     if s.buy_price_gap and s.buy_price_gap > -0.05:
    #         print(colored(s, "red"))
    #     elif s.sell_price_gap and s.sell_price_gap < 0.05:
    #         print(colored(s, "green"))
    #     else:
    #         print(s)

    s = Stock('FR0014003U94')
    s.load(online=False)
    s.trend_percent = 70
    s.buy_price = s.last_price + 1
    s.sell_price = s.last_price - 1
    s.set_alarm()