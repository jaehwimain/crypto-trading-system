import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

class RegressionOptimizer:
    def __init__(self, data_loader, config):
        self.data_loader = data_loader
        self.config = config
    
    def analyze_historical_data(self, coin: str) -> Dict:
        logger.info(f"분석: {coin}")
        df = self.data_loader.load_historical_data(coin)
        if df.empty:
            logger.warning(f"데이터 없음: {coin}")
            return {}
        indicators = self._calculate_indicators(df)
        return indicators
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        indicators = {}
        close = df['close'].astype(float)
        high = df['high'].astype(float)
        low = df['low'].astype(float)
        volume = df['volume'].astype(float)
        
        for period in [9, 21, 50]:
            indicators[f'ema_{period}'] = close.ewm(span=period).mean()
        
        indicators['rsi_14'] = self._calculate_rsi(close)
        
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        indicators['macd'] = ema12 - ema26
        indicators['macd_signal'] = indicators['macd'].ewm(span=9).mean()
        
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        indicators['bb_upper'] = sma20 + (std20 * 2)
        indicators['bb_lower'] = sma20 - (std20 * 2)
        
        indicators['atr_14'] = self._calculate_atr(high, low, close)
        indicators['roc_12'] = close.pct_change(periods=12) * 100
        indicators['volume_ratio'] = volume.rolling(20).mean()
        indicators['momentum_5'] = close - close.shift(5)
        indicators['volatility'] = close.pct_change().rolling(20).std() * 100
        
        return indicators
    
    @staticmethod
    def _calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def _calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def fit_regression(self, coin: str, indicators: Dict) -> Tuple[Dict, float]:
        df = self.data_loader.load_historical_data(coin)
        close = df['close'].astype(float)
        returns = close.pct_change() * 100
        returns = returns.dropna()
        
        ind_df = pd.DataFrame(indicators).dropna()
        common_idx = returns.index.intersection(ind_df.index)
        X = ind_df.loc[common_idx].values
        y = returns.loc[common_idx].values
        
        if len(X) < 100:
            return {}, 0.0
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        model = LinearRegression()
        model.fit(X_scaled, y)
        r2 = model.score(X_scaled, y)
        
        coef = np.abs(model.coef_)
        weights = coef / coef.sum()
        
        result = {}
        for i, (key, w) in enumerate(zip(indicators.keys(), weights)):
            if i < 15:
                result[key] = round(float(w), 4)
        
        if result:
            total = sum(result.values())
            result = {k: round(v/total, 4) for k, v in result.items()}
        
        return result, r2
    
    def optimize_all_coins(self, coins: list) -> Dict:
        logger.info("회귀분석 시작")
        params = {}
        
        for coin in coins:
            try:
                ind = self.analyze_historical_data(coin)
                if not ind:
                    continue
                weights, r2 = self.fit_regression(coin, ind)
                if not weights:
                    continue
                params[coin] = {
                    "weights": weights,
                    "entry_threshold": 65,
                    "stop_loss_pct": -2.0,
                    "take_profit_pct": 5.0,
                    "position_size_pct": 10.0,
                    "max_positions": 5,
                    "r2_score": r2
                }
            except Exception as e:
                logger.error(f"오류 {coin}: {e}")
        
        logger.info(f"완료: {len(params)}개 코인")
        return params
