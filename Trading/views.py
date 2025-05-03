from __future__ import unicode_literals

import base64
import datetime
import io
import json
import os
import sys
import time
import urllib

import matplotlib
import matplotlib.pyplot as plt
import mpld3
import numpy as np
import pandas as pd
import yfinance as yf
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect, render

matplotlib.pyplot.switch_backend("Agg")

from django.contrib.auth.hashers import check_password, make_password
import mysql.connector
import ta
import yfinance as yf
from pandas_datareader import data as pdr
from datetime import datetime
import pandas as pd
from datetime import datetime


from .nosql_connect import get_record_details, insert_record

HOST = '<RDS_DATABASE_HOST>'
USER = 'admin'
PASSWORD = '<PASSWORD>'
DATABASE = 'SMART'  
PORT = 3306


def SignupPage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")

        password1_hashed = make_password(request.POST.get("password1"))
        # print("HASHED PASS 1:", password1_hashed)
        match_password_status = check_password(request.POST.get("password2"), password1_hashed)
        # print("HASHED PASS 2 Match Status:", match_password_status)

        if match_password_status == False:
            return HttpResponse("Your password and confirmation password are not Same!")
        else:
            status = insert_record(
                {
                    "username": username,
                    "email": email,
                    "password": password1_hashed,
                    "firstname": firstname,
                    "lastname": lastname,
                }
            )
            # print("STATUS:", status)
            if status == False:
                return HttpResponse("Username and Email already exists. Try different username and email!")
            else:
                return redirect("login")

    return render(request, "signup.html")


def LoginPage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        record_details = get_record_details({"username": username})
        # print("STATUS:", record_details)
        if record_details == False:
            return HttpResponse("Username doesn't exist!")
        else:
            fetched_password = record_details["password"]
            match_password_status = check_password(request.POST.get("pass"), fetched_password)
            if match_password_status == True:
                request.session["username"] = record_details["username"]
                request.session["firstname"] = record_details["firstname"]
                request.session["lastname"] = record_details["lastname"]
                return redirect("HomeScreen")
            else:
                return HttpResponse("Username or Password is incorrect!")

    return render(request, "login.html")


def LogoutPage(request):
    request.session.clear()
    return redirect("login")


def create_connection():
    try:
        # Establish the connection
        conn = mysql.connector.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE, port=PORT)
        if conn.is_connected():
            print("Connected to MySQL database")
            # Perform database operations here
        return conn
    except mysql.connector.Error as e:
        print("Error connecting to MySQL database:", e)


def HomeScreen(request):
    if 'username' not in request.session:
        return redirect('login')  # Redirect to login page
    else:
        return render(request, "Menu.html")


