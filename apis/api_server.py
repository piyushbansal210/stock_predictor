from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uvicorn
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_fetch import scrape_page, get_news, get_graphs_data, compare_with_previous_hour, stats

app = FastAPI(
    title="Stock Market Data API",
    description="APIs for world indices, news, and historical graph data",
    version="1.0"
)

class NewsRequest(BaseModel):
    stock_code: str

class GraphRequest(BaseModel):
    stock_code: str
    time_period: str



@app.get("/indices", summary="World Indices Data")
def get_indices():
    try:
        data = scrape_page(resp=True)
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/news", summary="Latest News for Stock (via query param)")
def get_news_api(stock_code: str):
    """
    Pass stock_code in the URL like: /news?stock_code=AXJO
    """
    try:
        news = get_news(stock_code)
        return {"status": "success", "data": news}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.get("/stats", summary="Latest News for Stock (via query param)")
def get_news_api(stock_code: str):
    """
    Pass stock_code in the URL like: /news?stock_code=AXJO
    """
    try:
        news = stats(stock_code)
        return {"status": "success", "data": news}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/graph", summary="Graph Data for Stock (via query params)")
def get_graph_api(
    stock_code: str = Query(..., description="Stock index code, e.g. AXJO"),
    time_period: str = Query(..., description="Time period like 1d, 5d, 1mo, 6mo, 1y, max")
):
    """
    Returns historical graph data for the given stock code and time period.
    """
    try:
        graph = get_graphs_data(stock_code, time_period)
        return {"status": "success", "data": graph}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

    

@app.get("/compare/hour", summary="Compare market movement from the past hour")
def compare_hour_api():
    """
    Compares each index's current price with its value from 1 hour ago.
    Returns a list of significant changes.
    """
    try:
        results = compare_with_previous_hour()
        return {"status": "success", "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)

