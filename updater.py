import json
import time
import requests
import yfinance as yf
import pandas as pd

# ==========================================
# PART 1: STOCK SCREENING (AAOIFI Logic)
# ==========================================
def get_top_500_tickers():
    """উইকিপিডিয়া থেকে S&P 500 এর টপ ৫০০ কোম্পানির লিস্ট অটোমেটিক নিবে"""
    print("Fetching Top 500 US Companies list...")
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        # উইকিপিডিয়াকে বোকা বানানোর জন্য User-Agent (যাতে রোবট না ভাবে)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        html_data = requests.get(url, headers=headers).text
        
        tables = pd.read_html(html_data)
        df = tables[0]
        tickers = df['Symbol'].tolist()
        print(f"✅ Successfully fetched {len(tickers)} tickers from Wikipedia.")
        return tickers
    except Exception as e:
        print("Error fetching ticker list:", e)
        # ব্যাকআপ হিসেবে কিছু পপুলার স্টকের নাম
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA"]
def check_stock_shariah(ticker):
    """Yahoo Finance থেকে ব্যালেন্স শিট এনে হালাল/হারাম হিসাব করবে"""
    try:
        # Yahoo Finance থেকে ডেটা কল করা
        stock = yf.Ticker(ticker)
        info = stock.info
        
        name = info.get('shortName', ticker)
        sector = info.get('sector', 'Unknown')
        
        # ব্যালেন্স শিট (Balance Sheet) নিয়ে আসা
        bs = stock.balance_sheet
        
        if bs.empty:
            return {"ticker": ticker, "name": name, "status": "DOUBTFUL", "reason": "No financial data available"}
        
        # AAOIFI রুলস: Total Debt / Total Assets < 33%
        try:
            # লেটেস্ট বছরের ডেটা নেওয়া
            total_assets = bs.loc['Total Assets'].iloc[0]
            # যদি কোম্পানির কোনো ঋণ না থাকে, তবে Total Debt 0 ধরবে
            total_debt = bs.loc['Total Debt'].iloc[0] if 'Total Debt' in bs.index else 0
            
            if total_assets == 0:
                return {"ticker": ticker, "name": name, "status": "DOUBTFUL", "reason": "Assets are zero"}
            
            # শতকরা ঋণের হিসাব
            debt_ratio = (total_debt / total_assets) * 100
            
            # সিদ্ধান্ত গ্রহণ
            if debt_ratio < 33.0:
                status = "HALAL"
            else:
                status = "HARAM"
                
            reason = f"Debt Ratio: {debt_ratio:.2f}% (Limit: 33%)"
            
        except KeyError:
            status = "DOUBTFUL"
            reason = "Missing Debt/Asset data in Balance Sheet"
            
        return {"ticker": ticker, "name": name, "sector": sector, "status": status, "reason": reason}
        
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None

def update_stocks():
    tickers = get_top_500_tickers()
    stock_data = []
    
    # আমরা আপাতত প্রথম ৩০০ কোম্পানি নিচ্ছি যাতে Yahoo Finance ব্লক না করে (Rate Limit)
    for ticker in tickers[:300]: 
        print(f"Checking {ticker}...")
        result = check_stock_shariah(ticker)
        if result:
            stock_data.append(result)
        
        # Yahoo-কে বুঝতে না দেওয়ার জন্য প্রতি সার্চে ১ সেকেন্ড বিরতি (যাতে রোবট না ভাবে)
        time.sleep(1)
            
    # ডেটাবেস ফাইলে সেভ করা
    with open('data.json', 'w') as f:
        json.dump(stock_data, f, indent=4)
    print(f"✅ Saved {len(stock_data)} stocks to data.json")

# ==========================================
# PART 2: CRYPTO SCREENING (Category Logic)
# ==========================================

def update_cryptos():
    print("Fetching Top 100 Cryptocurrencies...")
    # CoinGecko API থেকে ডেটা আনা
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100, # মার্কেট ক্যাপ অনুযায়ী সেরা ১০০ ক্রিপ্টো
        "page": 1,
        "sparkline": False
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        crypto_data = []
        
        # হারাম ক্যাটাগরির লিস্ট (Meme, Gambling)
        haram_keywords = ["doge", "pepe", "inu", "shib", "floki", "casino", "gambling", "betting"]
        
        for coin in data:
            symbol = coin['symbol'].upper()
            name = coin['name']
            name_lower = name.lower()
            
            # ডিফল্ট স্ট্যাটাস
            status = "HALAL"
            reason = "General Utility / Layer 1 / Payment"
            
            # লজিক চেকিং
            if any(bad_word in name_lower for bad_word in haram_keywords):
                status = "HARAM"
                reason = "Meme coin or Prohibited Category"
            elif symbol in ["USDT", "USDC", "DAI", "FDUSD"]:
                status = "DOUBTFUL"
                reason = "Stablecoin (Requires checking underlying backing)"
                
            crypto_data.append({
                "ticker": symbol,
                "name": name,
                "status": status,
                "reason": reason
            })
            
        with open('crypto_data.json', 'w') as f:
            json.dump(crypto_data, f, indent=4)
        print(f"✅ Saved {len(crypto_data)} cryptos to crypto_data.json")
        
    except Exception as e:
        print("Error fetching cryptos:", e)

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🚀 Starting Automated Halal Screening System...")
    update_stocks()
    update_cryptos()
    print("🎉 All updates completed successfully!")
