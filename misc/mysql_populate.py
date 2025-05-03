# Define your connection parameters
# HOST = ''
# USER = ''
# PASSWORD = ''
# DATABASE = 'SMART'  
# PORT = 

HOST = '<RDS_DATABASE_HOST>'
USER = 'admin'
PASSWORD = '<PASSWORD>'
DATABASE = 'SMART'  
PORT = 3306

import mysql.connector

try:
    # Establish the connection
    conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        port=PORT
    )
    if conn.is_connected():
        print("Connected to MySQL database")
        # Perform database operations here
except mysql.connector.Error as e:
    print("Error connecting to MySQL database:", e)


import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
import datetime
from datetime import datetime, timedelta
import time
import os
import sys
import warnings
from uuid import uuid4
import alpaca_trade_api as tradeapi
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import math
import yfinance as yfin
from decimal import ROUND_HALF_UP, Decimal
from tqdm import tqdm
import ta

import warnings
warnings.filterwarnings("ignore")

APCA_API_BASE_URL = "https://api.alpaca.markets"
APCA_API_KEY_ID = "PKLJBHD5K70ZJQ9YIKEH"
APCA_API_SECRET_KEY = "lxZTnoH7PzLhYlbarUzWGGriohcpudGpQ0CkrkGr"
os.environ['APCA_API_KEY_ID'] = APCA_API_KEY_ID
os.environ['APCA_API_BASE_URL'] = APCA_API_BASE_URL
os.environ['APCA_API_SECRET_KEY'] = APCA_API_SECRET_KEY

# Initialize the Alpaca API
alpaca_api = tradeapi.REST(key_id=os.environ.get('APCA_API_KEY_ID'),
                    secret_key=os.environ.get('APCA_API_SECRET_KEY'),
                    base_url=os.environ.get('APCA_API_BASE_URL')
                )                


cursor = conn.cursor()
query = f"""USE {DATABASE};"""
cursor.execute(query)


cursor = conn.cursor()
query = f"""SHOW TABLES;"""
cursor.execute(query)
data = cursor.fetchall()
for row in data:
    print(row)


#########################################################################
######################### Create Daily Price table ######################
#########################################################################

cursor = conn.cursor()
table_name = "daily_price"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)

query = f"""
    CREATE TABLE {table_name} (
        Stock_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        Open FLOAT,
        High FLOAT,
        Low FLOAT,
        Close FLOAT,
        Volume FLOAT,
        Dividends FLOAT,
        Stock_Splits FLOAT,
        Ticker VARCHAR(10),
        Date VARCHAR(10),
        Fin_Year VARCHAR(4)
    );
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")

##########################################################################
######################### Create Balance Sheet Data table ################
##########################################################################

cursor = conn.cursor()
table_name = "balance_sheet"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)

# Create balance_sheet table
query = f"""
    CREATE TABLE {table_name} (
        Balance_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        Total_Debt FLOAT,
        Common_Stock_Equity FLOAT,
        Stockholders_Equity FLOAT,
        Common_Stock FLOAT,
        Current_Assets FLOAT,
        Current_Liabilities FLOAT,
        Cash_And_Cash_Equivalents FLOAT,
        Ticker VARCHAR(50),
        Date VARCHAR(10),
        Fin_Year VARCHAR(4),
        Stock_Id VARCHAR(50),
        FOREIGN KEY (Stock_Id) REFERENCES daily_price(Stock_Id)
    )
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")


##########################################################################
######################### Create Income Data table #######################
##########################################################################

cursor = conn.cursor()
table_name = "income_data"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)


query = f"""
    CREATE TABLE {table_name} (
        Income_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        Net_Interest_Income FLOAT, 
        Interest_Expense FLOAT, 
        Interest_Income FLOAT,
        Total_Expenses FLOAT, 
        Basic_EPS FLOAT, 
        Net_Income FLOAT,
        Operating_Income FLOAT, 
        Operating_Expense FLOAT,
        Gross_Profit FLOAT,
        Total_Revenue FLOAT,
        Ticker VARCHAR(50),
        Date VARCHAR(10),
        Fin_Year VARCHAR(4),
        Stock_Id VARCHAR(50),
        FOREIGN KEY (Stock_Id) REFERENCES daily_price(Stock_Id)
    )
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")


##########################################################################
######################### Create Cash Flow Data table ####################
##########################################################################

cursor = conn.cursor()
table_name = "cash_flow_data"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)

# Create Cash_flow_data table
query = f"""
    CREATE TABLE {table_name} (
        Cashflow_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        Free_Cash_Flow FLOAT,
        Net_Income_From_Continuing_Operations FLOAT,
        Cash_Dividends_Paid FLOAT, 
        Common_Stock_Dividend_Paid FLOAT,
        Repayment_Of_Debt FLOAT,
        End_Cash_Position FLOAT,  
        Investing_Cash_Flow FLOAT,
        Cash_Flow_From_Continuing_Investing_Activities FLOAT,
        Cash_Flow_From_Continuing_Operating_Activities FLOAT, 
        Ticker VARCHAR(50),
        Date VARCHAR(10),
        Fin_Year VARCHAR(4),
        Stock_Id VARCHAR(50),
        FOREIGN KEY (Stock_Id) REFERENCES daily_price(Stock_Id)
    )
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")


##########################################################################
######################### Create Dividend Data table ####################
##########################################################################

cursor = conn.cursor()
table_name = "dividend_data"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)


query = f"""
    CREATE TABLE {table_name} (
        Dividend_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        Dividends FLOAT,
        Stock_Splits FLOAT,
        Ticker VARCHAR(50),
        Date VARCHAR(10),
        Fin_Year VARCHAR(4),
        Stock_Id VARCHAR(50),
        FOREIGN KEY (Stock_Id) REFERENCES daily_price(Stock_Id)
    )
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")


##########################################################################
######################### Share Holding Pattern Data table ###############
##########################################################################

cursor = conn.cursor()
table_name = "shareholding_data"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)

query = f"""
    CREATE TABLE {table_name} (
        Shareholder_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        Holder VARCHAR(255),
        pctHeld FLOAT,
        Shares FLOAT,
        Value FLOAT,
        Ticker VARCHAR(50)
    )
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")


##########################################################################
######################### Stock Returns Summary table ####################
##########################################################################

cursor = conn.cursor()
table_name = "stock_returns_summary"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)

# Create stock_returns_summary table
query = f"""
    CREATE TABLE {table_name} (
        Stock_agg_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        daily_return FLOAT,
        y1_return FLOAT,
        y3_return FLOAT,
        y5_return FLOAT,
        y10_return FLOAT,
        start_date_1_year VARCHAR(10),
        start_date_3_year VARCHAR(10),
        start_date_5_year VARCHAR(10),
        start_date_10_year VARCHAR(10),
        Ticker VARCHAR(50),
        Date VARCHAR(10),
        Fin_Year VARCHAR(4),
        Stock_Id VARCHAR(50),
        FOREIGN KEY (Stock_Id) REFERENCES daily_price(Stock_Id)
    );
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")


##########################################################################
######################### Stock Fundamentals Summary table ###############
##########################################################################

cursor = conn.cursor()
table_name = "stock_fundamentals_summary"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)

# Create Stock_summary table
query = f"""
    CREATE TABLE stock_fundamentals_summary (
        Stock_agg_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        ProfitMargin FLOAT,
        DividendYield FLOAT,
        BookValue FLOAT,
        MarketCap FLOAT,
        PERatio FLOAT,
        CASH FLOAT,
        EnterpriseValue FLOAT,
        DividendPayoutRatio FLOAT,
        ROE FLOAT,
        SortinoRatio FLOAT,
        Beta FLOAT,
        Alpha FLOAT,
        SharpeRatio FLOAT,
        daily_return FLOAT,
        cum_return FLOAT,
        Ticker VARCHAR(50),
        Date VARCHAR(10),
        Fin_Year VARCHAR(4),
        Stock_Id VARCHAR(50),
        FOREIGN KEY (Stock_Id) REFERENCES daily_price(Stock_Id)
    )
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")


##########################################################################
######################### Stock Technicals Summary table #################
##########################################################################
'''
add Beta, Alpha, SharpeRatio, SortinoRatio 
'''
cursor = conn.cursor()
table_name = "stock_technicals_summary"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)

