# stock_predictor


from bs4 import BeautifulSoup
import requests
import time
import re
import json
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt


def scrape_page(resp=False):
    url = 'https://au.finance.yahoo.com/markets/world-indices/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table')
    data = []

    if not table:
        print("Table not found!")
    else:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if cols:
                index_link_tag = cols[0].find('a')
                if index_link_tag:
                    index_name = index_link_tag.text.strip()
                    last_price = cols[1].text.strip()
                    change = cols[2].text.strip()
                    percent_change = cols[3].text.strip()


                    data.append({
                        "index": index_name,
                        "last_price": last_price,
                        "change": change,
                        "percent_change": percent_change,
                    })

    if resp:
        return data
    else:
        print(json.dumps(data, indent=2))


def get_article_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        image_tag = soup.find("meta", property="og:image")
        image_url = image_tag["content"] if image_tag and image_tag.get("content") else None

        paragraphs = soup.find_all('p')
        full_text = "\n\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())

        stop_phrases = [
            "recommended reading",
            "related articles"
        ]
        for stop in stop_phrases:
            if stop in full_text.lower():
                split_point = full_text.lower().index(stop)
                full_text = full_text[:split_point]
                break

        blacklist_phrases = [
            "sign in",
            "subscribe",
            "newsletter",
            "oops, something went wrong",
            "get the app",
            "read full article",
            "share this article",
            "comment",
            "privacy policy",
            "cookies",
            "login"
        ]

        cleaned_paragraphs = [
            para for para in full_text.split('\n\n')
            if not any(bad in para.lower() for bad in blacklist_phrases)
        ]

        cleaned_text = "\n\n".join(cleaned_paragraphs)
        cleaned_text = cleaned_text if cleaned_text else "No meaningful content found."

        return {
            "content": cleaned_text,
            "image_url": image_url
        }

    except Exception as e:
        return {
            "content": f"Error fetching article: {str(e)}",
            "image_url": None
        }


def get_news(stock_code):
    symbol = "^" + stock_code
    search_result = yf.Search(symbol, news_count=5)
    news_data = []

    for article in search_result.news:
        title = article.get('title', 'No Title')
        publisher = article.get('publisher', 'Unknown')
        link = article.get('link', '#')
        timestamp = article.get('providerPublishTime', 0)

        time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else "Unknown"

        article_text = get_article_text(link)

        news_data.append({
            "title": title,
            "publisher": publisher,
            "link": link,
            "published": time_str,
            "content": article_text
        })

    return news_data


def get_graphs_data(stock_code, time_period):
    ticker_symbol = '^'+stock_code
    ticker_data = yf.Ticker(ticker_symbol)
    historical_data = ticker_data.history(period=time_period, interval="1m")
    print(historical_data)

 all this code is in one file data_fetch  can you create a fast api code to get all the data in index.py i wan to create different apis for each function that returns some data but before that 