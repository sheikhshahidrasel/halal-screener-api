import json
import time
import random
import requests
import yfinance as yf
import pandas as pd
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if type(obj) == type:
            return str(obj)
        return super(NumpyEncoder, self).default(obj)

def get_us_tickers():
    try:
        # Fetching US tickers directly from the SEC official API
        headers = {'User-Agent': 'HalalScreenerApp (contact@example.com)'}
        url = "https://www.sec.gov/files/company_tickers.json"
        
        response = requests.get(url, headers=headers)
        data = response.json()
        
        tickers = []
        for key in data:
            tickers.append(data[key]['ticker'])
            
        # Remove duplicate tickers
        unique_tickers = list(set(tickers))
        print(f"Successfully loaded {len(unique_tickers)} US tickers from SEC.")
        
        return unique_tickers
        
    except Exception as e:
        print(f"Error fetching SEC tickers: {e}")
        # Fallback list in case of network issues
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "ORCL"]

def check_shariah_compliance(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('shortName', ticker)
        sector = info.get('sector', 'Unknown')

        bs = stock.balance_sheet
        fin = stock.financials

        if bs.empty or fin.empty:
            return None

        try:
            total_assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else 0
            total_debt = bs.loc['Total Debt'].iloc[0] if 'Total Debt' in bs.index else 0
            
            cash = bs.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in bs.index else 0
            short_term_investments = bs.loc['Other Short Term Investments'].iloc[0] if 'Other Short Term Investments' in bs.index else 0
            total_cash_investments = cash + short_term_investments

            total_revenue = fin.loc['Total Revenue'].iloc[0] if 'Total Revenue' in fin.index else 0
            interest_income = fin.loc['Interest Income'].iloc[0] if 'Interest Income' in fin.index else 0
        except KeyError:
            return None

        # Handle missing essential data by marking as DOUBTFUL
        if total_assets == 0 or total_revenue == 0:
            return {
                "ticker": ticker,
                "name": name,
                "sector": sector,
                "status": "DOUBTFUL",
                "report": {
                    "debt_ratio": 0.0,
                    "cash_ratio": 0.0,
                    "income_ratio": 0.0,
                    "debt_pass": False,
                    "cash_pass": False,
                    "income_pass": False
                }
            }

        debt_ratio = (total_debt / total_assets) * 100
        cash_ratio = (total_cash_investments / total_assets) * 100
        income_ratio = (interest_income / total_revenue) * 100

        debt_pass = bool(debt_ratio < 33.0)
        cash_pass = bool(cash_ratio < 33.0)
        income_pass = bool(income_ratio < 5.0)

        # Fixed Shariah Logic (AAOIFI Standard)
        if debt_pass and cash_pass and income_pass:
            status = "HALAL"
        else:
            # If ANY of the 3 conditions fail, the stock is HARAM
            status = "HARAM"

        return {
            "ticker": ticker,
            "name": name,
            "sector": sector,
            "status": status,
            "report": {
                "debt_ratio": round(float(debt_ratio), 2),
                "cash_ratio": round(float(cash_ratio), 2),
                "income_ratio": round(float(income_ratio), 2),
                "debt_pass": debt_pass,
                "cash_pass": cash_pass,
                "income_pass": income_pass
            }
        }
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None

def update_us_stocks_part_1():
    tickers = get_us_tickers()
    
    # SLICING LOGIC: Take only the FIRST HALF of the tickers
    mid_point = len(tickers) // 2
    tickers_part_1 = tickers[:mid_point]
    
    print(f"Processing US Part 1: {len(tickers_part_1)} tickers...")
    
    stock_data = []

    for ticker in tickers_part_1:
        print(f"Processing {ticker}...")
        result = check_shariah_compliance(ticker)
        if result:
            stock_data.append(result)
        
        # Anti-ban randomized sleep to prevent GitHub Actions IP block from yfinance
        time.sleep(random.uniform(1.0, 2.5))

    # Save to a specific file for Part 1
    with open('us_data_1.json', 'w') as f:
        json.dump(stock_data, f, indent=4, cls=NumpyEncoder)
        
    print(f"Data saved: {len(stock_data)} US stocks saved to us_data_1.json.")

if __name__ == "__main__":
    update_us_stocks_part_1()