query = f"""
    CREATE TABLE stock_technicals_summary (
        Stock_agg_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        RSI FLOAT,
        overbought_signal BOOL,
        oversold_signal BOOL,
        golden_cross_signal BOOL,
        Ticker VARCHAR(50),
        Date VARCHAR(10),
        Fin_Year VARCHAR(4),
        Stock_Id VARCHAR(50),
        FOREIGN KEY (Stock_Id) REFERENCES daily_price(Stock_Id)
    )
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")


##########################################################################################
######################### Strategy table (Swing Trading) - snapshot data #################
##########################################################################################
cursor = conn.cursor()
table_name = "strategy"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)

query = f"""
    CREATE TABLE {table_name} (
        Strategy_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        rsi_signal_buy BOOLEAN,
        rsi_signal_sell BOOLEAN,
        rsi_PriceAction VARCHAR(255),
        bollinger_buy_signal BOOLEAN,
        bollinger_sell_signal BOOLEAN,
        bollinger_priceAction VARCHAR(255),
        mfi_Buy_signal BOOLEAN,
        mfi_Sell_signal BOOLEAN,
        mfi_priceAction VARCHAR(255),
        fab_buy_signal BOOLEAN,
        fab_sell_signal BOOLEAN,
        fab_priceAction VARCHAR(255),
        Ticker VARCHAR(50),
        Date VARCHAR(10),
        Fin_Year VARCHAR(4),
        Stock_Id VARCHAR(50),
        FOREIGN KEY (Stock_Id) REFERENCES daily_price(Stock_Id)
    )
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")


# ##########################################################################
# ######################### Strategy table - Real Time Snapshot ############
# ##########################################################################

# cursor = conn.cursor()
# table_name = "strategy_real_time"
# query = f"""DROP TABLE IF EXISTS {table_name}"""
# data = cursor.execute(query)

# query = f"""
#     CREATE TABLE {table_name} (
#         Strategy_Real_Time_Id VARCHAR(50) PRIMARY KEY NOT NULL,
#         rsi_signal_buy BOOLEAN,
#         rsi_signal_sell BOOLEAN,
#         rsi_PriceAction VARCHAR(255),
#         Ticker VARCHAR(50),
#         Date VARCHAR(10),
#         Fin_Year VARCHAR(10),
#         Stock_Id VARCHAR(50),
#         FOREIGN KEY (Stock_Id) REFERENCES daily_price(Stock_Id)
#     )
# """
# cursor.execute(query)
# conn.commit()
# print(f"{table_name} created successfully")


#########################################################################
######################### Create News Events table ######################
#########################################################################

cursor = conn.cursor()
table_name = "news_events"
query = f"""DROP TABLE IF EXISTS {table_name}"""
data = cursor.execute(query)

query = f"""
    CREATE TABLE {table_name} (
        News_Event_Id VARCHAR(50) PRIMARY KEY NOT NULL,
        Ticker VARCHAR(10),
        Headline VARCHAR(255),
        Url VARCHAR(255)
    );
"""
cursor.execute(query)
conn.commit()
print(f"{table_name} created successfully")

##########################################################################
##########################################################################


def find_last_date_indexes(date_list):
    last_date_indexes = {}
    for idx, date_str in enumerate(date_list):
        # Convert date string to datetime object
        current_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Extract the year from the current date
        year = current_date.year

        # Check if the current date is the last day of the year
        if year not in last_date_indexes or current_date > last_date_indexes[year][0]:
            last_date_indexes[year] = (current_date, idx)

    return last_date_indexes


def stock_table_df(df, table_cols, company):
    table_df = pd.DataFrame()

    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
        
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company.ticker, 
            'Stock_Id': str(uuid4())
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")
        
        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        temp_df = pd.DataFrame(temp_data)
        table_df = pd.concat([table_df, temp_df], ignore_index=True)
    
    return table_df


def balance_sheet_table_df(df, table_cols, company):
    table_df = pd.DataFrame()

    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
        
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company.ticker, 
            'Balance_Id': str(uuid4()),
            'Stock_Id': "" 
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")
        
        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        temp_df = pd.DataFrame(temp_data)
        table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
    return table_df


def income_data_table_df(df, table_cols, company):
    table_df = pd.DataFrame()

    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
        
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company.ticker, 
            'Income_Id': str(uuid4()),
            'Stock_Id': "" 
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")
        
        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        temp_df = pd.DataFrame(temp_data)
        table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
    return table_df


def cash_flow_data_table_df(df, table_cols, company):
    table_df = pd.DataFrame()

    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
        
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company.ticker, 
            'Cashflow_Id': str(uuid4()),
            'Stock_Id': "" 
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")
                    
        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        temp_df = pd.DataFrame(temp_data)
        table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
    return table_df


def dividend_data_table_df(df, table_cols, company):
    table_df = pd.DataFrame()

    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
        
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company.ticker, 
            'Dividend_Id': str(uuid4()),
            'Stock_Id': "" 
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")
        
        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        temp_df = pd.DataFrame(temp_data)
        table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
    return table_df


def shareholding_data_table_df(df, table_cols, company):
    table_df = pd.DataFrame()

    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
    
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company.ticker, 
            'Shareholder_Id': str(uuid4())
            # 'Stock_Id': "" 
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")
        
        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        temp_df = pd.DataFrame(temp_data)
        table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
    return table_df


def stock_returns_summary_table_df(df, table_cols, company_ticker):
    from uuid import uuid4
    table_df = pd.DataFrame()

    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
        
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company_ticker, 
            'Stock_agg_Id': str(uuid4()),
            'Stock_Id': ""
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")
        
        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        temp_df = pd.DataFrame(temp_data)
        # print("********** temp data *************")
        # print(temp_df)
        table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
    return table_df


def calculate_fundamental_SortinoRatio(company_ticker, start_date,end_date):

    df = fetch_history_data(company_ticker, start_date, end_date)
    daily_return = df['Close'].pct_change(1)
    daily_return.name = "return"

    volatility = daily_return[daily_return<0].std()
    mean = daily_return.mean()
    SortinoRatio = np.sqrt(252) * mean/volatility

    return SortinoRatio


def calculate_fundamental_Beta(company_ticker, start_date, end_date):
    import pandas as pd

    import pandas_datareader as web
    from pandas_datareader import data as pdr
    import yfinance as yfin
    yfin.pdr_override()
    snp500 = pdr.get_data_yahoo('SPY',  start='2020-01-01', end='2023-06-30')["Close"].pct_change(1)
    #snp500 = yf.download("^GSPC")["Close"].pct_change(1)
    snp500.name = "SP500"
    df = yf.download(company_ticker).dropna()
    daily_return = df['Close'].pct_change(1)
    daily_return.name = "return"
    val = pd.concat((daily_return, snp500), axis=1).dropna()
    covariance = np.cov(val[["return", "SP500"]].values, rowvar = False)[0][1]
    var = np.var(val["SP500"].values)

    Beta = covariance/var

    return Beta


def fetch_history_data(symbol, start_date, end_date):

    #stock_data_df = yf.download(symbol, start=start_date, end=end_date)
    stock_data_df = yf.Ticker(symbol).history(period="12mo")
    stock_data_df = pd.DataFrame(stock_data_df)

    return stock_data_df


def calculate_fundamental_alpha(company_ticker, Beta, start_date, end_date):

    df = fetch_history_data(company_ticker, start_date, end_date)
    daily_return = df['Close'].pct_change(1)
    daily_return.name = "return"
    mean = daily_return.mean()
    Beta = calculate_fundamental_Beta(company_ticker, start_date, end_date)
    Alpha  = 252 * (mean - Beta * mean)

    return Alpha


def calculate_fundamental_SharpeRatio(company_ticker, start_date, end_date, risk_free_rate=0):

    df = fetch_history_data(company_ticker, start_date, end_date)
    daily_return = df['Close'].pct_change(1)
    daily_return.name = "return"

    mean_return = daily_return.mean()
    std = daily_return.std()
    SharpeRatio = (mean_return - risk_free_rate)/std

    return SharpeRatio * np.sqrt(252)


