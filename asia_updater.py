import json
import time
import random
import requests
import io
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
    asia_tickers = set()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    # 1. Fetch ALL Indian Stocks directly from Official NSE CSV (~2000+ stocks)
    try:
        print("Fetching official NSE (India) stock list...")
        nse_url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        res = requests.get(nse_url, headers=headers, timeout=15)
        
        if res.status_code == 200:
            df_nse = pd.read_csv(io.StringIO(res.text))
            if 'SYMBOL' in df_nse.columns:
                for symbol in df_nse['SYMBOL'].dropna().astype(str):
                    clean_sym = symbol.strip()
                    if clean_sym != 'SYMBOL':
                        asia_tickers.add(f"{clean_sym}.NS")
            print(f"Successfully loaded Indian tickers from NSE.")
    except Exception as e:
        print(f"Error fetching NSE list: {e}")

    # 2. Wikipedia Major Indices for broader Asian coverage
    wiki_sources = [
        ("https://en.wikipedia.org/wiki/Nikkei_225", "T", False),
        ("https://en.wikipedia.org/wiki/Hang_Seng_Index", "HK", True),
        ("https://en.wikipedia.org/wiki/Straits_Times_Index", "SI", False),
        ("https://en.wikipedia.org/wiki/KOSPI", "KS", False),
        ("https://en.wikipedia.org/wiki/FTSE_Bursa_Malaysia_KLCI", "KL", False),
        ("https://en.wikipedia.org/wiki/IDX_Composite", "JK", False),
        ("https://en.wikipedia.org/wiki/SET50_Index_and_SET100_Index", "BK", False)
    ]
    
    print("Fetching major Asian indices via Wikipedia...")
    for url, suffix, is_hk in wiki_sources:
        try:
            res_wiki = requests.get(url, headers=headers, timeout=10)
            tables = pd.read_html(res_wiki.text)
            for df in tables:
                target_col = None
                for col in df.columns:
                    if any(keyword in str(col).upper() for keyword in ['TICKER', 'SYMBOL', 'CODE']):
                        target_col = col
                        break
                
                if target_col:
                    for val in df[target_col].dropna().astype(str):
                        clean_val = str(val).split()[0].replace('.', '')
                        if is_hk and clean_val.isdigit():
                            clean_val = clean_val.zfill(4)
                        if len(clean_val) > 0 and clean_val.upper() != 'SYMBOL':
                            asia_tickers.add(f"{clean_val}.{suffix}")
                    break
        except Exception as e:
            print(f"Skipping Wiki fetch for {suffix}: {e}")

    # 3. Systematic generation for highly active Asian markets (Japan & HK)
    print("Generating active trading ranges for Japan and Hong Kong...")
    
    # Adding Japan stocks (Safe range to avoid GitHub timeout)
    for i in range(4000, 7500): 
        asia_tickers.add(f"{i}.T")
        
    # Adding Hong Kong stocks
    for i in range(1, 1500): 
        asia_tickers.add(f"{i:04d}.HK")

    final_tickers = list(asia_tickers)
    print(f"Successfully compiled a total of {len(final_tickers)} unique Asian tickers.")
    
    # Fallback to prevent complete failure
    if len(final_tickers) < 10:
        return ["RELIANCE.NS", "TCS.NS", "7203.T", "0700.HK", "005930.KS", "D05.SI"]
        
    return final_tickers

def check_shariah_compliance(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Skip gracefully if it's an invalid generated ticker
        if not info or ('regularMarketPrice' not in info and 'previousClose' not in info and 'sector' not in info):
            return None

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

        # Fixed AAOIFI Shariah Logic
        if debt_pass and cash_pass and income_pass:
            status = "HALAL"
        else:
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
    except Exception:
        return None

def update_asia_stocks():
    tickers = get_asia_tickers()
    stock_data = []
    count = 0

    print("Starting data extraction...")
    for ticker in tickers:
        count += 1
        if count % 200 == 0:
            print(f"Scanning progress: {count}/{len(tickers)}...")
            
        result = check_shariah_compliance(ticker)
        if result:
            stock_data.append(result)
            
        # Anti-ban sleep (Slightly faster for large dataset, but safe)
        time.sleep(random.uniform(0.8, 1.8))

    with open('asia_data.json', 'w') as f:
        json.dump(stock_data, f, indent=4, cls=NumpyEncoder)
    print(f"Data saved: {len(stock_data)} valid Asian stocks processed successfully.")

if __name__ == "__main__":
    update_asia_stocks()
