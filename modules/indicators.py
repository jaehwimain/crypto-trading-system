"""
TechnicalIndicators - 모든 기술지표를 순수 Python으로 계산
talib 제거 버전
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple

class TechnicalIndicators:
    """기술지표 계산 (talib 없이 순수 Python)"""
    
    def __init__(self, ohlcv_df: pd.DataFrame):
        """
        Args:
            ohlcv_df: columns = ['open', 'high', 'low', 'close', 'volume']
        """
        self.df = ohlcv_df.copy().reset_index(drop=True)
        self.close = self.df['close'].values
        self.high = self.df['high'].values
        self.low = self.df['low'].values
        self.open = self.df['open'].values
        self.volume = self.df['volume'].values
        self.length = len(self.close)
    
    # ============================
    # 1. EMA (지수 이동 평균)
    # ============================
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """EMA 계산"""
        ema = np.full(len(data), np.nan, dtype=float)
        if len(data) < period:
            return ema
        
        ema[period - 1] = np.mean(data[:period])
        multiplier = 2 / (period + 1)
        
        for i in range(period, len(data)):
            ema[i] = (data[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        return ema
    
    def calculate_ema(self):
        """EMA 계산 (9, 21, 50)"""
        self.df['ema_9'] = self._ema(self.close, 9)
        self.df['ema_21'] = self._ema(self.close, 21)
        self.df['ema_50'] = self._ema(self.close, 50)
    
    # ============================
    # 2. SMA (단순 이동 평균)
    # ============================
    def calculate_sma(self):
        """SMA 계산 (20, 50, 200)"""
        self.df['sma_20'] = self.df['close'].rolling(window=20).mean().values
        self.df['sma_50'] = self.df['close'].rolling(window=50).mean().values
        self.df['sma_200'] = self.df['close'].rolling(window=200).mean().values
    
    # ============================
    # 3. RSI (상대강도지수)
    # ============================
    def calculate_rsi(self, period: int = 14):
        """RSI 계산"""
        delta = self.df['close'].diff().values
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        gain_series = pd.Series(gain)
        loss_series = pd.Series(loss)
        
        avg_gain = gain_series.rolling(window=period).mean().values
        avg_loss = loss_series.rolling(window=period).mean().values
        
        rs = np.divide(avg_gain, avg_loss, where=avg_loss!=0, out=np.zeros_like(avg_loss, dtype=float))
        rsi = 100 - (100 / (1 + rs))
        rsi = np.where(np.isnan(rsi), 50, rsi)
        
        self.df['rsi'] = rsi
    
    # ============================
    # 4. MACD
    # ============================
    def calculate_macd(self):
        """MACD 계산"""
        ema_12 = self._ema(self.close, 12)
        ema_26 = self._ema(self.close, 26)
        macd = ema_12 - ema_26
        signal = self._ema(macd, 9)
        histogram = macd - signal
        
        self.df['macd'] = macd
        self.df['macd_signal'] = signal
        self.df['macd_histogram'] = histogram
    
    # ============================
    # 5. Bollinger Bands
    # ============================
    def calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2):
        """Bollinger Bands 계산"""
        sma = self.df['close'].rolling(window=period).mean().values
        std = self.df['close'].rolling(window=period).std().values
        
        bb_upper = sma + (std * std_dev)
        bb_lower = sma - (std * std_dev)
        bb_width = bb_upper - bb_lower
        
        # BB Percent: (Close - Lower) / (Upper - Lower)
        bb_range = bb_upper - bb_lower
        bb_percent = np.divide(
            self.close - bb_lower,
            bb_range,
            where=bb_range!=0,
            out=np.zeros_like(self.close, dtype=float)
        )
        bb_percent = np.clip(bb_percent * 100, 0, 100)
        
        self.df['bb_upper'] = bb_upper
        self.df['bb_middle'] = sma
        self.df['bb_lower'] = bb_lower
        self.df['bb_width'] = bb_width
        self.df['bb_percent'] = bb_percent
    
    # ============================
    # 6. ATR (Average True Range)
    # ============================
    def calculate_atr(self, period: int = 14):
        """ATR 계산"""
        high = pd.Series(self.high)
        low = pd.Series(self.low)
        close = pd.Series(self.close)
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().values
        atr_percent = (atr / self.close) * 100
        
        self.df['atr'] = atr
        self.df['atr_percent'] = atr_percent
    
    # ============================
    # 7. Stochastic
    # ============================
    def calculate_stochastic(self, period: int = 14, smooth_k: int = 3, smooth_d: int = 3):
        """Stochastic 계산"""
        low_series = pd.Series(self.low)
        high_series = pd.Series(self.high)
        close_series = pd.Series(self.close)
        
        lowest_low = low_series.rolling(window=period).min().values
        highest_high = high_series.rolling(window=period).max().values
        
        k_raw = np.divide(
            self.close - lowest_low,
            highest_high - lowest_low,
            where=(highest_high - lowest_low) != 0,
            out=np.zeros_like(self.close, dtype=float)
        ) * 100
        
        stoch_k = pd.Series(k_raw).rolling(window=smooth_k).mean().values
        stoch_d = pd.Series(stoch_k).rolling(window=smooth_d).mean().values
        
        self.df['stoch_k'] = stoch_k
        self.df['stoch_d'] = stoch_d
    
    # ============================
    # 8. ADX (Average Directional Index)
    # ============================
    def calculate_adx(self, period: int = 14):
        """ADX 계산"""
        high = pd.Series(self.high)
        low = pd.Series(self.low)
        close = pd.Series(self.close)
        
        up = high.diff()
        down = -low.diff()
        
        plus_dm = pd.Series(np.where((up > 0) & (up > down), up, 0))
        minus_dm = pd.Series(np.where((down > 0) & (down > up), down, 0))
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean().values
        
        plus_di = (plus_dm.rolling(window=period).mean().values / atr) * 100
        minus_di = (minus_dm.rolling(window=period).mean().values / atr) * 100
        
        di_diff = np.abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        
        dx = np.divide(di_diff, di_sum, where=di_sum!=0, out=np.zeros_like(di_sum))
        adx = pd.Series(dx * 100).rolling(window=period).mean().values
        
        self.df['adx'] = adx
        self.df['plus_di'] = plus_di
        self.df['minus_di'] = minus_di
    
    # ============================
    # 9. CCI (Commodity Channel Index)
    # ============================
    def calculate_cci(self, period: int = 20):
        """CCI 계산"""
        typical_price = (self.high + self.low + self.close) / 3
        tp_series = pd.Series(typical_price)
        
        sma_tp = tp_series.rolling(window=period).mean().values
        mad = tp_series.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - np.mean(x)))
        ).values
        
        cci = np.divide(
            typical_price - sma_tp,
            0.015 * mad,
            where=mad!=0,
            out=np.zeros_like(typical_price, dtype=float)
        )
        self.df['cci'] = np.clip(cci, -200, 200)
    
    # ============================
    # 10. ROC (Rate of Change)
    # ============================
    def calculate_roc(self):
        """ROC 계산 (12, 25)"""
        close_series = pd.Series(self.close)
        
        roc_12 = ((close_series - close_series.shift(12)) / close_series.shift(12)) * 100
        roc_25 = ((close_series - close_series.shift(25)) / close_series.shift(25)) * 100
        
        self.df['roc_12'] = roc_12.values
        self.df['roc_25'] = roc_25.values
        self.df['roc_avg'] = ((roc_12 + roc_25) / 2).values
    
    # ============================
    # 11. Momentum
    # ============================
    def calculate_momentum(self):
        """Momentum 계산 (5, 10, 20)"""
        close_series = pd.Series(self.close)
        
        mom_5 = (close_series - close_series.shift(5)).values
        mom_10 = (close_series - close_series.shift(10)).values
        mom_20 = (close_series - close_series.shift(20)).values
        
        self.df['momentum_5'] = mom_5
        self.df['momentum_10'] = mom_10
        self.df['momentum_20'] = mom_20
        self.df['momentum_avg'] = (mom_5 + mom_10 + mom_20) / 3
    
    # ============================
    # 12. 추가 지표
    # ============================
    def calculate_additional_indicators(self):
        """추가 지표 계산"""
        # Price Change %
        self.df['price_change_pct'] = ((self.close - self.open) / self.open) * 100
        
        # Bullish Candle
        self.df['is_bullish'] = (self.close > self.open).astype(float)
        
        # Range %
        high_low_range = self.high - self.low
        self.df['range_pct'] = (high_low_range / self.low) * 100
        
        # Volatility (20-period)
        close_series = pd.Series(self.close)
        self.df['volatility'] = close_series.pct_change().rolling(window=20).std().values * 100
        
        # Williams %R
        period = 14
        low_series = pd.Series(self.low)
        high_series = pd.Series(self.high)
        
        lowest_low = low_series.rolling(window=period).min().values
        highest_high = high_series.rolling(window=period).max().values
        
        williams_r = -100 * (highest_high - self.close) / (highest_high - lowest_low)
        self.df['williams_r'] = williams_r
    
    # ============================
    # 13. Volume Indicators
    # ============================
    def calculate_volume_indicators(self):
        """거래량 지표 계산"""
        volume_series = pd.Series(self.volume)
        
        # Volume Ratio
        volume_ma = volume_series.rolling(window=20).mean().values
        volume_ratio = self.volume / np.maximum(volume_ma, 1e-10)
        self.df['volume_ratio'] = volume_ratio
        
        # Volume Std
        self.df['volume_std'] = volume_series.rolling(window=20).std().values
        
        # Price Change (거래량과 함께)
        self.df['price_change'] = np.abs(self.close - self.open)
    
    # ============================
    # MAIN: 모든 지표 계산
    # ============================
    def calculate_all(self) -> pd.DataFrame:
        """모든 지표 한번에 계산"""
        try:
            self.calculate_ema()
            self.calculate_sma()
            self.calculate_rsi()
            self.calculate_macd()
            self.calculate_bollinger_bands()
            self.calculate_atr()
            self.calculate_stochastic()
            self.calculate_adx()
            self.calculate_cci()
            self.calculate_roc()
            self.calculate_momentum()
            self.calculate_additional_indicators()
            self.calculate_volume_indicators()
            
            # NaN 값을 50.0으로 채우기 (중립값)
            self.df = self.df.fillna(50.0)
            
        except Exception as e:
            print(f"  지표 계산 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return self.df
