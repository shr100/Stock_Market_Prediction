import re
import csv
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import warnings

warnings.filterwarnings("ignore")


def prep_input_data():
    with open('stock_list.csv', 'r') as file:
        input_stock_list = csv.reader(file)
        stock_list = []
        for item in input_stock_list:
            if bool(re.match(r'[A-Z]+\^', item[0])):
                match = re.findall(r'[A-Z]+', item[0])
                if match[0] not in stock_list:
                    stock_list.append(match[0])
            else:
                if item[0] not in stock_list:
                    stock_list.append(item[0])
    return stock_list


def web_scraper(ticker):
    column_names = ['Ticker']

    # Request to website and download HTML contents
    url = f'https://finance.yahoo.com/quote/{ticker[0]}/history'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'close'
    }
    req = requests.get(url, headers=headers)
    # Beautiful Soup to parse the content of the website
    soup = BeautifulSoup(req.content, 'html.parser')

    table = soup.find('table', class_='W(100%)')

    for row in table.tbody.find_all('tr'):
        columns = row.find_all('td')
        if (columns != []):
            x = datetime.strftime(datetime.strptime(columns[0].text, '%b %d, %Y'), '%d-%m-%Y')
            if x not in column_names:
                column_names.append(x)

    df = pd.DataFrame(columns=column_names)

    for i, item in enumerate(ticker):
        # Request to website and download HTML contents
        url = f'https://finance.yahoo.com/quote/{item}/history'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'close'
        }
        req = requests.get(url, headers = headers, timeout=5)
        if req.status_code != 200:
            continue
        # Beautiful Soup to parse the content of the website
        soup = BeautifulSoup(req.content, 'html.parser')

        new_row = {'Ticker': item}

        table = soup.find('table', class_='W(100%)')
        for row in table.tbody.find_all('tr'):
            columns = row.find_all('td')
            if (columns!=[]):
                try:
                    x = datetime.strftime(datetime.strptime(columns[0].text, '%b %d, %Y'), '%d-%m-%Y')
                    try:
                        new_row[x] = float(columns[1].text)
                    except ValueError:
                        continue
                except ValueError:
                    pass

        df = df.append(new_row, ignore_index=True)
    df.to_csv('./scraped_data.csv')


def clean_data():
    # Drop rows with more than 50% of values missing
    df = pd.read_csv('scraped_data.csv', header=0, sep=',')

    # Drop the first column of indexes read from the input csv file
    df.drop(columns=df.columns[0], axis=1, inplace=True)
    df.set_index('Ticker', inplace=True)

    print(f'Shape of data before dropping rows = {df.shape}')
    column_count_threshold = df.shape[1]/2

    df['count'] = df.isnull().sum(axis=1)

    for index, row in df.iterrows():
        if row['count'] > column_count_threshold:
            df = df.drop(index)
    df.drop(['count'], axis=1, inplace=True)

    print(f'Shape of data after dropping rows = {df.shape}')

    # Fill empty cells with the mean stock value
    for item in df.index:
        df.loc[item] = df.loc[item].fillna(value=df.loc[item].mean())

    df = df.round(2)
    df.to_csv('./cleaned_data.csv')


def main():
    # To clean list of stocks and remove duplicates
    stock_list = prep_input_data()

    # To scrape the Yahoo finance website for each of the cleaned list of stocks
    web_scraper(stock_list)

    # Clean the scraped data
    clean_data()


main()