def TradingStrategy(request):
    search_param = dict()
    if request.method == "POST":
        search_param1 = request.POST["query"]
        print("Search paramas", search_param1)
    else:
        try:
            search_param1 = json.loads(request.GET.get("search_param", 1).replace("", "/"))
        except:
            print("search_param not found!")

    def date_to_timestamp(date_string):
        from datetime import datetime

        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        timestamp = int(date_obj.timestamp())

        return timestamp

    def load_equities_web(symbol, startdate, enddate):
        yf.pdr_override()
        startdate = datetime(2023, 1, 1)
        enddate = datetime(2024, 3, 1)
        # raw_data = web.DataReader(symbol, 'yahoo', pd.to_datetime(date_from), pd.datetime.now())
        data = pdr.get_data_yahoo(symbol, start=startdate, end=enddate)
        # data = raw_data.stack(dropna=False)['Adj Close'].to_frame().reset_index().rename(columns= {'Symbols':'symbol', 'Date':'date','Adj Close':'value'}).sort_values(by = ['symbol', 'date'])
        return data

    df = load_equities_web(search_param1, "2023-01-01", "2024-03-01")


    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    df["previous_RSI"] = df["RSI"].shift(1)

    # Create RSI Trading Strategy
    def RSI_trading_strategy(df):
        """
        ---------------------------------------------------------------
        |   Output: Function Returns the Profit returns of RSI Strategy |                                                        |
        | --------------------------------------------------------------|
        |   Input: Dataframe with RSI value of the stock                |
        |          neutral: Value of neutrality, no Action Zone         |
        |           window:  rolling period of the RSI                  |
        |                                                               |
        ---------------------------------------------------------------

        """
        # Buy Signal
        overbought = 70
        neutral_buy = 55

        # df["signal_buy"] = np.nan

        # Create Signal for Long Buy by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
        # Trading strategy for Open Buy Signal when Prv RSI < 55 and Current RSI > 55: Handle True Signal
        # This implies that RSI has increased from Yesterday and and is not in Overbought Threshold indicating Trend Reversal
        # Therefore Buy Long can be Executed

        df.loc[(df["RSI"] > neutral_buy) & (df["previous_RSI"] < neutral_buy), "signal_buy"] = df["Close"]

        # Create Signal for Long Buy by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
        # If the Current RSI is dropping from Neutral_Buy then indication of the Trend can go down, hence No Long Position
        # Trading strategy for Close Buy Signal when Prv RSI > 55 and Current RSI < 55: Handle False Signal
        df.loc[(df["RSI"] < neutral_buy) & (df["previous_RSI"] > neutral_buy), "signal_buy"] = 0

        # Create Signal for Long Buy by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
        # Trading strategy for Close Buy Signal when Prv RSI > 70 and Current RSI < 70: Handle Overbought Signal
        df.loc[(df["RSI"] < overbought) & (df["previous_RSI"] > overbought), "signal_buy"] = 0

        # Sell Signal
        oversold = 30
        neutral_sell = 45
        # df["signal_sell"] = np.nan
        # Create Signal for Open Short Signal and Close Short Signal by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
        # Trading strategy for Open Buy Signal when Prv RSI > 45 and Current RSI < 45: Handle the True Signal
        # This implies that RSI has decreased from Yesterday and and is not in yet in Threshold situation but indicating Downward trend line signal
        # Therefore Sell can be Executed
        df.loc[(df["RSI"] < neutral_sell) & (df["previous_RSI"] > neutral_sell), "signal_sell"] = df["Close"]

        # Create Signal for Close Sell by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
        # If the Current RSI is Increasing from the neutral_sell then indication of the Trend can go Up, hence No Sell Position
        # Trading strategy for Close Buy Signal when Prv RSI < 45 and Current RSI > 45: Handle the False Signal
        df.loc[(df["RSI"] > neutral_sell) & (df["previous_RSI"] < neutral_sell), "signal_sell"] = 0

        # Create Signal for Close Sell by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
        # Trading strategy for Close Buy Signal when Prv RSI < 30 and Current RSI > 30: Handle Overbought Signal
        df.loc[(df["RSI"] > overbought) & (df["previous_RSI"] < overbought), "signal_sell"] = 0

        # Compute the Returns
        # df['pct_change'] = df['Close'].pct_change(1)
        # Evaluate the Position
        # df['Position'] = (df['signal_sell'].fillna(method='ffill') + df['signal_buy'].fillna(method='ffill'))
        # Find the Returns
        # df['return'] = (df['Position'].shift(1)) * df['pct_change']

        return df

    df = RSI_trading_strategy(df)
    df["time"] = df.index
    df["time"] = df["time"].dt.date

    class Position:

        def __init__(self, open_datetime, open_price, order_type, Volume, sl, tp):
            self.open_datetime = open_datetime
            self.open_price = open_price
            self.order_type = order_type
            self.Volume = Volume
            self.sl = sl
            self.tp = tp

            self.close_datetime = None
            self.close_price = None
            self.profit = None
            self.status = "Open"

        def close_position(self, close_datetime, close_price):
            self.close_datetime = close_datetime
            self.close_price = close_price
            self.profit = (
                (self.close_price - self.open_price) * self.Volume
                if self.order_type == "buy"
                else (self.open_price - self.close_price) * self.volume
            )  # Logic needs to be based on buy date and sell date
            self.status = "Closed"

        def _asdict(self):
            return {
                "open_datetime": self.open_datetime,
                "open_price": self.open_price,
                "order_type": self.order_type,
                "Volume": self.Volume,
                "sl": self.sl,
                "tp": self.tp,
                "close_datetime": self.close_datetime,
                "close_price": self.close_price,
                "profit": self.profit,
                "status": self.status,
            }

    
    class Strategy:

        def __init__(self, df, starting_balance, Volume):

            self.starting_balance = starting_balance
            self.Volume = Volume
            self.positions = []
            self.data = df

        def get_positions_df(self):
            df = pd.DataFrame([position._asdict() for position in self.positions])
            df["pnl"] = df["profit"].cumsum() + self.starting_balance
            return df

        def add_position(self, position):
            self.positions.append(position)

            return True

        buy_price = []
        sell_price = []

        # def run(self):
        #     for i, data in self.data.iterrows():
        #         if data.crossover == 'bullish cross over':

        #             self.add_position(Position(data.time, data.Close, 'buy', self.Volume, 0, 0))
        #             #buy_price[i] = data.Close
        #         if data.crossover == 'bearish cross over':

        #             #sell_price[i] = data.Close
        #             for position in self.positions:
        #                 if position.status == 'Open':
        #                     position.close_position(data.time, data.Close)

        def run(self):
            for i, data in self.data.iterrows():
                if data.signal_buy > 0:

                    self.add_position(Position(data.time, data.Close, "buy", self.Volume, 0, 0))
                    # buy_price[i] = data.Close
                if data.signal_sell > 0:

                    # sell_price[i] = data.Close
                    for position in self.positions:
                        if position.status == "Open":
                            position.close_position(data.time, data.Close)

            return self.get_positions_df()

    pnl_result = Strategy(df, 10000, 25).run()
    # print(pnl_result)
    pnl_result_filter = pnl_result[pnl_result["status"] != "Open"]

    result_growth = pnl_result_filter["pnl"].values[-1]
    net_growth = ((result_growth / 10000) - 1) * 100
    # print("Investment Growth", net_growth)

    # https://github.com/bennycode/trading-signals
    # https://stackoverflow.com/questions/72110715/how-to-get-alternating-trading-signals

    # def create_connection(db_file):

    # connection = None
    # try:
    #    connection = sqlite3.connect('database.db')  # Works when on db name provided;  #db_file #Used db_path as well:: no table

    #    if connection:
    #        print("Connection Established Successfully!")
    #        print("Connection=", connection)
    # except Error as e:
    #    print(e)

    # return connection

    def select_db_records(connection, search_param1):
        # print("Value of search_param in db_records=", search_param1)
        cursor = connection.cursor()
        # print("Cusror returned", cursor)
        search_ticker1 = search_param1

        # Execute query with parameters

        query_ris_signals = """  WITH CTE_tmp_return
        as
        (
        Select * from
        (
        Select Ticker, Stock_Id, 1000 as StockInvesmentUnits,
        y1_return, y3_return, y5_return, y10_return,
        ROW_NUMBER () OVER (PARTITION BY Ticker ORDER BY Date) AS rownum from stock_returns_summary
        ) tmpa
        Where tmpa.rownum=1
        AND Ticker = %s
        ) 
        Select DP.Ticker, 
            SS.rsi_signal_buy, SS.rsi_signal_sell, SS.rsi_priceAction,
            SS.Date, RT.StockInvesmentUnits,
            CASE WHEN SS.rsi_signal_buy = 1 THEN  ((DP.Close -  DP.Open) * RT.StockInvesmentUnits)
                WHEN SS.rsi_signal_sell = -1 THEN  ((DP.Open -  DP.Close) * RT.StockInvesmentUnits)
                ELSE 'No Loss/No Profit'
            End as Profit_Loss
        from strategy SS
        JOIN daily_price DP on DP.Stock_Id = SS.Stock_Id
        JOIN CTE_tmp_return RT ON RT.Ticker = DP.Ticker
        Order by DP.Date desc limit 30 """

        cursor.execute(query_ris_signals, (search_ticker1,))
        rsi_stats = cursor.fetchall()

        return rsi_stats

    connection = create_connection()

    with connection:
        rsi_stats = select_db_records(connection, search_param1)
    # print("...........Checkpoint RSI Signals values.........")
    # print(rsi_stats)

    connection.close()
    stock_growth = (
        (pnl_result_filter["close_price"].values[-1] - pnl_result_filter["close_price"].values[0])
        / (pnl_result_filter["close_price"].values[0])
        * 100
    )
    stock_growth = round(stock_growth, 2)
    pnl_result_filter = pnl_result_filter.values.tolist()
    # print("Filtered.....result of PnL")
    # print(pnl_result_filter)
    net_growth = round(net_growth, 2)

    # Usee Trndspider
    # https://trendspider.com/developers/examples/
    return render(
        request,
        "Strategy.html",
        {"result1": pnl_result_filter, "result2": net_growth, "result3": rsi_stats, "result4": stock_growth},
    )


