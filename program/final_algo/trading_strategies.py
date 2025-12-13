import pandas as pd
import numpy as np
import math

# --- Strategy 1: The SVM Model's Predictions ---

class Strategy:
    def __init__(self):
        self.daily_portfolio_values = list()
    
    # The default is to trade each stock individually with $100 allotted, but if not this can be changed
    def run(self, model, feature_cols, scaler, test_data, printing=False):
        """
        Backtests the strategy based on the SVM model's signals.
        'test_data' must include 'ticker', 'date', 'change_day', and 'signal' (the y_pred).
        """
        self.model = model
        self.feature_cols = feature_cols
        self.scaler = scaler
        self.printing = printing
        
        print(f"\n--- Running {self.name} Strategy Simulation ---")
        test_data = test_data.sort_values('date')
        #test_data["date"] = pd.to_datetime(test_data["date"])
        #test_data = test_data.dropna(subset=["date"])
        #if test_data.empty:
        #    raise Exception("Empty set")

        self.data = test_data
        
        self.tickers = self.data['ticker'].unique()
        tickers_n = len(self.tickers)
        
        self.cashes = [100 for _ in range(tickers_n)]
        self.stock_values = [0.0 for _ in range(tickers_n)]
        
        self.first_date = self.data.iloc[0]["date"]
        self.last_date = self.data.iloc[-1]["date"]
        
        # Initialize share prices
        self.share_prices = [0.0 for _ in range(tickers_n)]
        price_per_ticker = (
            test_data.sort_values("date")
                .groupby("ticker")
                .first()["Adj Close"]
        )
        for i, ticker in enumerate(self.tickers):
            # get() can be None, but it's ok because it won't be used
            self.share_prices[i] = price_per_ticker.get(ticker)
        
        # Run simulation
        for day in pd.date_range(start=self.first_date, end=self.last_date):
            rows = self.data.loc[self.data["date"] == day]
            self.update_stocks(rows)
            
            old_stock_values = None
            if self.printing:
                old_stock_values = self.stock_values
                print("=========================")
                print(f"PROBABILITIES FOR {day}:")
            self.trade_day(rows)
            
            if self.printing:
                self.print_trades(old_stock_values)

        return self.metrics()
    
    # Calculate metrics for this strategy
    def metrics(self):
        results = []
        
        final_value = self.daily_portfolio_values[-1]
        original_value = 100 * len(self.tickers)
        total_return_pct = (final_value - original_value) / original_value
        profit = final_value - original_value
            
        daily_returns = pd.Series(self.daily_portfolio_values).pct_change().fillna(0)
        risk_pct = daily_returns.std()
        sharpe_ratio = (daily_returns.mean() / risk_pct) * np.sqrt(252) if risk_pct > 0 else 0
        
        results.append({
            'strategy': self.name,
            'final_value': final_value,
            'profit': profit,
            'total_return_pct': total_return_pct,
            'risk_pct': risk_pct,
            'sharpe_ratio': sharpe_ratio
        })
        
        return pd.DataFrame(results)
    
    # Update stock values with changing share prices
    def update_stocks(self, day_rows):
        for i, ticker in enumerate(self.tickers):
            ticker_rows = day_rows.loc[day_rows["ticker"] == ticker]
            if len(ticker_rows) == 0:
                continue
            row = ticker_rows.iloc[0]
            
            old_stock_value = self.stock_values[i]
            old_share_price = self.share_prices[i]
            
            # Shares = $ / ($ per share)
            shares = old_stock_value / old_share_price
            
            new_share_price = row["Adj Close"]
            new_stock_value = shares * new_share_price
            
            self.share_prices[i] = new_share_price
            self.stock_values[i] = new_stock_value
            
        self.daily_portfolio_values.append(sum(self.stock_values) + sum(self.cashes))
        
    
    def trade_day(self, rows):
        for i, ticker in enumerate(self.tickers):
            ticker_rows = rows.loc[rows["ticker"] == ticker]
            if len(ticker_rows) == 0:
                continue
            row = ticker_rows.iloc[0]
            
            cash = self.cashes[i]
            stock_value = self.stock_values[i]
            
            (cash, stock_value) = self.trade_stock(row, cash, stock_value)
                
            self.cashes[i] = cash
            self.stock_values[i] = stock_value

    
    def trade_stock(self, row, cash, stock_value):
        raise Exception("Not defined")
        
    def print_trades(self, old_stock_values):
        print("\nTRADES:")
        for i, ticker in enumerate(self.tickers):
            old = old_stock_values[i]
            new = self.stock_values[i]
            delta = new - old
            buy = delta > 0
            delta = abs(delta)
            if delta == 0:
                print(f"{ticker}: Hold (${new})")
            elif buy:
                print(f"{ticker}: Buy ${delta} (${old} -> ${new})")
            else:
                print(f"{ticker}: Sell ${delta} (${old} -> ${new})")


