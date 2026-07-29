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

def get_eu_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/eu_tickers_placeholder.txt"
        response = requests.get(url)
        if response.status_code == 200:
            tickers = response.text.strip().split('\n')
            return [t.strip() for t in tickers if t.strip()]
        else:
            raise Exception("Ticker list not found at URL")
    except Exception as e:
        print(f"Error fetching EU tickers: {e}")
        return [
            "SHEL.L", "AZN.L", "HSBA.L", "ULVR.L", "BP.L", 
            "ASML.AS", "MC.PA", "SAP.DE", "SIE.DE", "TTE.PA", 
            "OR.PA", "SAN.PA", "VOW3.DE", "ALV.DE", "IBE.MC"
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

def update_eu_stocks():
    tickers = get_eu_tickers()
    stock_data = []

    for ticker in tickers:
        print(f"Processing {ticker}...")
        result = check_shariah_compliance(ticker)
        if result:
            stock_data.append(result)
        time.sleep(1)

    with open('eu_data.json', 'w') as f:
        json.dump(stock_data, f, indent=4, cls=NumpyEncoder)
    print(f"Data saved: {len(stock_data)} EU/UK stocks.")

if __name__ == "__main__":
    update_eu_stocks()