def BollingerStrategy(request):
    search_param = dict()
    if request.method == "POST":
        search_param1 = request.POST["query"]
        # print("Search paramas", search_param1)
    else:
        try:
            search_param1 = json.loads(request.GET.get("search_param", 1).replace("", "/"))
        except:
            print("search_param not found!")

    def date_to_timestamp(date_string):
        from datetime import datetime

        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        timestamp = int(date_obj.timestamp())

        return timestamp

    def load_equities_web(symbol, startdate, enddate):
        yf.pdr_override()
        startdate = datetime(2023, 1, 1)
        enddate = datetime(2024, 3, 1)
        # raw_data = web.DataReader(symbol, 'yahoo', pd.to_datetime(date_from), pd.datetime.now())
        data = pdr.get_data_yahoo(symbol, start=startdate, end=enddate)
        # data = raw_data.stack(dropna=False)['Adj Close'].to_frame().reset_index().rename(columns= {'Symbols':'symbol', 'Date':'date','Adj Close':'value'}).sort_values(by = ['symbol', 'date'])
        return data

    df = load_equities_web(search_param1, "2023-01-01", "2024-03-01")

    df["time"] = df.index
    df["time"] = df["time"].dt.date

    class Position:

        def __init__(self, open_datetime, open_price, order_type, Volume, sl, tp):
            self.open_datetime = open_datetime
            self.open_price = open_price
            self.order_type = order_type
            self.Volume = Volume
            self.sl = sl
            self.tp = tp

            self.close_datetime = None
            self.close_price = None
            self.profit = None
            self.status = "Open"

        def close_position(self, close_datetime, close_price):
            self.close_datetime = close_datetime
            self.close_price = close_price
            self.profit = (
                (self.close_price - self.open_price) * self.Volume
                if self.order_type == "buy"
                else (self.open_price - self.close_price) * self.volume
            )  # Logic needs to be based on buy date and sell date
            self.status = "Closed"

        def _asdict(self):
            return {
                "open_datetime": self.open_datetime,
                "open_price": self.open_price,
                "order_type": self.order_type,
                "Volume": self.Volume,
                "sl": self.sl,
                "tp": self.tp,
                "close_datetime": self.close_datetime,
                "close_price": self.close_price,
                "profit": self.profit,
                "status": self.status,
            }

    
    class Strategy:

        def __init__(self, df, starting_balance, Volume):

            self.starting_balance = starting_balance
            self.Volume = Volume
            self.positions = []
            self.data = df

        def get_positions_df(self):
            df = pd.DataFrame([position._asdict() for position in self.positions])
            df["pnl"] = df["profit"].cumsum() + self.starting_balance
            return df

        def add_position(self, position):
            self.positions.append(position)

            return True

        buy_price = []
        sell_price = []

        # def run(self):
        #     for i, data in self.data.iterrows():
        #         if data.crossover == 'bullish cross over':

        #             self.add_position(Position(data.time, data.Close, 'buy', self.Volume, 0, 0))
        #             #buy_price[i] = data.Close
        #         if data.crossover == 'bearish cross over':

        #             #sell_price[i] = data.Close
        #             for position in self.positions:
        #                 if position.status == 'Open':
        #                     position.close_position(data.time, data.Close)

        def run(self):
            for i, data in self.data.iterrows():
                if data.signal_buy > 0:

                    self.add_position(Position(data.time, data.Close, "buy", self.Volume, 0, 0))
                    # buy_price[i] = data.Close
                if data.signal_sell > 0:

                    # sell_price[i] = data.Close
                    for position in self.positions:
                        if position.status == "Open":
                            position.close_position(data.time, data.Close)

            return self.get_positions_df()

    # pnl_result = Strategy(df, 10000, 25).run()
    # print(pnl_result)
    # pnl_result_filter = pnl_result[pnl_result['status'] !='Open']

    # result_growth = pnl_result_filter['pnl'].values[-1]
    # net_growth = ((result_growth/10000)-1)* 100
    # print("Investment Growth", net_growth)

    # https://github.com/bennycode/trading-signals
    # https://stackoverflow.com/questions/72110715/how-to-get-alternating-trading-signals

    # def create_connection(db_file):

    # connection = None
    # try:
    #    connection = sqlite3.connect('database.db')  # Works when on db name provided;  #db_file #Used db_path as well:: no table

    #    if connection:
    #        print("Connection Established Successfully!")
    #        print("Connection=", connection)
    # except Error as e:
    #    print(e)

    # return connection

    def select_db_records(connection, search_param1):

        # print("Value of search_param in db_records=", search_param1)
        cursor = connection.cursor()
        # print("Cusror returned", cursor)
        search_ticker1 = search_param1

        # Execute query with parameters

        query_bollinger_signals = """  WITH CTE_tmp_return
        as
        (
        Select * from
        (
        Select Ticker, Stock_Id, 1000 as StockInvesmentUnits,
        y1_return, y3_return, y5_return, y10_return,
        ROW_NUMBER () OVER (PARTITION BY Ticker ORDER BY Date) AS rownum from stock_returns_summary
        ) tmpa
        Where tmpa.rownum=1
        AND Ticker = %s
        ) 
        Select DP.Ticker, 
            SS.bollinger_buy_signal, SS.bollinger_sell_signal, SS.bollinger_priceAction,
            SS.Date, RT.StockInvesmentUnits,
            CASE WHEN SS.bollinger_buy_signal = 1 THEN  ((DP.Close -  DP.Open) * RT.StockInvesmentUnits)
                WHEN SS.bollinger_sell_signal = -1 THEN  ((DP.Open -  DP.Close) * RT.StockInvesmentUnits)
                ELSE 'No Loss/No Profit'
            End as Profit_Loss
        from strategy SS
        JOIN daily_price DP on DP.Stock_Id = SS.Stock_Id
        JOIN CTE_tmp_return RT ON RT.Ticker = DP.Ticker
        Order by DP.Date desc limit 30 """

        cursor.execute(query_bollinger_signals, (search_ticker1,))
        bollinger_stats = cursor.fetchall()

        return bollinger_stats

    connection = create_connection()

    with connection:
        bollinger_stats = select_db_records(connection, search_param1)
    # print("...........Checkpoint Bollinger Signals values.........")
    # print(bollinger_stats)

    connection.close()
    # stock_growth = (pnl_result_filter['close_price'].values[-1] - pnl_result_filter['close_price'].values[0])/( pnl_result_filter['close_price'].values[0]) * 100
    # stock_growth = round(stock_growth, 2)
    # pnl_result_filter = pnl_result_filter.values.tolist()
    # print("Filtered.....result of PnL")
    # print(pnl_result_filter)
    # net_growth = round(net_growth,2)

    # Usee Trndspider
    # https://trendspider.com/developers/examples/
    return render(
        request,
        "BollingerStrategy.html",
        {
            #  'result1': pnl_result_filter,
            #   'result2': net_growth,
            "result3": bollinger_stats
            #   'result4': stock_growth
        },
    )