def calculate_fundamental_returns_1y_3y_5y_10y_15y_20y(symbol):
    # Define the date range
    end_date = datetime.today().strftime('%Y-%m-%d')    
    start_date = '2024-03-31'
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    start_date_1_year = (start_date - relativedelta(years=1))
    start_date_3_year = (start_date - relativedelta(years=3))
    start_date_5_year = (start_date - relativedelta(years=5))
    start_date_10_year = (start_date - relativedelta(years=10))

    # Download history
    history = yf.download(symbol, start=start_date_10_year, end=end_date)

    # Calculate returns
    daily_return = (history['Adj Close'].pct_change())
    y1_return = (history['Adj Close'].pct_change() + 1).loc[start_date_1_year:end_date].cumprod() - 1
    y3_return = (history['Adj Close'].pct_change() + 1).loc[start_date_3_year:end_date].cumprod() - 1
    y5_return = (history['Adj Close'].pct_change() + 1).loc[start_date_5_year:end_date].cumprod() - 1
    y10_return = (history['Adj Close'].pct_change() + 1).loc[start_date_10_year:end_date].cumprod() - 1

    daily_return = round(daily_return.iloc[-1] * 100, 2)
    y1_return = round(y1_return.iloc[-1] * 100, 2)
    y3_return = round(y3_return.iloc[-1] * 100, 2)
    y5_return = round(y5_return.iloc[-1] * 100, 2)
    y10_return = round(y10_return.iloc[-1] * 100, 2)

    return  daily_return, y1_return, y3_return, y5_return, y10_return, start_date_1_year.strftime('%Y-%m-%d'), start_date_3_year.strftime('%Y-%m-%d'), start_date_5_year.strftime('%Y-%m-%d'), start_date_10_year.strftime('%Y-%m-%d')


def agg_Stock_income_cash_data(company_ticker):
    temp_conn = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        port=PORT
    )
    sql_select_query = f"""
    Select DP.Stock_Id, DP.Ticker, DP.Date, DP.Stock_ID,
    (ID.Net_Income/ID.Total_Revenue) as ProfitMargin,
    (DD.Dividends/DP.Close) as DividendYield,
    BD.Total_Debt as TotalDebt,
    (BD.Stockholders_Equity/BD.Common_Stock_Equity)	as BookValue,
        (DP.Volume * DP.Close) as MarketCap,
    (DP.Close/ID.Basic_EPS) as PERatio,
    ID.Basic_EPS as EPS,
        (CD.Free_Cash_Flow + CD.End_Cash_Position + CD.Investing_Cash_Flow + CD.Cash_Flow_From_Continuing_Investing_Activities + CD.Cash_Flow_From_Continuing_Operating_Activities)  
    as CASH,
        ((DP.Volume * DP.Close) + (BD.Total_Debt) -  (CD.Free_Cash_Flow + CD.End_Cash_Position + CD.Investing_Cash_Flow + CD.Cash_Flow_From_Continuing_Investing_Activities + CD.Cash_Flow_From_Continuing_Operating_Activities) ) 
        as EnterpriseValue ,
        ((CD.Cash_Dividends_Paid +CD.Common_Stock_Dividend_Paid)/ ID.Net_Interest_Income) as DividendPayoutRatio,
    ( ID.Net_Interest_Income/BD.Stockholders_Equity) as ROE     
    FROM daily_price DP
    JOIN balance_sheet BD ON BD.Stock_id = DP.Stock_id
    JOIN cash_flow_data CD ON DP.Stock_id = CD.Stock_id
    JOIN income_data ID ON ID.Stock_id = DP.Stock_id
    JOIN dividend_data DD ON DD.Stock_id = DP.Stock_id
    WHERE DP.Ticker = '{company_ticker}'
    """
    temp_cursor = temp_conn.cursor()
    temp_cursor.execute(sql_select_query)
    data = temp_cursor.fetchall()

    # Get column names from the cursor description
    columns = [col[0] for col in temp_cursor.description]
    df = pd.DataFrame(data, columns=columns)
    temp_cursor.close()

    if 'temp_conn' in locals() and temp_conn.is_connected():
        temp_conn.close()
        
    return df


def stock_fundamentals_summary_table_df(df, table_cols, company_ticker):
    table_df = pd.DataFrame()

    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
        
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company_ticker, 
            'Stock_agg_Id': str(uuid4())
            'Stock_Id': "" 
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")
        
        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        temp_df = pd.DataFrame(temp_data)
        #print("********** temp data *************")
        #print(temp_df)
        table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
    return table_df


def calculate_fundamental_Returns(company_ticker, start_date, end_date):

    df = fetch_history_data(company_ticker, start_date, end_date)
    daily_return = df['Close'].pct_change(1)
    daily_return.name = "return"
    df['daily_return'] = daily_return.mean()
    # print("Inside Function...")
    # print( df['daily_return'])
    cum_return = (1 + df['daily_return']).cumprod() - 1         

    return  daily_return.mean(), cum_return.mean()


def stock_technicals_summary_table_df(df, table_cols, company_ticker):
    table_df = pd.DataFrame()

    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
        
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company_ticker, 
            'Stock_agg_Id': str(uuid4()),
            'Stock_Id': "" 
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")

        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        temp_df = pd.DataFrame(temp_data)
        table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
    return table_df


def check_overbought_rsi_indicator(stock_data_tech_df):
  
    overbought = 70
    df["overbought_signal"] = np.nan
    stock_data_tech_df.loc[(stock_data_tech_df['RSI'] > overbought), "overbought_signal"] = 1
    stock_data_tech_df = stock_data_tech_df.fillna(0)

    return stock_data_tech_df['overbought_signal']


def check_oversold_rsi_indicator(stock_data_tech_df):
    import numpy as np
    oversold = 30
    df["oversold_signal"] = np.nan
    stock_data_tech_df.loc[(stock_data_tech_df['RSI'] < oversold), "oversold_signal"] = -1
    stock_data_tech_df = stock_data_tech_df.fillna(0)

    return stock_data_tech_df["oversold_signal"]


def Golden_Cross(stock_data_tech_df):
    # We download the stock price from start date until end date
    #stock_data_tech_df = yf.download("AAPL", start="2018-01-01", end="2021-06-01")

    # We compute our simple moving averages
    stock_data_tech_df["50_sma"] = stock_data_tech_df["Close"].rolling(50).mean()
    stock_data_tech_df["200_sma"] = stock_data_tech_df["Close"].rolling(200).mean()

    # This is important so that we have both SMA starting a the same time.
    stock_data_tech_df = stock_data_tech_df.dropna() 

    # We compute our 50 SMA > 200 SMA
    stock_data_tech_df["golden_cross_signal"] = stock_data_tech_df.apply(lambda row: 1 if row[f"50_sma"] > row[f"200_sma"]  else 0, axis=1)

    # To store when our golden cross are happening
    # list_golden_cross_ts = []
    # first_golden_cross = False

    # We take the date where the first 50 SMA > 200 SMA appears
    #for idx, each in stock_data_tech_df["golden_cross_signal"].iteritems():
    #    if each == 1:
            # If its the first golden cross we see we add the timestamp
    #        if first_golden_cross:
    #            list_golden_cross_ts.append(idx)
    #            first_golden_cross = False
    #    else:
    #        first_golden_cross = True

    return stock_data_tech_df["golden_cross_signal"]


def calculate_rsi(prices, period=14):
    delta = prices.diff()

    gain = delta.where(delta >0, 0)
    loss= -delta.where(delta <0, 0)
    avg_gain = gain.ewm(com=period-1, min_periods = period).mean()
    avg_loss = loss.ewm(com=period-1, min_periods = period).mean()

    rs = avg_gain /avg_loss
    rsi = (100 - 100/(1+rs))
    return rsi


def strategy_table_df(df, table_cols, company_ticker):
    table_df = pd.DataFrame()
    # print("df of strategies::::::", df)
    # print(table_cols)
    if df.index.inferred_type == 'datetime64':
        ADD_DATE_INDEX = True
    else:
        ADD_DATE_INDEX = False
        
    for idx, row in df.iterrows():
        temp_data = {
            'Ticker': company_ticker, 
            'Strategy_Id': str(uuid4()),
            'Stock_Id': "" 
        }
        if ADD_DATE_INDEX:
            temp_data['Date'] = idx.strftime("%Y-%m-%d")
            temp_data['Fin_Year'] = idx.strftime("%Y")
        
        for i in row.keys():
            if i in table_cols:
                col_name = i.replace(' ', '_')
                temp_data[col_name] = [row[i]]
        #print("******** Strategy temp data *************")
        #print(temp_data)
        temp_df = pd.DataFrame(temp_data)

        table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
    return table_df