# Make trade based on SVM signal
class Svm(Strategy):
    def __init__(self):
        super().__init__()
        self.super_bid = 0.20
        self.small_bid = 0.10
        self.name = "SVM Model"

    def trade_stock(self, row, cash, stock_value):
        signal = row["signal"]
        
        if signal == 0:
            return (cash, stock_value)
        
        quantity = 0
        if abs(signal) == 1:
            quantity = self.small_bid
        else:
            quantity = self.super_bid
        
        if signal > 0:
            # Buy
            trade = cash * quantity
            cash -= trade
            stock_value += trade
        else:
            # Sell
            trade = stock_value * quantity
            stock_value -= trade
            cash += trade
            
        return (cash, stock_value)
    
# --- Strategy 2: The "Buy and Hold" Benchmark ---

class BuyAndHold(Strategy):
    def __init__(self):
        super().__init__()
        self.name = "Buy and Hold"

    def trade_stock(self, row, cash, stock_value):
        if cash > 0:
            stock_value += cash
            cash = 0
        
        return (cash, stock_value)

# --- Strategy 3: Raw SVC Signal (Bonus) ---

class RawSvc(Strategy):
    def __init__(self, svc_buy_threshold=0.5, svc_sell_threshold=-0.5):
        super().__init__()
        self.svc_buy = svc_buy_threshold
        self.svc_sell = svc_sell_threshold
        self.name = "Raw SVC"

    def trade_stock(self, row, cash, stock_value):
        # Trade based on raw SVC, not the SVM signal
        svc = row['svc']
                
        if svc > self.svc_buy: # Buy
            trade_amount = cash * 0.10
            cash -= trade_amount
            stock_value += trade_amount
        elif svc < self.svc_sell: # Sell
            trade_amount = stock_value * 0.10
            stock_value -= trade_amount
            cash += trade_amount
        
        return (cash, stock_value)

# Default expected growth for a class: Geometric mean of minimum and maximum growth
def default_expected_growth(thresholds):
    growth = dict()
    growth[0] = (0.0, (thresholds[0][1], -thresholds[0][1]))
    for i, (_, threshold) in enumerate(thresholds):
        next = None
        neg_limits = None
        if i + 1 < len(thresholds):
            _, next = thresholds[i+1]
            neg_limits = (-next, -threshold)
            pos_limits = (threshold, next)
        else:
            next = threshold * 2
            neg_limits = (None, -threshold)
            pos_limits = (threshold, None)
        
        expected_growth = math.sqrt(threshold * next)
        growth[i+1] = (expected_growth, pos_limits)
        growth[-i-1] = (-expected_growth, neg_limits)
    return growth

# A strategy that uses the Random Forest's probabilities of each class of growth
class SoftMax(Strategy):
    # expected growth for each class
    def __init__(self, beta=0.5, expected_growth=None, thresholds=None):
        super().__init__()
        
        self.thresholds = thresholds
        if expected_growth == None:
            expected_growth = default_expected_growth(thresholds)
        self.expected_growth = expected_growth
        
        self.beta = beta
        self.name = f"SoftMax beta={beta}"
        
    def trade_day(self, rows):
        # Prepare for total reorganization of assets
        
        # A dictionary representing the weight given to each stock
        weights = dict()
        total_weight = 0
        total_assets = 0
        for i, ticker in enumerate(self.tickers):
            ticker_rows = rows.loc[rows["ticker"] == ticker]
            if len(ticker_rows) == 0:
                continue
            
            row = ticker_rows.iloc[[0]]
            
            row_features = row[self.feature_cols]
            row_scaled = self.scaler.transform(row_features)
            probs = self.model.predict_proba(row_scaled)[0]
            if self.printing:
                print(f"{ticker}:")
            
            expected_returns = 0
            for classs, (growth, limits) in sorted(self.expected_growth.items()):
                index = classs + len(self.thresholds)
                probability = probs[index]
                
                if self.printing:
                    g = growth * 100
                    (a,b) = limits
                    print(f"{probability} chance of growth rate ~{g}% (btwn {a} and {b})")
                
                growth_rate = 1.0 + growth
                
                expected_returns += growth_rate * probability
                
            weight = math.exp(expected_returns * self.beta)
            # Keys for stock in "weights" are their index in self.tickers
            weights[i] = weight
            total_weight += weight
            
            # Reorganize all assets in stocks with data present
            total_assets += self.stock_values[i]
            total_assets += self.cashes[i]
            self.stock_values[i] = 0
            self.cashes[i] = 0
            
        if total_weight == 0:
            return
        
        for stock_index, weight in weights.items():
            proportion = weight / total_weight
            investment = total_assets * proportion
            self.stock_values[stock_index] = investment
        
        #print(str(sum(self.stock_values)))

