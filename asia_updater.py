import json
import time
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

def get_asia_tickers():
    try:
        # Fetching real global/Asia tickers from a working GitHub raw CSV
        url = "https://gist.githubusercontent.com/yepster1/b90404149664f954c3ae/raw/stocks.csv"
        df = pd.read_csv(url, on_bad_lines='skip')
        
        if 'Symbols' in df.columns:
            raw_tickers = df['Symbols'].dropna().astype(str).tolist()
        else:
            raw_tickers = df.iloc[:, 0].dropna().astype(str).tolist()

        asia_tickers = []
        asia_suffixes = ['.AX', '.HK', '.T', '.KS', '.NS', '.BO']
        
        for ticker in raw_tickers:
            clean_ticker = ticker.strip()
            if any(clean_ticker.endswith(suffix) for suffix in asia_suffixes):
                asia_tickers.append(clean_ticker)
                
        print(f"Successfully loaded {len(asia_tickers)} Asia-Pacific tickers.")
        
        if len(asia_tickers) < 10:
             return asia_tickers + ["7203.T", "6758.T", "9984.T", "0700.HK", "9988.HK", "RELIANCE.NS"]
        return asia_tickers
    except Exception as e:
        print(f"Error fetching Asia tickers: {e}")
        # Fallback list in case of network issues
        return [
            "7203.T", "6758.T", "9984.T", "0700.HK", "9988.HK", 
            "0941.HK", "RELIANCE.NS", "TCS.NS", "INFY.NS", 
            "005930.KS", "000660.KS", "1810.HK", "3690.HK"
        ]

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

        if total_assets == 0 or total_revenue == 0:
            return None

        debt_ratio = (total_debt / total_assets) * 100
        cash_ratio = (total_cash_investments / total_assets) * 100
        income_ratio = (interest_income / total_revenue) * 100

        debt_pass = bool(debt_ratio < 33.0)
        cash_pass = bool(cash_ratio < 33.0)
        income_pass = bool(income_ratio < 5.0)

        if debt_pass and cash_pass and income_pass:
            status = "HALAL"
        elif not debt_pass and not cash_pass and not income_pass:
            status = "HARAM"
        else:
            status = "DOUBTFUL"

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

def update_asia_stocks():
    tickers = get_asia_tickers()
    stock_data = []

    for ticker in tickers:
        print(f"Processing {ticker}...")
        result = check_shariah_compliance(ticker)
        if result:
            stock_data.append(result)
        time.sleep(1)

    with open('asia_data.json', 'w') as f:
        json.dump(stock_data, f, indent=4, cls=NumpyEncoder)
    print(f"Data saved: {len(stock_data)} Asia stocks.")

if __name__ == "__main__":
    update_asia_stocks()
