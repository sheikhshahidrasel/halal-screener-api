import yfinance as yf
import json
import os

# এখানে আমরা জনপ্রিয় স্টকগুলোর নাম দিয়েছি (আপনি চাইলে পরে আরও যোগ করতে পারবেন)
STOCKS = ["AAPL", "GOOG", "TSLA", "META", "MSFT", "NFLX", "AMZN", "NVDA"]

def check_shariah(ticker):
    stock = yf.Ticker(ticker)
    try:
        info = stock.info
        # ব্যালেন্স শিট থেকে মোট ঋণের পরিমাণ (Total Debt) এবং মোট সম্পদ (Total Assets) খোঁজা হচ্ছে
        debt = info.get('totalDebt', 0)
        assets = info.get('totalAssets', 1) # 1 দেওয়া হলো যাতে 0 দিয়ে ভাগ না হয়
        
        # AAOIFI নিয়ম অনুযায়ী Debt Ratio বের করা হচ্ছে (ঋণ / সম্পদ * ১০০)
        debt_ratio = (debt / assets) * 100 if assets else 0
        
        # হালাল/হারাম লজিক (Debt Ratio < 33% হলে Halal)
        if debt_ratio < 33:
            status = "HALAL"
        elif debt_ratio < 40:
            status = "DOUBTFUL"
        else:
            status = "HARAM"
            
        return {
            "status": status,
            "income": "< 5% (Est.)", 
            "securities": "Checked",
            "debt": f"{round(debt_ratio, 1)}%"
        }
    except Exception as e:
        return None

def main():
    database = {}
    print("Starting automated Shariah screening...")
    
    for ticker in STOCKS:
        print(f"Checking {ticker}...")
        result = check_shariah(ticker)
        if result:
            database[ticker] = result
        else:
            # যদি কোনো ডেটা না পাওয়া যায়
            database[ticker] = {"status": "DOUBTFUL", "income": "N/A", "securities": "N/A", "debt": "N/A"}
    
    # নতুন ডেটা দিয়ে আপনার ওয়েবসাইটের data.json ফাইলটি আপডেট করে দেওয়া হচ্ছে
    with open('data.json', 'w') as f:
        json.dump(database, f, indent=4)
        
    print("Database successfully updated with live data!")

if __name__ == "__main__":
    main()
