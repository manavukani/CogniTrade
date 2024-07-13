from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime
from alpaca_trade_api import REST
from datetime import timedelta

import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
BASE_URL = os.getenv("BASE_URL")

ALPACA_CREDS = {"API_KEY": API_KEY, "API_SECRET": API_SECRET, "PAPER": True}


class MLTrader(Strategy):
    def initialize(self, symbol: str = "SPY", cash_at_risk: float = 0.5):
        self.symbol = symbol
        self.sleeptime = "24H"
        self.last_trade = None
        self.cash_at_risk = cash_at_risk
        self.api = REST(key_id=API_KEY, secret_key=API_SECRET, base_url=BASE_URL)

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity = round(cash * self.cash_at_risk / last_price, 0)
        return cash, last_price, quantity

    def get_dates(self):
        end_date = self.get_datetime()
        start_date = end_date - timedelta(days=3)
        return end_date.strftime("%Y-%m-%d"), start_date.strftime("%Y-%m-%d")

    def get_news(self):
        end_date, start_date = self.get_dates()
        news = self.api.get_news(symbol=self.symbol, start=start_date, end=end_date)
        news = [event.__dict__["_raw"]["headline"] for event in news]
        return news        

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()

        if cash > last_price:
            # testing news
            news = self.get_news()
            print(news)
            
            if self.last_trade == None:
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "buy",
                    type="bracket",
                    take_profit_price=last_price * 1.20,
                    stop_loss_price=last_price * 0.95,
                )
                self.submit_order(order)
                self.last_trade = "buy"


start_date = datetime(2024, 6, 1)
end_date = datetime(2024, 6, 30)

broker = Alpaca(ALPACA_CREDS)
strategy = MLTrader(
    name="mlstrat", broker=broker, parameters={"symbol": "SPY", "cash_at_risk": 0.5}
)

strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol": "SPY", "cash_at_risk": 0.5},
)