def rsi_trading_signals(df):
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

    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    #df =df.dropna()
    df["previous_RSI"] = df['RSI'].shift(1)

    # Buy Signal
    overbought = 70
    neutral_buy = 55

    #df["signal_buy"] = np.nan


    # Create Signal for Long Buy by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # Trading strategy for Open Buy Signal when Prv RSI < 55 and Current RSI > 55: Handle True Signal
    # This implies that RSI has increased from Yesterday and and is not in Overbought Threshold indicating Trend Reversal
        # Therefore Buy Long can be Executed
    # print("df print for rsi")
    # print(df)
    df.loc[(df['RSI'] > neutral_buy) & (df['previous_RSI'] < neutral_buy), "rsi_signal_buy"] = 1

    # Create Signal for Long Buy by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
     # If the Current RSI is dropping from Neutral_Buy then indication of the Trend can go down, hence No Long Position
    # Trading strategy for Close Buy Signal when Prv RSI > 55 and Current RSI < 55: Handle False Signal
    df.loc[(df['RSI'] < neutral_buy) & (df['previous_RSI'] > neutral_buy), "rsi_signal_buy"] = 0

    # Create Signal for Long Buy by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # Trading strategy for Close Buy Signal when Prv RSI > 70 and Current RSI < 70: Handle Overbought Signal
    df.loc[(df['RSI'] < overbought) & (df['previous_RSI'] > overbought), "rsi_signal_buy"] = 0


    # Sell Signal
    oversold = 30
    neutral_sell = 45
    #df["signal_sell"] = np.nan
    # Create Signal for Open Short Signal and Close Short Signal by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # Trading strategy for Open Buy Signal when Prv RSI > 45 and Current RSI < 45: Handle the True Signal
    # This implies that RSI has decreased from Yesterday and and is not in yet in Threshold situation but indicating Downward trend line signal
        # Therefore Sell can be Executed
    df.loc[(df['RSI'] < neutral_sell) & (df['previous_RSI'] > neutral_sell), "rsi_signal_sell"] = -1


    # Create Signal for Close Sell by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
     # If the Current RSI is Increasing from the neutral_sell then indication of the Trend can go Up, hence No Sell Position
    # Trading strategy for Close Buy Signal when Prv RSI < 45 and Current RSI > 45: Handle the False Signal
    df.loc[(df['RSI'] > neutral_sell) & (df['previous_RSI'] < neutral_sell), "rsi_signal_sell"] = 0

    # Create Signal for Close Sell by compare Current RSI and Previous Day RSI & Check for Trend Up or Down
    # Trading strategy for Close Buy Signal when Prv RSI < 30 and Current RSI > 30: Handle Overbought Signal
    df.loc[(df['RSI'] > overbought) & (df['previous_RSI'] < overbought), "rsi_signal_sell"] = 0


    # Compute the Returns
    df['pct_change'] = df['Close'].pct_change(1)
    # Evaluate the Position
    df['Position'] = (df['rsi_signal_sell'].fillna(method='ffill') + df['rsi_signal_buy'].fillna(method='ffill'))
    # Find the Returns
    df['return'] = (df['Position'].shift(1)) * df['pct_change']

    # default No Action Req
    df['rsi_PriceAction'] = 'No Action Req'
    for i in range(1, len(df)):
        if df['rsi_signal_buy'].iloc[i] == 1:

            df['rsi_PriceAction'].iloc[i] = "Long Position Action Req"


        elif df['rsi_signal_sell'].iloc[i] == -1:

            df['rsi_PriceAction'].iloc[i] = "Short Position Action Req"

        else:
            df['rsi_PriceAction'].iloc[i] = "No Action Req"
    #return df['rsi_signal_buy'], df['rsi_signal_sell'], df['rsi_PriceAction']
    return df

def bollinger_trade_signals(df):
    """
    ------------------------------------------------------------------
    |Output: Function Returns the Profit returns of Bollinger Strategy|
    | --------------------------------------------------------------  |
    |   Input: Dataframe with Pricing value of the stock              |
    |          SMA: Value STD: Value                                  |
    |          Upper level:  SMA + STD *2                             |
    |          Lower Level: SMa - STD *2                              |
    ------------------------------------------------------------------

    """

    
    period =30
    #Calculate the SMA
    df['SMA'] = df['Close'].rolling(window=period).mean()
    #Get the Standard Deviation
    df['STD'] = df['Close'].rolling(window=period).std()
    #Calculate Upper Bollinger Band
    df['Upper'] = df['SMA']  + (df['STD'] * 2)
    df['Lower'] = df['SMA']  - (df['STD'] * 2)

    def get_signal(df):
        bollinger_buy_signal = []
        bollinger_sell_signal = []
        
        for i in range(len(df['Close'])):

            if df['Close'][i] > df['Upper'][i]: #Then Sell
                bollinger_buy_signal.append(0)
                bollinger_sell_signal.append(-1)

            elif df['Close'][i] < df['Lower'][i]: # Then Buy
                bollinger_buy_signal.append(1)
                bollinger_sell_signal.append(0)

            else:
                bollinger_buy_signal.append(0)
                bollinger_sell_signal.append(0)

        return (bollinger_buy_signal, bollinger_sell_signal)
    

    df['bollinger_buy_signal']  = get_signal(df)[0]
    df['bollinger_sell_signal'] = get_signal(df)[1]

 
    
    df['bollinger_priceAction'] = ''
    for i in range(1, len(df)):
        if df['bollinger_buy_signal'].iloc[i] == 1:

            df['bollinger_priceAction'].iloc[i] = "Long Position Action Req"

        elif df['bollinger_sell_signal'].iloc[i] == -1:

            df['bollinger_priceAction'].iloc[i] = "Short Position Action Req"

        else:
            df['bollinger_priceAction'].iloc[i] = "No Action Req"


    return df


def mfi_trade_signal(df):

    """
    ------------------------------------------------------------------
    |Output: Function Returns Signals of the  Money Flow Strategy     |
    | --------------------------------------------------------------  |
    |   Input: Dataframe with Pricing value of the stock              |
    |          AVG Price: (Close + High + Low )/3                     |
    |          MFI value:  period = 14 days                           |
    |                                                                 |
    ------------------------------------------------------------------

    """

    #Get all of the positive and negative cash flows
    def get_Cash_flow_ByStock(df, period = 14):

        # print("length of MFI df=", len(df))
        # Calculate the Average Price
        Avg_price = (df['Close'] + df['High'] + df['Low'])/3
        # Calculate the Money Flow
        money_flow = Avg_price * df['Volume']

        positive_cash_flow = []
        negative_cash_flow = []

        # Loop through the typical price
        for i in range(1, len(Avg_price)):
            if (Avg_price[i] > Avg_price[i-1]):
                positive_cash_flow.append(money_flow[i-1])
                negative_cash_flow.append(0)

            elif (Avg_price[i] < Avg_price[i-1]):
                positive_cash_flow.append(0)
                negative_cash_flow.append(money_flow[i-1])

            else:
                positive_cash_flow.append(0)
                negative_cash_flow.append(0)
        # Get all the positive and negative cash flow within the time period

        total_positive_money_flow = []
        total_negative_money_flow = []

        for i in range(period-1, len(positive_cash_flow)):
            total_positive_money_flow.append(sum(positive_cash_flow[i+1-period : i+1])) # 0 to 13 values

        for i in range(period-1, len(negative_cash_flow)):
            total_negative_money_flow.append(sum(negative_cash_flow[i+1-period : i+1]))

        df['MFI'] = ''
        mfi_value = 100 * (np.array(total_positive_money_flow)/(np.array(total_positive_money_flow) + np.array(total_negative_money_flow)))
        df = df[14:]
        df['MFI']  = mfi_value
        return df

    df = get_Cash_flow_ByStock(df, 14)


    def get_trading_buy_sell_signal(df, high_threshold, low_threshold):

        buy_signal = []
        sell_signal = []

        for i in range(len(df['MFI'])):
            if df['MFI'][i] > high_threshold:
                buy_signal.append(0)
                sell_signal.append(-1)

            elif df['MFI'][i] < low_threshold:
                buy_signal.append(1)
                sell_signal.append(0)

            else:
                sell_signal.append(0)
                buy_signal.append(0)


        return buy_signal, sell_signal
    
    df['mfi_Buy_signal'] = get_trading_buy_sell_signal(df, 80,20)[0]
    df['mfi_Sell_signal'] = get_trading_buy_sell_signal(df, 80, 20)[1]

    df['mfi_priceAction'] = ''

    for i in range(1, len(df)):
        if df['mfi_Buy_signal'].iloc[i] == 1:
            df['mfi_priceAction'].iloc[i] = "Long Position Action Req"

        elif df['mfi_Sell_signal'].iloc[i] == -1:
            df['mfi_priceAction'].iloc[i] = "Short Position Action Req"

        else:
            df['mfi_priceAction'].iloc[i] = "No Action Req"

    #print("******************debug signals************")
    #print(df[:30])
    return df


