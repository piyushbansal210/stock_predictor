from bs4 import BeautifulSoup
import requests
import time
import re
import json
import yfinance as yf
from datetime import datetime
import matplotlib.pyplot as plt


def scrape_page(resp=False):
    try:
        url = 'https://au.finance.yahoo.com/markets/stocks/most-active/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
        }

        response = requests.get(url, headers=headers, timeout=10)
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
                    try:
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
                    except Exception as inner_err:
                        print(f"Row parsing error: {inner_err}")
        
        if resp:
            return data
        else:
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error in scrape_page: {e}")
        return []


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
    news_data = []
    try:
        symbol = "^" + stock_code
        search_result = yf.Search(symbol, news_count=20)

        for article in search_result.news:
            try:
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
            except Exception as article_err:
                print(f"Error processing article: {article_err}")
                continue
    except Exception as e:
        print(f"Error in get_news: {e}")
    
    return news_data


def get_graphs_data(stock_code, time_period):
    graph_data = []
    try:
        ticker_symbol = '^' + stock_code
        ticker_data = yf.Ticker(ticker_symbol)

        interval = "1d"  # default
        if time_period == "1d":
            interval = "1h"
        elif time_period in ["2d", "5d", "7d", "10d", "30d"]:
            interval = "1h"
        elif time_period in ["1mo", "3mo", "6mo"]:
            interval = "1d"
        elif time_period in ["1y"]:
            interval = "1wk"
        elif time_period in ["2y", "5y", "10y", "max"]:
            interval = "1mo"

        historical_data = ticker_data.history(period=time_period, interval=interval)

        for timestamp, row in historical_data.iterrows():
            graph_data.append({
                "time": timestamp.strftime('%Y-%m-%d %H:%M'),
                "price": round(row["Close"], 2) if not row["Close"] != row["Close"] else None
            })

    except Exception as e:
        print(f"Error in get_graphs_data for {stock_code}: {e}")
    
    return graph_data

def stats(stock_code):

    ticker = yf.Ticker("^"+stock_code) 
    info = ticker.info

    print(info)

    return info

    # # Example: Access some key stats
    # print("Company Name:", info.get("longName"))
    # print("Market Cap:", info.get("marketCap"))
    # print("PE Ratio:", info.get("trailingPE"))
    # print("52 Week High:", info.get("fiftyTwoWeekHigh"))
    # print("Dividend Yield:", info.get("dividendYield"))

def compare_with_previous_hour():
    """
    Compares index prices now vs. 1 hour ago using yfinance intraday data.
    Returns significant market movement messages.
    """
    try:
        print("📦 Getting current stock index data...")
        current_data = scrape_page(resp=True)
        movements = []

        for item in current_data:
            print(item)
            index_name = item["index"]
            symbol_path =  index_name.split()[0]  # Ensure proper ticker format

            try:
                ticker = yf.Ticker(symbol_path)
                hist = ticker.history(period="1d", interval="1m")

                if hist.empty or len(hist) < 61:
                    continue  # Need at least 1 hour of minute-level data

                old_price = hist["Close"].iloc[-61]  # ~1 hour ago
                current_price = hist["Close"].iloc[-1]

                print(f"{index_name} | 1h Ago: {old_price} → Now: {current_price}")

                change = current_price - old_price
                percent_change = (change / old_price) * 100

                if abs(percent_change) < 0.2:
                    continue

                if percent_change > 2:
                    status = f"🚀 {index_name} is skyrocketing right now! (+{percent_change:.2f}%)"
                elif percent_change > 0.2:
                    status = f"🔼 {index_name} is trending up (+{percent_change:.2f}%)"
                elif percent_change < -2:
                    status = f"💥 {index_name} is crashing fast! ({percent_change:.2f}%)"
                else:
                    status = f"🔻 {index_name} is dropping slightly ({percent_change:.2f}%)"

                movements.append({
                    "index": index_name,
                    "old_price": round(old_price, 2),
                    "current_price": round(current_price, 2),
                    "percent_change": round(percent_change, 2),
                    "message": status
                })

            except Exception:
                continue

        if not movements:
            return [{"message": "😐 No major change in the market over the past hour."}]
        
        return movements

    except Exception as e:
        return [{"message": f"Error occurred: {str(e)}"}]