def bstrategyTicker(request):
    return render(request, "BollingerTicker.html")


def strategyTicker(request):
    return render(request, "strategyTicker.html")


def SearchTicker(request):
    return render(request, "search.html")


def Search(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # print("**********************")
    # print(os.path.join(BASE_DIR), "templates/")

    return render(request, "search1.html")


def CompareTickers(request):
    return render(request, "compare.html")


def StockFundamentals(request):
    search_param = dict()
    if request.method == "POST":
        search_param1 = request.POST["query1"]
        # print("Search paramas", search_param1)
        search_param2 = request.POST["query2"]
        # print("Search paramas", search_param2)
    else:
        try:
            search_param1 = json.loads(request.GET.get("search_param1", 1).replace("", "/"))
        except:
            # print("search_param not found!", search_param1)
            return HttpResponse("Error")

    if search_param1 is None:
        return HttpResponseRedirect(reverse("Menu.html"))

    # def create_connection(db_file):

    # connection = None
    # try:
    #    connection = sqlite3.connect('database.db')  # Works when on db name provided;  #db_file #Used db_path as well:: no table

    #    if connection:
    #        print("Connection Established Successfully!")
    #        print("Connection=", connection)
    # except Error as e:
    #    print(e)

    # return connection

    def select_db_records(connection, search_param1, search_param2):
        # print("Value of search_param in db_records=", search_param1, search_param2)
        cursor = connection.cursor()
        # print("Cusror returned", cursor)
        search_ticker1 = search_param1
        search_ticker2 = search_param2

        # Execute query with parameters

        query_stock_stats = """ SELECT SF.MarketCap, SF.ProfitMargin*100 as ProfitMargin, 
                            SF.DividendYield,  SF.PERatio, 
                            SF.ROE, SF.BookValue,
                            SF.EnterpriseValue, SF.CASH,
                            SF.DividendPayoutRatio,
                            SF.SortinoRatio, SF.Beta,
                            SF.Alpha, SF.SharpeRatio,
                            DP.Close, DP.High, DP.Low, DP.Ticker
                            FROM stock_fundamentals_summary SF
                            JOIN daily_price DP 
                            ON DP.Stock_Id = SF.Stock_Id 
                            AND DP.Ticker = %s """

        cursor.execute(query_stock_stats, (search_ticker1,))
        results_stats1 = cursor.fetchall()
        cursor.execute(query_stock_stats, (search_ticker2,))
        results_stats2 = cursor.fetchall()

        # if results_stats1:
        #     for row in results_stats1:
        #         print("******** data results1 *******")
        #         print(row)
        # if results_stats2:
        #     for row in results_stats2:
        #         print("******** data results2 *******")
        #         print(row)
        Win1count = 0
        Win2count = 0
        ProfitMargin1 = results_stats1[0][1]
        DividendYield1 = results_stats1[0][2]
        PERatio1 = results_stats1[0][3]
        ROE1 = results_stats1[0][4]
        DividendPayoutRatio1 = results_stats1[0][8]
        SortinoRatio1 = results_stats1[0][9]
        Beta1 = results_stats1[0][10]
        Alpha1 = results_stats1[0][11]
        SharpeRatio1 = results_stats1[0][12]

        ProfitMargin2 = results_stats2[0][1]
        DividendYield2 = results_stats2[0][2]
        PERatio2 = results_stats2[0][3]
        ROE2 = results_stats2[0][4]
        DividendPayoutRatio2 = results_stats2[0][8]
        SortinoRatio2 = results_stats2[0][9]
        Beta2 = results_stats2[0][10]
        Alpha2 = results_stats2[0][11]
        SharpeRatio2 = results_stats2[0][12]

        if SharpeRatio1 > SharpeRatio2:
            Win1count += 1
        else:
            Win2count += 1

        if SortinoRatio1 > SortinoRatio2:
            Win1count += 1
        else:
            Win2count += 1

        if DividendYield1 > DividendYield2:
            Win1count += 1
        else:
            Win2count += 1

        if PERatio1 > PERatio2:
            Win2count += 1
        else:
            Win1count += 1

        if Alpha1 > Alpha2:
            Win1count += 1
        else:
            Win2count += 1

        if Beta1 > Beta2:
            Win2count += 1
        else:
            Win1count += 1

        if ProfitMargin1 > ProfitMargin2:
            Win1count += 1
        else:
            Win2count += 1

        if Win1count > Win2count:
            Winner = search_param1
            Loser = search_param2
        else:
            Winner = search_param2
            Loser = search_param1

        return results_stats1, results_stats2, Winner, Loser

    # database = r"C:Users\gauravshruti\Downloads\StockMarketapp\SMART\database.db"
    connection = create_connection()

    with connection:
        results_stats1, results_stats2, Winner, Loser = select_db_records(connection, search_param1, search_param2)

    connection.close()
    return render(
        request,
        "StockFundamentals.html",
        {"result1": results_stats1, "result2": results_stats2, "result3": Winner, "result4": Loser},
    )


def display_stock_fundamentals(request):
    # def create_connection(db_file):
    # connection = None
    # try:
    #    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #    print("PAth=",os.path.join(BASE_DIR))

    #    db_path = os.path.join(BASE_DIR, "database.db")
    #    connection = sqlite3.connect('database.db')  # Works when on db name provided;  #db_file #Used db_path as well:: no table

    #    if connection:
    #        print("Connection Established Successfully!")
    #        print("Connection=", connection)
    # except Error as e:
    #    print(e)

    # return connection

    def select_db_records(connection, search_param):
        # print("Value of search_param in db_records=", search_param)
        cursor = connection.cursor()
        # print("Cusror returned", cursor)
        search_ticker = search_param
        query = """ SELECT * FROM daily_price WHERE Ticker = %s Order by Date desc limit 10"""

        # Execute query with parameters
        cursor.execute(query, (search_ticker,))  # Pass parameter as a tuple
        # Fetch results
        results_stock = cursor.fetchall()
        # rows = cursor.fetchall()
        # if results_stock:
        #     print("results found..")
        #     for row in results_stock:
        #         print(row)

        query_bal = """ SELECT * FROM balance_sheet B 
                        JOIN daily_price P 
                        ON P.Stock_Id = B.Stock_Id 
                        AND P.Ticker = %s Order by P.Date """

        cursor.execute(query_bal, (search_ticker,))
        results_balance = cursor.fetchall()

        # if results_balance:
        #     for row in results_balance:
        #         print(row)

        query_income = """ SELECT * FROM income_data ID
                             JOIN daily_price DP 
                             ON DP.Stock_Id = ID.Stock_Id 
                             AND DP.Ticker = %s Order by DP.Date"""

        cursor.execute(query_income, (search_ticker,))
        results_income = cursor.fetchall()

        # if results_income:
        #     for row in results_income:
        #         print(row)

        query_cashflow = """ SELECT * FROM cash_flow_data CD
                             JOIN daily_price DP 
                             ON DP.Stock_Id = CD.Stock_Id 
                             AND DP.Ticker = %s Order by DP.Date"""

        cursor.execute(query_cashflow, (search_ticker,))
        results_cashflow = cursor.fetchall()

        # if results_cashflow:
        #     for row in results_cashflow:
        #         print(row)

        query_holder = """ SELECT * FROM shareholding_data SD
                         WHERE SD.Ticker = %s Order by SD.pctHeld desc"""

        cursor.execute(query_holder, (search_ticker,))
        results_holders = cursor.fetchall()

        # if results_holders:
        #     for row in results_holders:
        #         print("********holders data results*******")
        #         print(row)

        query_stock_stats = """ SELECT SF.MarketCap, SF.ProfitMargin*100 as ProfitMargin, 
                            SF.DividendYield,  SF.PERatio, 
                            SF.ROE, SF.BookValue,
                            DP.Close, DP.High, DP.Low 
                            FROM stock_fundamentals_summary SF
                            JOIN daily_price DP 
                            ON DP.Stock_Id = SF.Stock_Id 
                            AND DP.Ticker = %s """

        cursor.execute(query_stock_stats, (search_ticker,))
        fundametal_stats = cursor.fetchall()

        # if fundametal_stats:
        #     for row in fundametal_stats:
        #         print("********holders data results*******")
        #         print(row)

        query_stock_return = """ SELECT SR.daily_return, SR.y1_return, 
                            SR.y3_return, SR.y5_return, SR.y10_return    
                            FROM stock_returns_summary SR
                            WHERE SR.Ticker = %s Limit 1 """

        query_stock_return1 = """ 
         
                SELECT SR.daily_return, SR.y1_return,
                SR.y3_return, SR.y5_return,SR.y10_return,
                start_date_1_year,
                start_date_3_year,
                start_date_5_year,
                start_date_10_year,
                SR.Ticker,
                SF.Date, SF.ProfitMargin
                FROM stock_returns_summary SR
                JOIN stock_fundamentals_summary SF on SF.Ticker = SR.Ticker
                WHERE  substr(SF.Date, 1,4) = substr(SR.start_date_1_year, 1,4)
                AND SR.Ticker = %s
            UNION
            SELECT SR.daily_return, SR.y1_return,
                SR.y3_return, SR.y5_return, SR.y10_return,
                start_date_1_year,
                start_date_3_year,
                start_date_5_year,
                start_date_10_year,
                SR.Ticker,
                SF.Date, SF.ProfitMargin
                FROM stock_returns_summary SR
                JOIN stock_fundamentals_summary SF on SF.Ticker = SR.Ticker
                WHERE  substr(SF.Date, 1,4) = substr(SR.start_date_3_year, 1,4)
                AND SR.Ticker = %s
            UNION
            SELECT SR.daily_return, SR.y1_return,
                SR.y3_return, SR.y5_return,SR.y10_return,
                start_date_1_year,
                start_date_3_year,
                start_date_5_year,
                start_date_10_year,
                SR.Ticker,
                SF.Date, SF.ProfitMargin
                FROM stock_returns_summary SR 
                JOIN stock_fundamentals_summary SF on SF.Ticker = SR.Ticker
                WHERE  substr(SF.Date, 1,4) = substr(SR.start_date_5_year, 1,4)
                AND SR.Ticker = %s 
                UNION
                SELECT SR.daily_return, SR.y1_return,
                    SR.y3_return, SR.y5_return,SR.y10_return,
                    start_date_1_year,
                    start_date_3_year,
                    start_date_5_year,
                    start_date_10_year,
                    SR.Ticker,
                    SF.Date, SF.ProfitMargin
                    FROM stock_returns_summary SR
                    JOIN stock_fundamentals_summary SF on SF.Ticker = SR.Ticker
                    WHERE  substr(SF.Date, 1,4) = substr(SR.start_date_10_year, 1,4)
                AND SR.Ticker = %s
                """

        query_stock_return_values = (search_ticker, search_ticker, search_ticker, search_ticker)

        cursor.execute(query_stock_return1, query_stock_return_values)
        results_stats = cursor.fetchall()

        # if results_stats:
        #     for row in results_stats:
        #         print("********Returns data results*******")
        #         print(row)

        query_news = """ SELECT Headline FROM news_events WHERE Ticker = %s Limit 3
        """

        cursor.execute(query_news, (search_ticker,))
        results_news = cursor.fetchall()

        # if results_news:
        #     for row in results_news:
        #         print("********Returns data results*******")
        #         print(row)
        results_news = ". ".join([i[0] for i in results_news])

        return (
            results_stock,
            results_balance,
            results_income,
            results_cashflow,
            results_holders,
            results_stats,
            fundametal_stats,
            results_news,
        )

    # database = r"C:Users\gauravshruti\Downloads\StockMarketapp\SMART\database.db"
    connection = create_connection()

    search_param = dict()
    if request.method == "POST":
        # print("POST Called..")
        search_param = request.POST["query"]
        # print("Search paramas", search_param)

    else:
        try:
            search_param = json.loads(request.GET.get("search_param", 1).replace("", "/"))
        except:
            print("search_param not found!")

    with connection:
        (
            results_stock,
            results_balance,
            results_income,
            results_cashflow,
            results_holders,
            results_stats,
            fundametal_stats,
            results_news,
        ) = select_db_records(connection, search_param)

    # cursor.close()
    connection.close()

    return render(
        request,
        "Fundamentals.html",
        {
            "results_stock": results_stock,
            "results_balance": results_balance,
            "results_income": results_income,
            "results_cashflow": results_cashflow,
            "results_holders": results_holders,
            "results_stats": results_stats,
            "fundametal_stats": fundametal_stats,
            "results_news": results_news,
        },
    )


def find_under_valued_stocks(request):
    if 'username' not in request.session:
        return redirect('login')  # Redirect to login page
    
    # def create_connection(db_file):
    #     connection = None
    #     try:
    #         BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #         print("PAth=",os.path.join(BASE_DIR))

    #         db_path = os.path.join(BASE_DIR, "database.db")
    #         connection = sqlite3.connect('database.db')
    #         if connection:
    #             print("Connection Established Successfully!")
    #             print("Connection=", connection)
    #     except Error as e:
    #         print(e)

    #     return connection

    def select_db_records(connection):

        cursor = connection.cursor()

        query_mv = """ SELECT DISTINCT Date, Ticker, Open, High, Low, Close, Volume 
                        oversold_signal FROM TechnicalSignalsView 
                        WHERE oversold_signal = -1 Order by Ticker asc Limit 30
        
                    """
        # Execute query with parameters
        cursor.execute(query_mv)  # Pass parameter as a tuple
        # Fetch resultsf
        results = cursor.fetchall()
        # rows = cursor.fetchall()
        # if results:
        #     print("results found..")
        #     for row in results:
        #         print(row)

        return results

    # database = r"C:Users\gauravshruti\Downloads\StockMarketapp\SMART\database.db"
    connection = create_connection()

    with connection:
        results = select_db_records(connection)

    connection.close()
    return render(request, "UnderValuedStocks.html", {"results": results})


def find_over_valued_stocks(request):
    if 'username' not in request.session:
        return redirect('login')  # Redirect to login page
    
    # def create_connection(db_file):
    #     connection = None
    #     try:
    #         BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    #         print("PAth=",os.path.join(BASE_DIR))

    #         db_path = os.path.join(BASE_DIR, "database.db")
    #         connection = sqlite3.connect('database.db')
    #         if connection:
    #             print("Connection Established Successfully!")
    #             print("Connection=", connection)
    #     except Error as e:
    #         print(e)

    #     return connection

    def select_db_records(connection):
        cursor = connection.cursor()

        ''' -------- Optimization by Materialized View -------------
        query = """ SELECT ST.Date, ST.Ticker, DP.Open, DP.High, DP.Low, DP.Close, DP.Volume 
                    from stock_technicals_summary ST JOIN daily_price DP 
                    ON DP.Stock_Id = ST.Stock_Id WHERE 1=1
                    AND overbought_signal = 1 Order by ST.Ticker asc limit 10	"""
        '''
        query_mv = """ SELECT DISTINCT Date, Ticker, Open, High, Low, Close, Volume 
                        oversold_signal FROM TechnicalSignalsView 
                        WHERE overbought_signal = 1 Order by Ticker asc Limit 30
        
                    """

        # Execute query with parameters
        cursor.execute(query_mv)  # Pass parameter as a tuple
        # Fetch results
        results = cursor.fetchall()
        # rows = cursor.fetchall()
        # if results:
        #     print("results found..")
        #     for row in results:
        #         print(row)

        return results

    # database = r"C:Users\gauravshruti\Downloads\StockMarketapp\SMART\database.db"
    connection = create_connection()

    with connection:
        results = select_db_records(connection)

    connection.close()
    return render(request, "OvervaluedStocks.html", {"results": results})


def find_golden_cross_stocks(request):
    if 'username' not in request.session:
        return redirect('login')  # Redirect to login page
    
    # def create_connection(db_file):
    #     connection = None
    #     try:
    #         connection = sqlite3.connect('database.db')
    #         if connection:
    #             print("Connection Established Successfully!")
    #             print("Connection=", connection)
    #     except Error as e:
    #         print(e)

    #     return connection

    def select_db_records(connection):
        cursor = connection.cursor()

        query_mv = """ SELECT DISTINCT Date, Ticker, Open, High, Low, Close, Volume 
                        oversold_signal FROM TechnicalSignalsView 
                        WHERE golden_cross_signal = 1 Order by Ticker asc Limit 30 """
        # Execute query with parameters
        cursor.execute(query_mv)  # Pass parameter as a tuple
        # Fetch results
        results = cursor.fetchall()
        # rows = cursor.fetchall()
        # if results:
        #     print("results found..")
        #     for row in results:
        #         print(row)

        return results

    # database = r"C:Users\gauravshruti\Downloads\StockMarketapp\SMART\database.db"
    connection = create_connection()

    with connection:
        results = select_db_records(connection)

    connection.close()
    return render(request, "GoldenStocks.html", {"results": results})


def find_bearish_cross_over(request):
    df = pd.DataFrame()  # remove
    fast_sma_period = 10
    slow_sma_period = 100

    df["slow_sma"] = df["Close"].rolling(slow_sma_period).mean()
    df["fast_sma"] = df["Close"].rolling(fast_sma_period).mean()

    # find crossover
    df["prv_fast_sma"] = df["fast_sma"].shift(1)
    df["prv_slow_sma"] = df["slow_sma"].shift(1)

    def find_crossover(fast_sma, slow_sma, prv_fast_sma):
        if fast_sma > slow_sma and prv_fast_sma < slow_sma:
            return "bullish cross over"
        elif fast_sma < slow_sma and prv_fast_sma > slow_sma:
            return "bearish cross over"
        else:
            return None

    df.dropna(inplace=True)
    df["crossover"] = np.vectorize(find_crossover)(df["fast_sma"], df["prv_fast_sma"], df["slow_sma"])
    df_bearish = df[df["crossover"] == "bearish cross over"]
    signal = df[df["crossover"] == "bullish cross over"].copy()

    results = signal
    return render(request, "BearishCrossOver.html", {"results": results})


################################# Back Testing #########################################################
def date_to_timestamp(date_string):
    date_obj = datetime.strptime(date_string, "%Y-%m-%d")
    timestamp = int(date_obj.timestamp())
    return timestamp


""" """


#### Asli Code
# Create RSI Trading Strategy
def RSI_trading_strategy(df):
    """
     ---------------------------------------------------------------
    |   Output: Function Returns the Profit returns of RSI Strategy |                                                        |
    | --------------------------------------------------------------|
    |   Input: Dataframe with RSI value of the stock                |
    |          neutral: Value of neutrality, no Action Zone         |
    |           window:  rolling period of the RSI                  |
    |                                                               |
     ---------------------------------------------------------------

    """
    # Buy Signal
    overbought = 70
    neutral_buy = 55

    # df["signal_buy"] = np.nan
    
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    df["previous_RSI"] = df["RSI"].shift(1)

    df

    # Create Signal for Long Buy by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # Trading strategy for Open Buy Signal when Prv RSI < 55 and Current RSI > 55: Handle True Signal
    # This implies that RSI has increased from Yesterday and and is not in Overbought Threshold indicating Trend Reversal
    # Therefore Buy Long can be Executed

    df.loc[(df["RSI"] > neutral_buy) & (df["previous_RSI"] < neutral_buy), "signal_buy"] = 1

    # Create Signal for Long Buy by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # If the Current RSI is dropping from Neutral_Buy then indication of the Trend can go down, hence No Long Position
    # Trading strategy for Close Buy Signal when Prv RSI > 55 and Current RSI < 55: Handle False Signal
    df.loc[(df["RSI"] < neutral_buy) & (df["previous_RSI"] > neutral_buy), "signal_buy"] = 0

    # Create Signal for Long Buy by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # Trading strategy for Close Buy Signal when Prv RSI > 70 and Current RSI < 70: Handle Overbought Signal
    df.loc[(df["RSI"] < overbought) & (df["previous_RSI"] > overbought), "signal_buy"] = 0

    # Sell Signal
    oversold = 30
    neutral_sell = 45
    # df["signal_sell"] = np.nan
    # Create Signal for Open Short Signal and Close Short Signal by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # Trading strategy for Open Buy Signal when Prv RSI > 45 and Current RSI < 45: Handle the True Signal
    # This implies that RSI has decreased from Yesterday and and is not in yet in Threshold situation but indicating Downward trend line signal
    # Therefore Sell can be Executed
    df.loc[(df["RSI"] < neutral_sell) & (df["previous_RSI"] > neutral_sell), "signal_sell"] = -1

    # Create Signal for Close Sell by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # If the Current RSI is Increasing from the neutral_sell then indication of the Trend can go Up, hence No Sell Position
    # Trading strategy for Close Buy Signal when Prv RSI < 45 and Current RSI > 45: Handle the False Signal
    df.loc[(df["RSI"] > neutral_sell) & (df["previous_RSI"] < neutral_sell), "signal_sell"] = 0

    # Create Signal for Close Sell by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # Trading strategy for Close Buy Signal when Prv RSI < 30 and Current RSI > 30: Handle Overbought Signal
    df.loc[(df["RSI"] > overbought) & (df["previous_RSI"] < overbought), "signal_sell"] = 0

    # Compute the Returns
    # df['pct_change'] = df['Close'].pct_change(1)
    # Evaluate the Position
    # df['Position'] = (df['signal_sell'].fillna(method='ffill') + df['signal_buy'].fillna(method='ffill'))
    # Find the Returns
    # df['return'] = (df['Position'].shift(1)) * df['pct_change']

    return df


def signal_val(df):
    buy_signal_val = []
    sell_signal_val = []

    for i in range(len(df["Close"])):
        if df["signal_buy"][i] == 1:

            buy_signal_val.append(df["Close"][i])
            sell_signal_val.append(0)
        elif df["signal_sell"][i] == -1:

            buy_signal_val.append(0)
            sell_signal_val.append(df["Close"][i])
        else:
            buy_signal_val.append(0)
            sell_signal_val.append(0)

    return (buy_signal_val, sell_signal_val)


class Position:
    def __init__(self, open_datetime, open_price, order_type, Volume, sl, tp):
        self.open_datetime = open_datetime
        self.open_price = open_price
        self.order_type = order_type
        self.Volume = Volume
        self.sl = sl
        self.tp = tp

        self.close_datetime = None
        self.close_price = None
        self.profit = None
        self.status = "Open"

    def close_position(self, close_datetime, close_price):
        self.close_datetime = close_datetime
        self.close_price = close_price
        self.profit = (
            (self.close_price - self.open_price) * self.Volume
            if self.order_type == "buy"
            else (self.open_price - self.close_price) * self.volume
        )  # Logic needs to be based on buy date and sell date
        self.status = "Closed"

    def _asdict(self):
        return {
            "open_datetime": self.open_datetime,
            "open_price": self.open_price,
            "order_type": self.order_type,
            "Volume": self.Volume,
            "sl": self.sl,
            "tp": self.tp,
            "close_datetime": self.close_datetime,
            "close_price": self.close_price,
            "profit": self.profit,
            "status": self.status,
        }


class Strategy:
    def __init__(self, df, starting_balance, Volume):
        self.starting_balance = starting_balance
        self.Volume = Volume
        self.positions = []
        self.data = df

    def get_positions_df(self):
        df = pd.DataFrame([position._asdict() for position in self.positions])
        df["pnl"] = df["profit"].cumsum() + self.starting_balance
        return df

    def add_position(self, position):
        self.positions.append(position)
        return True

    buy_price = []
    sell_price = []

    # def run(self):
    #     for i, data in self.data.iterrows():
    #         if data.crossover == 'bullish cross over':

    #             self.add_position(Position(data.time, data.Close, 'buy', self.Volume, 0, 0))
    #             #buy_price[i] = data.Close
    #         if data.crossover == 'bearish cross over':

    #             #sell_price[i] = data.Close
    #             for position in self.positions:
    #                 if position.status == 'Open':
    #                     position.close_position(data.time, data.Close)

    def run(self):
        for i, data in self.data.iterrows():
            if data.signal_buy > 0:

                self.add_position(Position(data.time, data.Close, "buy", self.Volume, 0, 0))
                # buy_price[i] = data.Close
            if data.signal_sell > 0:

                # sell_price[i] = data.Close
                for position in self.positions:
                    if position.status == "Open":
                        position.close_position(data.time, data.Close)

        return self.get_positions_df()



def load_equities_web(symbol, date_from):
    yf.pdr_override()
    startdate = datetime(2020, 12, 1)
    enddate = datetime(2023, 6, 30)
    # raw_data = web.DataReader(symbol, 'yahoo', pd.to_datetime(date_from), pd.datetime.now())
    data = pdr.get_data_yahoo(symbol, start=startdate, end=enddate)
    # data = raw_data.stack(dropna=False)['Adj Close'].to_frame().reset_index().rename(columns= {'Symbols':'symbol', 'Date':'date','Adj Close':'value'}).sort_values(by = ['symbol', 'date'])
    return data


def chart(request):
    # Make it Dynamic based on Strategy df
    df = load_equities_web(["AAPL"], date_from="2023-01-01")

    df = RSI_trading_strategy(df)
    df["buy_signal_val"] = signal_val(df)[0]
    df["sell_signal_val"] = signal_val(df)[1]
    dummy_df = df[df["buy_signal_val"] != 0]
    # print(dummy_df)
    # Plot all the datas
    fig = plt.figure(figsize=(12, 10))
    # Add the subplot
    ax = fig.add_subplot(1, 1, 1)  # same size
    # Get the Index values of the data frame
    x_axis = df.index
    # Plot and shade the area between Upper band and Lower band
    # ax.fill_between(x_axis, data['Upper'], data['Lower'], color='grey')
    ax.plot(x_axis, df["Close"], color="gold", lw=4, label="Close Price")
    ax.scatter(x_axis, df["buy_signal_val"], color="green", lw=3, label="Buy", marker="v")
    ax.scatter(x_axis, df["sell_signal_val"], color="red", lw=3, label="Sell", marker="^")
    plt.plot(df.index, df["RSI"])
    plt.axhline(0, linestyle="--", alpha=0.5, color="gray")
    plt.axhline(10, linestyle="--", alpha=0.5, color="orange")
    plt.axhline(20, linestyle="--", alpha=0.5, color="green")
    plt.axhline(30, linestyle="--", alpha=0.5, color="red")
    plt.axhline(70, linestyle="--", alpha=0.5, color="red")
    plt.axhline(80, linestyle="--", alpha=0.5, color="green")
    plt.axhline(90, linestyle="--", alpha=0.5, color="orange")
    plt.axhline(100, linestyle="--", alpha=0.5, color="gray")
    ax.set_title("RSI Price Action Signals")
    ax.set_xlabel("Date")
    ax.set_ylabel("USD Price ($)")
    plt.xticks(rotation=45)

    # Save the figure to a memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    # Convert the image to base64
    graphic = urllib.parse.quote(base64.b64encode(image_png))
    html_fig = mpld3.fig_to_html(fig)
    # Pass the base64 string to the template
    return render(request, "Chart.html", {"html_fig": html_fig})


def dashboardView(request):
    if 'username' not in request.session:
        return redirect('login')  # Redirect to login page
    
    def select_db_records(connection):
        query_dashboardView = """  SELECT DISTINCT  Ticker, y1_return, y3_return, y5_return,
            Close,
            Volume,
            Date
            FROM DashboardView Where Date = '2024-03-28'
            ORDER BY Ticker DESC  """

        query_dashboardAggView = """  SELECT tradeableAssets, NonTradeableAssets, OverboughtStocks, OverSoldStocks, MomentumStocks,
            DividendPayingStocks, LargeCapStocks, GrwothStocks
            FROM DashboardAggView
        """
        cursor = connection.cursor()

        # Execute query with parameters
        cursor.execute(query_dashboardView)  # Pass parameter as a tuple
        # Fetch results
        results = cursor.fetchall()
        # rows = cursor.fetchall()
        # if results:
        #     print("results found..")
        #     for row in results:
        #         print(row)

        cursor.execute(query_dashboardAggView)  # Pass parameter as a tuple
        # Fetch results
        results2 = cursor.fetchall()
        # rows = cursor.fetchall()
        # if results2:
        #     print("results found..")
        #     for row in results2:
        #         print(row)

        return results, results2

    connection = create_connection()

    with connection:
        results, results2 = select_db_records(connection)

    connection.close()

    return render(request, "dashboard.html", {"result1": results, "result2": results2})
