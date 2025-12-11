import pandas as pd
import numpy as np

# --- Strategy 1: The SVM Model's Predictions ---

class Strategy:
    def run(self, test_data):
        raise Exception("Not defined")

class Svm(Strategy):
    def run(self, test_data):
        """
        Backtests the 10% buy/sell strategy based on the SVM model's signals.
        'test_data' must include 'ticker', 'date', 'change_day', and 'signal' (the y_pred).
        """
        print("\n--- Running SVM Strategy Simulation ---")
        results = []
        
        for ticker in test_data['ticker'].unique():
            ticker_df = test_data[test_data['ticker'] == ticker].sort_values('date')
            if ticker_df.empty:
                continue

            cash = 100.0
            stock_value = 0.0
            daily_portfolio_values = [100.0]

            for index, row in ticker_df.iterrows():
                # 1. Update portfolio value based on the day's market move
                daily_return = row['change_day']
                stock_value *= (1 + daily_return)
                daily_portfolio_values.append(cash + stock_value)

                # 2. Make trade based on signal
                signal = row['signal']
                
                if signal == 1: # Buy
                    trade_amount = cash * 0.10
                    cash -= trade_amount
                    stock_value += trade_amount
                elif signal == -1: # Sell
                    trade_amount = stock_value * 0.10
                    stock_value -= trade_amount
                    cash += trade_amount
                
            # Calculate metrics for this ticker
            final_value = cash + stock_value
            total_return_pct = (final_value - 100) / 100
            profit = final_value - 100
            
            daily_returns = pd.Series(daily_portfolio_values).pct_change().fillna(0)
            risk_pct = daily_returns.std()
            sharpe_ratio = (daily_returns.mean() / risk_pct) * np.sqrt(252) if risk_pct > 0 else 0
            
            results.append({
                'ticker': ticker,
                'strategy': 'SVM Model',
                'final_value': final_value,
                'profit': profit,
                'total_return_pct': total_return_pct,
                'risk_pct': risk_pct,
                'sharpe_ratio': sharpe_ratio
            })
            
        return pd.DataFrame(results)

# --- Strategy 2: The "Buy and Hold" Benchmark ---

class BuyAndHold(Strategy):
    def run(self, test_data):
        """
        Backtests a simple Buy and Hold strategy for comparison.
        'test_data' must include 'ticker', 'date', and 'change_day'.
        """
        print("--- Running Buy and Hold Simulation ---")
        results = []
        
        for ticker in test_data['ticker'].unique():
            ticker_df = test_data[test_data['ticker'] == ticker].sort_values('date')
            if ticker_df.empty:
                continue
                
            bnh_value = 100.0
            daily_portfolio_values = [100.0]
            
            for index, row in ticker_df.iterrows():
                daily_return = row['change_day']
                bnh_value *= (1 + daily_return)
                daily_portfolio_values.append(bnh_value)
                
            # Calculate metrics
            final_value = bnh_value
            total_return_pct = (final_value - 100) / 100
            profit = final_value - 100
            
            daily_returns = pd.Series(daily_portfolio_values).pct_change().fillna(0)
            risk_pct = daily_returns.std()
            sharpe_ratio = (daily_returns.mean() / risk_pct) * np.sqrt(252) if risk_pct > 0 else 0
            
            results.append({
                'ticker': ticker,
                'strategy': 'Buy and Hold',
                'final_value': final_value,
                'profit': profit,
                'total_return_pct': total_return_pct,
                'risk_pct': risk_pct,
                'sharpe_ratio': sharpe_ratio
            })
            
        return pd.DataFrame(results)

    # --- Strategy 3: Raw SVC Signal (Bonus) ---

class RawSvc(Strategy):
    def __init__(self, svc_buy_threshold=0.5, svc_sell_threshold=-0.5):
        self.svc_buy = 0.5
        self.svc_sell = -0.5

    def run(self, test_data):
        """
        Backtests a strategy based only on raw SVC thresholds.
        'test_data' must include 'ticker', 'date', 'change_day', and 'svc'.
        """
        print("--- Running Raw SVC Signal Simulation ---")
        results = []
        
        for ticker in test_data['ticker'].unique():
            ticker_df = test_data[test_data['ticker'] == ticker].sort_values('date')
            if ticker_df.empty:
                continue

            cash = 100.0
            stock_value = 0.0
            daily_portfolio_values = [100.0]

            for index, row in ticker_df.iterrows():
                daily_return = row['change_day']
                stock_value *= (1 + daily_return)
                daily_portfolio_values.append(cash + stock_value)

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
                
            # Calculate metrics
            final_value = cash + stock_value
            total_return_pct = (final_value - 100) / 100
            profit = final_value - 100
            
            daily_returns = pd.Series(daily_portfolio_values).pct_change().fillna(0)
            risk_pct = daily_returns.std()
            sharpe_ratio = (daily_returns.mean() / risk_pct) * np.sqrt(252) if risk_pct > 0 else 0
            
            results.append({
                'ticker': ticker,
                'strategy': 'Raw SVC Signal',
                'final_value': final_value,
                'profit': profit,
                'total_return_pct': total_return_pct,
                'risk_pct': risk_pct,
                'sharpe_ratio': sharpe_ratio
            })
            
        return pd.DataFrame(results)



STRATEGIES = [Svm(), BuyAndHold(), RawSvc()]