def fab_trade_signal(df):

    """
    ------------------------------------------------------------------
    |Output: Function Returns Signals of the  Fabionacci  Strategy    |
    | --------------------------------------------------------------  |
    |   Input: Dataframe with Pricing value of the stock              |
    |          Short EMA: 12 days                                     |
    |           Long EMA: 30 days                                     |
    |          MACD =   Short EMA -  Long EMA                         |
    |                                                                 |
    ------------------------------------------------------------------

    """

    #Calculate the Fibonacci Retracement Levels
    max_price = df['Close'].max()
    min_price = df['Close'].min()



    difference = max_price - min_price
    first_level = max_price - difference * 0.236 #Fibonacci Ratio
    second_level = max_price - difference * 0.382
    third_level = max_price - difference * 0.5
    fourth_level = max_price - difference * 0.618


    #Calculate the MACD Line and the Signal Line indicators
    #Calculate the short term Exponential Moving Average
    ShortEMA  = df.Close.ewm(span=12, adjust = False).mean()
    #Calculate Long Term Exponential Moving Average
    LongEMA = df.Close.ewm(span=30, adjust=False).mean()
    #Calculate the Moving Average Convergance and Divergence (MACD)
    MACD = ShortEMA - LongEMA
    signal_line = MACD.ewm(span=10, adjust=False).mean()

    df['MACD'] = MACD
    df['Signal line'] = signal_line

    #Create a Function to get upper Fibonacci level and lower Fibonnaci level
    def getLevels(price):
        if price > first_level:
            return(max_price, first_level)
        elif price >= second_level:
            return(first_level, second_level)
        elif price >= third_level:
            return(second_level, third_level)
        elif price >= fourth_level:
            return(third_level, fourth_level)
        else:
            return(fourth_level, min_price)
        
    def buy_sell_strategy(df):

        buy_list = []
        sell_list = []
        flag = 0
        last_buy_price = 0

        # Loop through the dataset
        for i in range(0, df.shape[0]):
            price = df['Close'][i]
            # if this is the first data point within the dataset then get the level above and below it
            if i==0:
                upper_level, lower_level = getLevels(price)
                buy_list.append(0)
                sell_list.append(0)
                # Else if the current price >= upper level or <= lower_level then price has hit or crossed a new Fibonacci level
            elif price >= upper_level or price <= lower_level:
                #Check the MACD and Signal line
                if df['Signal line'][i] > df['MACD'][i] and flag ==0:
                    last_buy_price = price
                    buy_list.append(1)
                    sell_list.append(0)
                    # Set the Flag to 1 to signal that the share was bought
                    flag = 1
                    # Set the flag=1 to show share was bought
                elif df['Signal line'][i] < df['MACD'][i] and flag==1 and price > last_buy_price:
                    buy_list.append(0)
                    sell_list.append(-1)
                    # Set the flag = 0 to signal that the share was sold
                else:
                    buy_list.append(0)
                    sell_list.append(0)
            else:
                buy_list.append(0)
                sell_list.append(0)

            #Update the new levels
            upper_level, lower_level = getLevels(price)
        return buy_list, sell_list
    
    # Create buy and sell columns
    buy, sell = buy_sell_strategy(df)

    df['fab_buy_signal'] = buy
    df['fab_sell_signal'] = sell
    df['fab_priceAction'] = ''

    for i in range(1, len(df)):
        if df['fab_buy_signal'].iloc[i] > 0:
            df['fab_priceAction'].iloc[i] = "Long Position Action Req"

        elif df['fab_sell_signal'].iloc[i] > 0:
            df['fab_priceAction'].iloc[i] = "Short Position Action Req"

        else:
            df['fab_priceAction'].iloc[i] = "No Action Req"
    
    # print("***************Fabionacci dataframe************")
    # print(df)

    return df


# def strategy_table_real_time_df(df, table_cols, company_ticker):
#     table_df = pd.DataFrame()

#     if df.index.inferred_type == 'datetime64':
#         ADD_DATE_INDEX = True
#     else:
#         ADD_DATE_INDEX = False
        
#     for idx, row in df.iterrows():
#         temp_data = {
#             'Ticker': company_ticker, 
#             'Strategy_Real_Time_Id': str(uuid4()),
#             'Stock_Id': "" 
#         }
#         if ADD_DATE_INDEX:
#             temp_data['Date'] = idx.strftime("%Y-%m-%d")
#             temp_data['Fin_Year'] = idx.strftime("%Y")
            
        
#         for i in row.keys():
#             if i in table_cols:
#                 col_name = i.replace(' ', '_')
#                 temp_data[col_name] = [row[i]]
#         # print("******** Strategy temp data *************")
#         # print(temp_data)
#         temp_df = pd.DataFrame(temp_data)

#         table_df = pd.concat([table_df, temp_df], ignore_index=True)
        
#     return table_df


def fetch_history_data_alpaca(company_ticker):
    barTime = '1Hour'
    set_date = '2024-03-29'
    set_date = datetime.strptime(set_date, '%Y-%m-%d')
    # lastDate = (datetime.now() - timedelta(days=1)).isoformat()[:10]
    lastDate = (set_date - timedelta(days=1)).isoformat()[:10]
    
    data = alpaca_api.get_bars(company_ticker, barTime, start=lastDate)
    stock_data_df = data.df
    stock_data_df['Ticker'] = company_ticker
    stock_data_df['Date'] = stock_data_df.index
    stock_data_df.rename(columns={'close': 'Close', 'high': 'High', 'low': 'Low', 'volume': 'Volume', 'open': 'Open'}, inplace=True)
    return stock_data_df



def news_events_df(company_ticker):
    news = []
    # Yfinance news
    company = yf.Ticker(company_ticker)
    yfinance_news = company.get_news()

    # select only top 3 news
    for i in range(0, 3):
        try:
            news.append([str(uuid4()), company_ticker, yfinance_news[i]['title'], yfinance_news[i]['link']])
        except:
            pass

    ###############
    # Alpaca news
    alpaca_news = alpaca_api.get_news(company_ticker)
    for i in range(0, 3):
        try:
            news.append([str(uuid4()), company_ticker, alpaca_news[i].headline, alpaca_news[i].url])
        except:
            pass
    
    news_event_df = pd.DataFrame(data=news, columns=['News_Event_Id', 'Ticker', 'Headline', 'Url'])
    return news_event_df



