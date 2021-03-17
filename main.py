import time
import datetime
import calendar

import pandas as pd
import pandas_datareader.data as pdr
import yfinance as fix
import matplotlib.pyplot as plt

fix.pdr_override()

import holidays

ONE_DAY = datetime.timedelta(days=1)
HOLIDAYS_US = holidays.US()


def next_business_day(date):
    next_day = date + ONE_DAY
    while next_day.weekday() in holidays.WEEKEND or next_day in HOLIDAYS_US:
        next_day += ONE_DAY
    return next_day


def get_stock_data(ticker, start_date, end_date):
    """
    Gets historical stock data of given tickers between dates
    :param ticker: company, or companies whose data is to fetched
    :type ticker: string or list of strings
    :param start_date: starting date for stock prices
    :type start_date: string of date "YYYY-mm-dd"
    :param end_date: end date for stock prices
    :type end_date: string of date "YYYY-mm-dd"
    :return: stock_data.csv
    """
    i = 1
    try:
        all_data = pdr.get_data_yahoo(ticker, start_date, end_date)
    except ValueError:
        print("ValueError, trying again")
        i += 1
        if i < 5:
            time.sleep(10)
            get_stock_data(ticker, start_date, end_date)
        else:
            print("Tried 5 times, Yahoo error. Trying after 2 minutes")
            time.sleep(120)
            get_stock_data(ticker, start_date, end_date)
    stock_data = all_data["Adj Close"]
    stock_data.to_csv("stock_prices.csv")


def get_sp500(start_date, end_date):
    """
    Gets sp500 price data
    :param start_date: starting date for sp500 prices
    :type start_date: string of date "Y-m-d"
    :param end_date: end date for sp500 prices
    :type end_date: string of date "Y-m-d"
    :return: sp500_data.csv
    """
    sp500_all_data = pdr.get_data_yahoo("^GSPC", start_date, end_date)
    sp500_data = sp500_all_data["Adj Close"]
    sp500_data.to_csv("sp500_data.csv")


def invest_at_first(initial_investment=1, monthly_contributions=1):
    """
    Invest at first of month
    """
    invests_and_dates = pd.DataFrame(columns=["Date", "Cumulative", "Invest"])
    cumulative = initial_investment
    sp500_data = pd.read_csv("sp500_data.csv")

    # Initial close
    previous_close = sp500_data["Adj Close"][0]
    months_closes = [previous_close]

    for i, data in sp500_data.iterrows():

        # Get the current close
        current_close = data["Adj Close"]
        d = datetime.datetime.strptime(data["Date"], "%Y-%m-%d")

        cumulative *= current_close / previous_close

        # Invest on the last day of the month
        if d.month != next_business_day(d).month:
            cumulative += monthly_contributions
            months_closes = []
            invests_and_dates = invests_and_dates.append({"Date": d, "Cumulative": cumulative, "Invest": True},
                                     ignore_index=True)
        else:
            invests_and_dates = invests_and_dates.append({"Date": d, "Cumulative": cumulative, "Invest": False},
                                     ignore_index=True)

        months_closes.append(current_close)
        previous_close = current_close

    plot_data = pd.Series(data=list(invests_and_dates["Cumulative"]), index=invests_and_dates["Date"])

    plot_data.plot(title="Regular", markevery=list(invests_and_dates[invests_and_dates["Invest"] == True].index), marker='o', markerfacecolor='r')
    return cumulative


def invest_at_secretary(initial_investment=1, monthly_contributions=1):
    """
    We reject every day until 11 of the month and invest in the worst day since,
    or on the last day of the month because we must only if we haven't invested before
    """
    invests_and_dates = pd.DataFrame(columns=["Date", "Cumulative", "Invest"])
    cumulative = initial_investment
    sp500_data = pd.read_csv("sp500_data.csv")

    # Initial close
    previous_close = sp500_data["Adj Close"][0]
    months_closes = [previous_close]
    did_invest = False

    for i, data in sp500_data.iterrows():

        # Get the current close
        current_close = data["Adj Close"]
        d = datetime.datetime.strptime(data["Date"], "%Y-%m-%d")

        cumulative *= current_close / previous_close

        if ((d.day > 11 and current_close < min(months_closes)) or
            d.month != next_business_day(d).month) and not did_invest:
            cumulative += monthly_contributions
            did_invest = True
            invests_and_dates = invests_and_dates.append({"Date": d, "Cumulative": cumulative, "Invest": True},
                                     ignore_index=True)
        else:
            invests_and_dates = invests_and_dates.append({"Date": d, "Cumulative": cumulative, "Invest": False},
                                     ignore_index=True)

        # Reset the month when we get to the next month
        if d.month != next_business_day(d).month:
            months_closes = []
            did_invest = False

        months_closes.append(current_close)
        previous_close = current_close

    plot_data = pd.Series(data=list(invests_and_dates["Cumulative"]), index=invests_and_dates["Date"])

    plot_data.plot(title="Secretary", markevery=list(invests_and_dates[invests_and_dates["Invest"] == True].index), marker='o', markerfacecolor='r')
    return cumulative


def main():
    """
    Parse S&P500 and get:
    1. Reject 1/e of the first days of the month (basically first 11 days)
    2. Put 1 USD$ in the next worst day than those before
    3. Repeat

    Compare to revenue after the period at first of each month
    """
    # sp500_data = get_sp500(datetime.datetime.fromtimestamp(0), datetime.datetime.now())
    plt.figure(1)
    print(invest_at_secretary())
    plt.figure(2)
    print(invest_at_first())
    plt.show()


if __name__ == '__main__':
    main()
