"""
src/optimizer/data_accumulator.py
과거 + 현재 데이터 누적 및 관리
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DataAccumulator:
    """
    과거 1년 데이터 + 실시간 현재 데이터 누적
    – 최적화 엔진이 항상 최신 데이터로 학습
    """

    def __init__(self, coin: str, data_dir: str = "data/historical"):
        """
        Args:
            coin: 코인명 (BTC, ETH, SOL 등)
            data_dir: 데이터 저장 디렉토리
        """
        self.coin = coin
        self.data_dir = data_dir
        self.historical_file = f"{data_dir}/{coin}_historical.csv"
        self.current_file = f"{data_dir}/{coin}_current.csv"
        
        os.makedirs(data_dir, exist_ok=True)
        
        self.historical_data = None  # 과거 1년 데이터 (메모리)
        self.current_data = []       # 현재 데이터 (누적 중)
        
        logger.info(f"[DataAccumulator] 초기화: {coin}")

    def load_historical_data(self) -> pd.DataFrame:
        """
        과거 1년 데이터 로드 (CSV 또는 API)
        
        Returns:
            columns: timestamp, open, high, low, close, volume
        """
        try:
            if os.path.exists(self.historical_file):
                self.historical_data = pd.read_csv(self.historical_file)
                logger.info(
                    f"[DataAccumulator] {self.coin} 과거 데이터 로드: {len(self.historical_data)}행"
                )
                return self.historical_data
            else:
                logger.warning(f"[DataAccumulator] {self.coin} 과거 데이터 파일 없음 – API로 수집 필요")
                # TODO: Upbit API에서 1년 데이터 수집
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"[DataAccumulator] {self.coin} 과거 데이터 로드 오류: {e}")
            return pd.DataFrame()

    def add_current_candle(self, candle: Dict):
        """
        현재 1분 캔들 데이터 추가
        
        Args:
            candle: {'timestamp': ..., 'open': ..., 'high': ..., 'low': ..., 'close': ..., 'volume': ...}
        """
        try:
            self.current_data.append(candle)
            
            # 매 100개마다 파일에 저장 (주기적 저장)
            if len(self.current_data) % 100 == 0:
                self._save_current_data()
            
        except Exception as e:
            logger.error(f"[DataAccumulator] {self.coin} 캔들 추가 오류: {e}")

    def _save_current_data(self):
        """현재 데이터를 CSV에 저장"""
        try:
            if not self.current_data:
                return
            
            df = pd.DataFrame(self.current_data)
            df.to_csv(self.current_file, mode='a', header=False, index=False)
            logger.debug(f"[DataAccumulator] {self.coin} 현재 데이터 저장: {len(self.current_data)}행")
            self.current_data = []  # 메모리 정리
            
        except Exception as e:
            logger.error(f"[DataAccumulator] {self.coin} 데이터 저장 오류: {e}")

    def get_combined_data(self, days: int = 30) -> pd.DataFrame:
        """
        과거 + 현재 데이터 병합
        (최근 N일 데이터로 백테스트)
        
        Args:
            days: 최근 몇 일의 데이터 사용 (기본 30일)
        
        Returns:
            병합된 DataFrame
        """
        try:
            # 과거 데이터 로드
            if self.historical_data is None:
                self.load_historical_data()
            
            # 현재 데이터 로드
            current_df = pd.DataFrame()
            if os.path.exists(self.current_file):
                current_df = pd.read_csv(self.current_file)
            
            # 병합
            if self.historical_data is not None and not self.historical_data.empty:
                combined = pd.concat([self.historical_data, current_df], ignore_index=True)
            else:
                combined = current_df
            
            # 시간순 정렬
            combined['timestamp'] = pd.to_datetime(combined['timestamp'])
            combined = combined.sort_values('timestamp').reset_index(drop=True)
            
            # 최근 N일 데이터만 반환
            cutoff_date = datetime.now() - timedelta(days=days)
            combined = combined[combined['timestamp'] >= cutoff_date]
            
            logger.info(
                f"[DataAccumulator] {self.coin} 병합 데이터: {len(combined)}행 "
                f"({combined['timestamp'].min()} ~ {combined['timestamp'].max()})"
            )
            
            return combined
            
        except Exception as e:
            logger.error(f"[DataAccumulator] {self.coin} 데이터 병합 오류: {e}")
            return pd.DataFrame()

    def get_latest_candles(self, limit: int = 100) -> List[Dict]:
        """최근 N개 캔들 반환"""
        try:
            combined = self.get_combined_data(days=7)  # 최근 7일
            if combined.empty:
                return []
            
            return combined.tail(limit).to_dict('records')
        except Exception as e:
            logger.error(f"[DataAccumulator] {self.coin} 최근 캔들 조회 오류: {e}")
            return []

    def reset_current_data(self):
        """현재 데이터 초기화"""
        self.current_data = []
        if os.path.exists(self.current_file):
            os.remove(self.current_file)
        logger.info(f"[DataAccumulator] {self.coin} 현재 데이터 초기화")