company_tickers = ['A', 'A', 'AA', 'AAPL', 'ABBV', 'ABCB', 'ABR', 'ABT', 'ACN', 'ADI', 'ADP', 'AEP', 'AES', 'AFG', 'AFL', 'AGCO', 'AIT', 'AJG', 'AL', 'ALB', 'ALEX', 'ALGT', 'ALK', 'ALL', 'ALLE', 'AME', 'AMG', 'AMKR', 'AMSF', 'AMT', 'AMZN', 'AON', 'APA', 'APH', 'APLE', 'APOG', 'ARCH', 'ARE', 'ARI', 'AROC', 'ARR', 'ASB', 'ASH', 'ASIX', 'ASTE', 'ATNI', 'ATO', 'ATR', 'AVA', 'AVNT', 'AVT', 'AVY', 'AWR', 'AYI', 'AZTA', 'AZZ', 'B', 'BAC', 'BALL', 'BANR', 'BAX', 'BBY', 'BC', 'BCC', 'BCO', 'BCPC', 'BDX', 'BG', 'BGC', 'BHE', 'BKE', 'BLK', 'BOH', 'BR', 'BRC', 'BRKL', 'BRKR', 'BRO', 'BRX', 'BSIG', 'BTU', 'BWXT', 'BX', 'BXP', 'BYD', 'C', 'CADE', 'CAG', 'CAKE', 'CARR', 'CASH', 'CASY', 'CATY', 'CB', 'CBRL', 'CBT', 'CBU', 'CCI', 'CCK', 'CCOI', 'CDW', 'CF', 'CFFN', 'CG', 'CGNX', 'CHD', 'CHH', 'CHRW', 'CINF', 'CL', 'CLB', 'CLX', 'CMA', 'CMC', 'CMCSA', 'CNMD', 'COF', 'COLM', 'COO', 'COP', 'COR', 'COST', 'COTY', 'CPK', 'CPT', 'CRI', 'CRM', 'CRS', 'CSCO', 'CSGS', 'CSL', 'CTRE', 'CTS', 'CVBF', 'CVI', 'CVS', 'CVX', 'CWEN', 'CWT', 'CXW', 'DCI', 'DE', 'DEI', 'DFS', 'DGX', 'DINO', 'DLX', 'DOC', 'DOW', 'DRI', 'DUK', 'DXCM', 'EA', 'EAT', 'EBAY', 'ECL', 'EFC', 'EG', 'EGP', 'EIX', 'ELME', 'ELV', 'EMN', 'EMR', 'ENOV', 'ENR', 'ENS', 'EPC', 'EPR', 'EPRT', 'EQIX', 'EQT', 'ES', 'ETRN', 'EVR', 'EVTC', 'EWBC', 'EXC', 'EXLS', 'EXP', 'EXPD', 'EXPI', 'EXPO', 'EXR', 'F', 'FAF', 'FANG', 'FAST', 'FBK', 'FBP', 'FCF', 'FCFS', 'FCPT', 'FDX', 'FE', 'FELE', 'FFBC', 'FHB', 'FHI', 'FIS', 'FLO', 'FLS', 'FNB', 'FNF', 'FOX', 'FOXA', 'FR', 'FRT', 'FTV', 'GBCI', 'GD', 'GES', 'GFF', 'GGG', 'GHC', 'GILD', 'GIS', 'GL', 'GLPI', 'GNL', 'GOOG', 'GOOGL', 'GPC', 'GPN', 'GPS', 'GTY', 'GVA', 'GWW', 'H', 'HAFC', 'HAS', 'HASI', 'HAYN', 'HCA', 'HCSG', 'HD', 'HIG', 'HLI', 'HLT', 'HNI', 'HOG', 'HOMB', 'HOPE', 'HPQ', 'HRL', 'HST', 'HTH', 'HUBB', 'HUM', 'HWC', 'HXL', 'IBM', 'IBTX', 'ICE', 'IDCC', 'IEX', 'IFF', 'IIIN', 'IIPR', 'INTC', 'INTU', 'INVH', 'IP', 'IPAR', 'IPG', 'IR', 'IRM', 'IRT', 'ITW', 'J', 'JACK', 'JBHT', 'JBSS', 'JHG', 'JJSF', 'JKHY', 'JNJ', 'JOE', 'JPM', 'KEY', 'KFY', 'KHC', 'KIM', 'KLAC', 'KLIC', 'KMB', 'KNSL', 'KO', 'KREF', 'KRG', 'KW', 'L', 'LEG', 'LFUS', 'LGND', 'LH', 'LII', 'LIN', 'LKFN', 'LKQ', 'LLY', 'LNC', 'LNN', 'LNT', 'LPX', 'LRCX', 'LVS', 'LW', 'LXP', 'LYB', 'LZB', 'MAA', 'MAC', 'MAR', 'MAS', 'MATV', 'MATW', 'MATX', 'MCD', 'MCS', 'MCY', 'MDC', 'MDT', 'MET', 'MKC', 'MKSI', 'MLKN', 'MLM', 'MMC', 'MMM', 'MMS', 'MO', 'MORN', 'MOS', 'MPC', 'MPW', 'MRK', 'MRTN', 'MS', 'MSA', 'MSCI', 'MSFT', 'MTB', 'MU', 'NAVI', 'NBR', 'NDAQ', 'NDSN', 'NEM', 'NFG', 'NHC', 'NI', 'NJR', 'NOC', 'NOG', 'NOV', 'NSA', 'NSP', 'NTAP', 'NUE', 'NUS', 'NWBI', 'NWN', 'NWS', 'NWSA', 'NX', 'NXPI', 'NXRT', 'NYCB', 'NYMT', 'OC', 'ODFL', 'OFG', 'OGE', 'OKE', 'OLN', 'OMC', 'OMI', 'ORA', 'ORCL', 'OTIS', 'OTTR', 'OUT', 'OVV', 'OXM', 'OXY', 'OZK', 'PAHC', 'PANW', 'PATK', 'PAYX', 'PBI', 'PDCO', 'PEG', 'PEP', 'PFBC', 'PGR', 'PH', 'PHM', 'PII', 'PINC', 'PIPR', 'PJT', 'PK', 'PKG', 'PLUS', 'PMT', 'PNC', 'PNFP', 'PNM', 'PNW', 'PPG', 'PPL', 'PR', 'PRGS', 'PRI', 'PRU', 'PSMT', 'PTEN', 'PVH', 'PXD', 'PZZA', 'QCOM', 'R', 'RBC', 'RC', 'RDN', 'REG', 'REX', 'RF', 'RGA', 'RGP', 'RGR', 'RILY', 'RL', 'RNST', 'ROK', 'ROL', 'ROP', 'ROST', 'RPM', 'RTX', 'RVTY', 'RWT', 'RYN', 'SAIC', 'SBRA', 'SBUX', 'SCHL', 'SCHW', 'SCL', 'SEM', 'SFNC', 'SGH', 'SHEN', 'SHO', 'SJM', 'SKT', 'SLB', 'SLGN', 'SLM', 'SMG', 'SMP', 'SNEX', 'SNV', 'SON', 'SPGI', 'SPWR', 'SR', 'SRE', 'STAG', 'STC', 'STRA', 'STX', 'STZ', 'SWK', 'SXC', 'SXI', 'SXT', 'SYF', 'SYK', 'T', 'TAP', 'TDG', 'TECH', 'TEL', 'TER', 'TFC', 'TFX', 'TGT', 'TILE', 'TJX', 'TKR', 'TMP', 'TNL', 'TPR', 'TRMK', 'TSN', 'TT', 'TTEK', 'TWO', 'TXN', 'UCBI', 'UE', 'UFPI', 'UGI', 'UNH', 'UPS', 'USB', 'UVV', 'V', 'VAC', 'VFC', 'VLO', 'VLY', 'VMI', 'VNO', 'VNT', 'VRE', 'VRSK', 'VRTS', 'VTLE', 'VTR', 'VTRS', 'VYX', 'VZ', 'WAB', 'WABC', 'WAFD', 'WBS', 'WDFC', 'WEC', 'WELL', 'WERN', 'WGO', 'WH', 'WKC', 'WM', 'WMT', 'WNC', 'WOLF', 'WPC', 'WRK', 'WSFS', 'WSO', 'WTRG', 'WTS', 'WWD', 'WYNN', 'XOM', 'XPO', 'XYL', 'YUM', 'ZBH', 'ZEUS', 'ZION', 'ZTS']


working_tickers = []
non_working_tickers = []

