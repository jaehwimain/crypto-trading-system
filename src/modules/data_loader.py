# src/modules/data_loader.py
import sys
from pathlib import Path

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """데이터 로딩 및 검증"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.historical_dir = data_dir / "historical"
        self.current_dir = data_dir / "current"
    
    def load_historical_data(self, coin: str, limit: int = None) -> pd.DataFrame:
        """과거 8년 데이터 로드"""
        filename = self.historical_dir / f"{coin}_USDT_8years.parquet"
        
        if not filename.exists():
            logger.warning(f"{coin} 과거 데이터 없음: {filename}")
            return pd.DataFrame()
        
        df = pd.read_parquet(filename)
        
        if limit:
            df = df.tail(limit)
        
        return self._validate_data(df)
    
    def load_current_data(self, coin: str) -> pd.DataFrame:
        """현재 1분 캔들 데이터 로드"""
        filename = self.current_dir / f"{coin}_USDT_current.parquet"
        
        if not filename.exists():
            logger.warning(f"{coin} 현재 데이터 없음: {filename}")
            return pd.DataFrame()
        
        df = pd.read_parquet(filename)
        return self._validate_data(df)
    
    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 검증"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        
        # 컬럼명 소문자로 변환
        df.columns = df.columns.str.lower()
        
        # 필수 컬럼 확인
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"필수 컬럼 '{col}' 없음")
                return pd.DataFrame()
        
        # 결측치 처리
        df = df.dropna(subset=required_cols)
        
        # 중복 제거
        df = df.drop_duplicates()
        
        return df
    
    def normalize_data(self, df: pd.DataFrame, col: str) -> pd.Series:
        """0~100 범위로 정규화"""
        series = df[col].astype(float)
        min_val = series.min()
        max_val = series.max()
        
        if max_val == min_val:
            return pd.Series([50] * len(series), index=series.index)
        
        normalized = ((series - min_val) / (max_val - min_val)) * 100
        return normalized
    
    def load_all_coins(self, coins: list, data_type: str = "historical") -> Dict[str, pd.DataFrame]:
        """모든 코인 데이터 일괄 로드"""
        data = {}
        
        for coin in coins:
            if data_type == "historical":
                df = self.load_historical_data(coin)
            else:
                df = self.load_current_data(coin)
            
            if not df.empty:
                data[coin] = df
            else:
                logger.warning(f"{coin} 데이터 로드 실패")
        
        return data

if __name__ == "__main__":
    from config import DATA_DIR, COINS
    
    loader = DataLoader(DATA_DIR)
    
    # 테스트: BTC 과거 데이터 로드
    btc_data = loader.load_historical_data("BTC", limit=100)
    print(f"BTC 데이터: {len(btc_data)} 행")
    print(btc_data.head())