for company_ticker in company_tickers:
    try:
        company = yf.Ticker(company_ticker)

        #########################################################################
        ######################### Insert daily_price Data #######################
        #########################################################################
        
        df = company.history(period="10y", interval="1d")
        df_cols = list(df.columns)
        table_name = 'daily_price'
        daily_price_df = stock_table_df(df, df_cols, company)

        daily_price_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in daily_price_df.iterrows()
        ]
        col_name = ', '.join(list(i for i in daily_price_df.columns))
        col_vals = '%s, ' * len(daily_price_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        cursor.executemany(query, daily_price_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()
        
        daily_price_date_list = daily_price_df['Date']
        daily_price_year_indexes = find_last_date_indexes(daily_price_date_list)

        #########################################################################
        ######################### Insert balance_sheet Data #####################
        #########################################################################

        # balance sheet
        df = company.balance_sheet
        df = df.T
        df_cols = ['Total Debt',
                    'Common Stock Equity',
                    'Stockholders Equity',
                    'Common Stock',
                    'Current Assets',
                    'Current Liabilities',
                    'Cash And Cash Equivalents']
        table_name = 'balance_sheet'
        balance_sheet_df = balance_sheet_table_df(df, df_cols, company)

        for idx, row in balance_sheet_df.iterrows():
            date = datetime.strptime(row['Date'], "%Y-%m-%d")
            year = date.year
            if year in daily_price_year_indexes.keys():
                req_idx = daily_price_year_indexes[year][1]
                balance_sheet_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']

        balance_sheet_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in balance_sheet_df.iterrows()
        ]

        col_name = ', '.join(list(i for i in balance_sheet_df.columns))
        col_vals = '%s, ' * len(balance_sheet_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        cursor.executemany(query, balance_sheet_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()

        #########################################################################
        ######################### Insert income_data Data #######################
        #########################################################################

        # Income data
        df = company.income_stmt
        df = df.T
        df_cols = [
            'Net Interest Income', 
            'Interest Expense', 
            'Interest Income',
            'Total Expenses', 
            'Basic EPS', 
            'Net Income',
            'Operating Income', 
            'Operating Expense',
            'Gross Profit',
            'Total Revenue'
        ]
        table_name = 'income_data'
        Income_data_df = income_data_table_df(df, df_cols, company)

        for idx, row in Income_data_df.iterrows():
            date = datetime.strptime(row['Date'], "%Y-%m-%d")
            year = date.year
            if year in daily_price_year_indexes.keys():
                req_idx = daily_price_year_indexes[year][1]
                Income_data_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']

        Income_data_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in Income_data_df.iterrows()
        ]

        col_name = ', '.join(list(i for i in Income_data_df.columns))
        col_vals = '%s, ' * len(Income_data_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        cursor.executemany(query, Income_data_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()


        #########################################################################
        ######################### Insert cash_flow_data Data ####################
        #########################################################################

        # Cash Flow 
        df = company.cashflow
        df = df.T
        df_cols = [
            'Free Cash Flow',
            'Net Income From Continuing Operations',
            'Cash Dividends Paid', 
            'Common Stock Dividend Paid',
            'Repayment Of Debt',
            'End Cash Position',  
            'Investing Cash Flow',
            'Cash Flow From Continuing Investing Activities',
            'Cash Flow From Continuing Operating Activities' 
        ]
        table_name = 'cash_flow_data'
        Cash_flow_data_df = cash_flow_data_table_df(df, df_cols, company)

        for idx, row in Cash_flow_data_df.iterrows():
            date = datetime.strptime(row['Date'], "%Y-%m-%d")
            year = date.year
            if year in daily_price_year_indexes.keys():
                req_idx = daily_price_year_indexes[year][1]
                Cash_flow_data_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']

        Cash_flow_data_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in Cash_flow_data_df.iterrows()
        ]

        col_name = ', '.join(list(i for i in Cash_flow_data_df.columns))
        col_vals = '%s, ' * len(Cash_flow_data_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        cursor.executemany(query, Cash_flow_data_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()

        #########################################################################
        ######################### Insert dividend_data Data #####################
        #########################################################################

        # Dividend sheet
        df = company.actions
        df['Date'] = df.index
        df_cols = [
            'Dividends',
            'Stock Splits',
                    ]
        table_name = 'dividend_data'
        Dividend_data_df = dividend_data_table_df(df, df_cols, company)

        for idx, row in Dividend_data_df.iterrows():
            date = datetime.strptime(row['Date'], "%Y-%m-%d")
            year = date.year
            if year in daily_price_year_indexes.keys():
                req_idx = daily_price_year_indexes[year][1]
                Dividend_data_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']

        Dividend_data_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in Dividend_data_df.iterrows()
        ]

        col_name = ', '.join(list(i for i in Dividend_data_df.columns))
        col_vals = '%s, ' * len(Dividend_data_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        cursor.executemany(query, Dividend_data_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()

        #########################################################################
        ######################### Insert shareholding_data Data #################
        #########################################################################

        # Shareholding data
        df = company.institutional_holders
        df_cols = [
            'Holder',
            'pctHeld',
            'Shares',
            'Value'
                    ]
        from datetime import date
        table_name = 'shareholding_data'
        Shareholding_data_df = shareholding_data_table_df(df, df_cols, company)

        # Shareholding_data_df['Date'] = date.today().strftime('%Y-%m-%d')
        # print("Shareholder DataFrame")
        # print(Shareholding_data_df)
        # for idx, row in Shareholding_data_df.iterrows():
        #     date = datetime.strptime(row['Date'], "%Y-%m-%d")
        #     year = date.year
        #     if year in daily_price_year_indexes.keys():
        #         req_idx = daily_price_year_indexes[year][1]
        #         Shareholding_data_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']

        Shareholding_data_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in Shareholding_data_df.iterrows()
        ]

        col_name = ', '.join(list(i for i in Shareholding_data_df.columns))
        col_vals = '%s, ' * len(Shareholding_data_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        cursor.executemany(query, Shareholding_data_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()

        #########################################################################
        ######################### Insert stock_returns_summary Data #############
        #########################################################################


        df = agg_Stock_income_cash_data(company_ticker)
        #daily_return, y1_return, y3_return, y5_return, y10_return, y15_return, y20_return = calculate_fundamental_returns_1y_3y_5y_10y_15y_20y(company_ticker)
        daily_return, y1_return, y3_return, y5_return, y10_return, start_date_1_year, start_date_3_year, start_date_5_year, start_date_10_year = calculate_fundamental_returns_1y_3y_5y_10y_15y_20y(company_ticker)

        df['daily_return'] = daily_return
        df['y1_return'] = y1_return
        df['y3_return'] = y3_return
        df['y5_return'] = y5_return
        df['y10_return'] = y10_return
        df['start_date_1_year'] = start_date_1_year
        df['start_date_3_year'] = start_date_3_year
        df['start_date_5_year'] = start_date_5_year
        df['start_date_10_year'] = start_date_10_year
        # print("-----Checking---")
        # print(df['daily_return'])
        # print("-------------Printing df of the Stock agg data------------")
        # print("******Checkpoint for DataFrame***********",df)

        #    df['Date'] = df.index
        df_cols = [
            'daily_return',
            'y1_return',
            'y3_return',
            'y5_return',
            'y10_return',
            'start_date_1_year',
            'start_date_3_year',
            'start_date_5_year',
            'start_date_10_year',
            'Date'
        ]
        table_name = 'stock_returns_summary'
        # print("Company ticker.....", company_ticker)
        Stock_Returns_summary_df = stock_returns_summary_table_df(df, df_cols, company_ticker)

        # remove duplicate entries
        subset_cols = list(Stock_Returns_summary_df.columns)
        subset_cols.remove('Stock_agg_Id')
        Stock_Returns_summary_df.drop_duplicates(subset=subset_cols, inplace=True)

        # print("*********Before Foreign key Insertion Checkpoint ***********")
        # print(Stock_Fundamentals_summary_df)
        for idx, row in Stock_Returns_summary_df.iterrows():
            # print("******************This is Pass ******************", idx)
            date = datetime.strptime(row['Date'], "%Y-%m-%d")
            year = date.year
            if year in daily_price_year_indexes.keys():
                req_idx = daily_price_year_indexes[year][1]
                Stock_Returns_summary_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']
            # print("Print Stock Returns Summary df")
            # print(Stock_Returns_summary_df)
            
            # Add Fin_Year
            Stock_Returns_summary_df.loc[idx, 'Fin_Year'] = date.strftime("%Y")
        Stock_Returns_summary_df_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in Stock_Returns_summary_df.iterrows()
        ]

        col_name = ', '.join(list(i for i in Stock_Returns_summary_df.columns))
        col_vals = '%s, ' * len(Stock_Returns_summary_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""
        # print("******Print Stock Returns tuples ********")
        # print(Stock_Returns_summary_df)

        cursor.executemany(query, Stock_Returns_summary_df_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()


        #########################################################################
        ######################### Insert stock_fundamentals_summary Data ########
        #########################################################################

        df = agg_Stock_income_cash_data(company_ticker)

        SortinoRatio = calculate_fundamental_SortinoRatio(company_ticker, '2023-01-01', '2024-03-01')
        df['SortinoRatio'] = SortinoRatio

        Beta = calculate_fundamental_Beta(company_ticker, '2023-01-01', '2024-03-01')
        df['Beta'] = Beta
        Alpha = calculate_fundamental_alpha(company_ticker, Beta, '2023-01-01', '2024-03-01')
        df['Alpha'] = Alpha
        SharpeRatio = calculate_fundamental_SharpeRatio(company_ticker, '2023-01-01', '2024-03-01', risk_free_rate=0)
        df['SharpeRatio'] = SharpeRatio
        daily_return, cum_return = calculate_fundamental_Returns(company_ticker, '2023-01-01', '2024-03-01')
        df['daily_return'] = daily_return
        df['cum_return'] = cum_return
        # print("-----Checking---")
        # print(df['daily_return'])
        # print("-------------Printing df of the Stock agg data------------")
        # print("******Checkpoint for DataFrame***********",df)

        #    df['Date'] = df.index
        df_cols = [
            'ProfitMargin',
            'DividendYield',
            'BookValue',
            'MarketCap',
            'PERatio',
            'CASH',
            'EnterpriseValue',
            'DividendPayoutRatio',
            'ROE',
            'SortinoRatio',
            'Beta',
            'Alpha',
            'daily_return',
            'cum_return',
            'SharpeRatio',
            'Date'
        ]
        table_name = 'stock_fundamentals_summary'
        # print("Company ticker.....", company_ticker)
        Stock_Fundamentals_summary_df = stock_fundamentals_summary_table_df(df, df_cols, company_ticker)
        # print("*********Before Foreign key Insertion Checkpoint ***********")
        # print(Stock_Fundamentals_summary_df)

        # remove duplicate entries
        subset_cols = list(Stock_Fundamentals_summary_df.columns)
        subset_cols.remove('Stock_agg_Id')
        Stock_Fundamentals_summary_df.drop_duplicates(subset=subset_cols, inplace=True)


        for idx, row in Stock_Fundamentals_summary_df.iterrows():
            # print("******************This is Pass ******************", idx)
            date = datetime.strptime(row['Date'], "%Y-%m-%d")
            year = date.year
            if year in daily_price_year_indexes.keys():
                req_idx = daily_price_year_indexes[year][1]
                Stock_Fundamentals_summary_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']
            # print("Print Stock Fundamental Summary df")
            # print(Stock_Fundamentals_summary_df)
                
            # Add Fin_Year
            Stock_Fundamentals_summary_df.loc[idx, 'Fin_Year'] = date.strftime("%Y")
        Stock_Fundamentals_summary_df_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in Stock_Fundamentals_summary_df.iterrows()
        ]

        col_name = ', '.join(list(i for i in Stock_Fundamentals_summary_df.columns))
        col_vals = '%s, ' * len(Stock_Fundamentals_summary_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""
        # print("******Print Stock Summary tuples ********")

        cursor.executemany(query, Stock_Fundamentals_summary_df_tuples)
        # print(Stock_Fundamentals_summary_df_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()


        #########################################################################
        ######################### Insert stock_technicals_summary Data ##########
        #########################################################################

        stock_data_tech_df = pd.DataFrame()
        stock_data_df = fetch_history_data(company_ticker, '2023-01-01', '2024-03-01')
        #stock_data_df['Ticker'] = company
        stock_data_tech_df = pd.concat([stock_data_tech_df, stock_data_df])
        rsi = calculate_rsi(stock_data_tech_df['Close'], period=14)
        stock_data_tech_df['RSI'] = rsi
        #print("Checking for Technicals.......")
        #print(stock_data_tech_df)
        stock_data_tech_df['overbought_signal'] = check_overbought_rsi_indicator(stock_data_tech_df)
        stock_data_tech_df["oversold_signal"]   = check_oversold_rsi_indicator(stock_data_tech_df)
        stock_data_tech_df["golden_cross_signal"] =  Golden_Cross(stock_data_tech_df)


        stock_data_tech_df['Date'] = stock_data_tech_df.index

        df_cols = [
            'RSI',
            'overbought_signal',
            'oversold_signal',
            'golden_cross_signal'
            ]
        table_name = 'stock_technicals_summary'
        Stock_Technicals_summary_df = stock_technicals_summary_table_df(stock_data_tech_df, df_cols, company_ticker)

        for idx, row in Stock_Technicals_summary_df.iterrows():
            date = datetime.strptime(row['Date'], "%Y-%m-%d")
            year = date.year
            if year in daily_price_year_indexes.keys():
                req_idx = daily_price_year_indexes[year][1]
                Stock_Technicals_summary_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']

        Stock_Technicals_summary_df_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in Stock_Technicals_summary_df.iterrows()
        ]
        Stock_Technicals_summary_df_tuples = Stock_Technicals_summary_df_tuples[-1]
        col_name = ', '.join(list(i for i in Stock_Technicals_summary_df.columns))
        col_vals = '%s, ' * len(Stock_Technicals_summary_df.columns)
        col_vals = col_vals[:-2]

        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        cursor.execute(query, Stock_Technicals_summary_df_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()


        #########################################################################
        ######################### Insert strategy Data ##########################
        #########################################################################

        ''' This Logic is for the Insertion of the Strategies Indicators in the Daily Strategies Summary Tabel::'''

        stock_data_tech_df = pd.DataFrame()
        stock_data_df = fetch_history_data(company_ticker, '2023-01-01', '2024-03-01')
        stock_data_df['Ticker'] = company_ticker
        stock_data_tech_df = pd.concat([stock_data_tech_df, stock_data_df])


        stock_data_tech_df['Date'] = stock_data_tech_df.index
        stock_data_tech_df = rsi_trading_signals(stock_data_tech_df)
        stock_data_tech_df = bollinger_trade_signals(stock_data_tech_df)
        stock_data_tech_df = mfi_trade_signal(stock_data_tech_df)
        stock_data_tech_df = fab_trade_signal(stock_data_tech_df)
        #print("********** Checking for the df of Strategies ************")


        df_cols = [
            'rsi_signal_buy',
            'rsi_signal_sell',
            'rsi_PriceAction',
            'bollinger_buy_signal',
            'bollinger_sell_signal',
            'bollinger_priceAction',
            'mfi_Buy_signal',
            'mfi_Sell_signal',
            'mfi_priceAction',
            'fab_buy_signal',
            'fab_sell_signal',
            'fab_priceAction'
        ]


        table_name = 'strategy'
        Strategies_df = strategy_table_df(stock_data_tech_df, df_cols, company_ticker)
        # print("Insertion of strategies data....")
        # print(Strategies_df[:25])
        for idx, row in Strategies_df.iterrows():
            date = datetime.strptime(row['Date'], "%Y-%m-%d")
            year = date.year
            if year in daily_price_year_indexes.keys():
                req_idx = daily_price_year_indexes[year][1]
                Strategies_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']

        # newly added code
        Strategies_df.fillna(value=0, inplace=True)
        # newly added code

        Strategies_df_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in Strategies_df.iterrows()
        ]

        col_name = ', '.join(list(i for i in Strategies_df.columns))
        col_vals = '%s, ' * len(Strategies_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        cursor.executemany(query, Strategies_df_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()


        # #########################################################################
        # ##################### Insert strategy_real_time Data ####################
        # #########################################################################
            
        # ''' This Logic is for the Insertion of the Strategies Indicators in the Strategies Real Time Table:'''

        # intra_day_df = fetch_history_data_alpaca(company_ticker)
        # intra_day_df['Ticker'] = company_ticker

        # # print("********** Checking for the df of Strategies ************")
        # # print(intra_day_df)
        # intra_day_df = rsi_trading_signals(intra_day_df)
        # # fillna  values with 0
        # intra_day_df.fillna(value=0, inplace=True)
        # df_cols = [
        #     'rsi_signal_buy',
        #     'rsi_signal_sell',
        #     'rsi_PriceAction'
        #     #'bollinger_buy_signal',
        #     #'bollinger_Sell_sginal',
        #     #'mfi_buy_signal',
        #     #'mfi_sell_signal',
        #     #'rsi_PriceAction',
        #     #'bollinger_PriceAction',
        #     #'mfi_PriceAction',
        #     #'fabionacci_PriceAction'
        #     ]
        # table_name = 'strategy_real_time'
        # Strategies_real_time_df = strategy_table_real_time_df(intra_day_df, df_cols, company_ticker)

        # # remove duplicate entries
        # subset_cols = list(Strategies_real_time_df.columns)
        # subset_cols.remove('Strategy_Real_Time_Id')
        # Strategies_real_time_df.drop_duplicates(subset=subset_cols, inplace=True)


        # for idx, row in Strategies_real_time_df.iterrows():
        #     date = datetime.strptime(row['Date'], "%Y-%m-%d")
        #     year = date.year
        #     if year in daily_price_year_indexes.keys():
        #         req_idx = daily_price_year_indexes[year][1]
        #         Strategies_real_time_df.loc[idx, 'Stock_Id'] = daily_price_df.loc[req_idx, 'Stock_Id']

        # Strategies_real_time_df_tuples = [
        #     tuple(row[i] for i in row.keys())
        #     for idx, row in Strategies_real_time_df.iterrows()
        # ]

        # col_name = ', '.join(list(i for i in Strategies_real_time_df.columns))
        # col_vals = '%s, ' * len(Strategies_real_time_df.columns)
        # col_vals = col_vals[:-2]
        # query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        # cursor.executemany(query, Strategies_real_time_df_tuples)
        # print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        # conn.commit()
        

        #########################################################################
        ##################### Insert news_events Data ####################
        #########################################################################

        table_name = 'news_events'
        news_event_df = news_events_df(company_ticker)
        col_name = ', '.join(list(i for i in news_event_df.columns))
        col_vals = '%s, ' * len(news_event_df.columns)
        col_vals = col_vals[:-2]
        query = f"""INSERT INTO {table_name} ({col_name}) VALUES ({col_vals})"""

        news_event_df_tuples = [
            tuple(row[i] for i in row.keys())
            for idx, row in news_event_df.iterrows()
        ]

        cursor.executemany(query, news_event_df_tuples)
        print(f'Inserted {cursor.rowcount} records to the table {table_name}')
        conn.commit()


        working_tickers.append(company_ticker)
    except:
        non_working_tickers.append(company_ticker)
        print(f"{company_ticker}::: Not Working")





