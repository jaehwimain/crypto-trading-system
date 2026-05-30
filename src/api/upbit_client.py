"""
Upbit API를 통한 실시간 데이터 수집 모듈
50개 코인의 1분 캔들 데이터를 실시간으로 수집합니다.
"""

import ccxt
import pandas as pd
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UpbitClient:
    """Upbit API 클라이언트 - 실시간 데이터 수집"""
    
    def __init__(self, api_key: str = None, api_secret: str = None):
        """
        Upbit 클라이언트 초기화
        
        Args:
            api_key: Upbit API 키
            api_secret: Upbit API 시크릿
        """
        try:
            self.exchange = ccxt.upbit(config={
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'rateLimit': 100
            })
            self.exchange.load_markets()
            logger.info("✅ Upbit 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"❌ Upbit 클라이언트 초기화 실패: {e}")
            raise
    
    def get_available_coins(self, limit: int = 50) -> List[str]:
        """
        거래 가능한 코인 목록 조회
        
        Args:
            limit: 조회할 코인 개수
        
        Returns:
            코인 심볼 리스트 (예: ['BTC/KRW', 'ETH/KRW', ...])
        """
        try:
            symbols = []
            for symbol in self.exchange.symbols:
                if symbol.endswith('/KRW'):
                    symbols.append(symbol)
                if len(symbols) >= limit:
                    break
            logger.info(f"✅ {len(symbols)}개 코인 조회 완료")
            return symbols
        except Exception as e:
            logger.error(f"❌ 코인 목록 조회 실패: {e}")
            return []
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> Optional[pd.DataFrame]:
        """
        OHLCV 데이터 조회
        
        Args:
            symbol: 코인 심볼 (예: 'BTC/KRW')
            timeframe: 캔들 주기 (기본값: '1m')
            limit: 조회 개수 (기본값: 100)
        
        Returns:
            OHLCV 데이터 DataFrame
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            
            # DataFrame 생성
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # timestamp를 datetime으로 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            
            return df
        
        except Exception as e:
            logger.error(f"❌ {symbol} OHLCV 조회 실패: {e}")
            return None
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        현재 시세 조회
        
        Args:
            symbol: 코인 심볼 (예: 'BTC/KRW')
        
        Returns:
            현재 시세 정보
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ {symbol} 시세 조회 실패: {e}")
            return None
    
    def get_balance(self) -> Optional[Dict]:
        """
        계좌 잔고 조회
        
        Returns:
            잔고 정보
        """
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"❌ 잔고 조회 실패: {e}")
            return None
    
    def fetch_multiple_ohlcv(self, symbols: List[str], timeframe: str = '1m', limit: int = 100) -> Dict[str, pd.DataFrame]:
        """
        여러 코인의 OHLCV 데이터를 병렬로 조회
        
        Args:
            symbols: 코인 심볼 리스트
            timeframe: 캔들 주기
            limit: 조회 개수
        
        Returns:
            {심볼: DataFrame} 딕셔너리
        """
        result = {}
        
        for symbol in symbols:
            try:
                df = self.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
                if df is not None:
                    result[symbol] = df
                    logger.info(f"✅ {symbol} 데이터 조회 완료")
                time.sleep(0.1)  # Rate limit 고려
            except Exception as e:
                logger.error(f"❌ {symbol} 데이터 조회 실패: {e}")
                continue
        
        logger.info(f"✅ {len(result)}/{len(symbols)} 코인 데이터 수집 완료")
        return result
    
    def save_ohlcv_to_csv(self, df: pd.DataFrame, filepath: str) -> bool:
        """
        OHLCV 데이터를 CSV로 저장
        
        Args:
            df: OHLCV DataFrame
            filepath: 저장 경로
        
        Returns:
            저장 성공 여부
        """
        try:
            df.to_csv(filepath, index=False)
            logger.info(f"✅ {filepath}에 데이터 저장 완료")
            return True
        except Exception as e:
            logger.error(f"❌ CSV 저장 실패: {e}")
            return False
    
    def save_current_data_json(self, data: Dict, filepath: str) -> bool:
        """
        현재 데이터를 JSON으로 저장
        
        Args:
            data: 저장할 데이터
            filepath: 저장 경로
        
        Returns:
            저장 성공 여부
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ {filepath}에 데이터 저장 완료")
            return True
        except Exception as e:
            logger.error(f"❌ JSON 저장 실패: {e}")
            return False


class RealtimeDataCollector:
    """실시간 데이터 수집기"""
    
    def __init__(self, upbit_client: UpbitClient, coins: List[str]):
        """
        초기화
        
        Args:
            upbit_client: UpbitClient 인스턴스
            coins: 모니터링할 코인 리스트
        """
        self.client = upbit_client
        self.coins = coins
        self.data_buffer = {}
    
    def collect_current_minute(self) -> Dict[str, Dict]:
        """
        현재 분의 모든 코인 데이터 수집
        
        Returns:
            {코인: 시세 정보} 딕셔너리
        """
        current_data = {}
        
        for coin in self.coins:
            try:
                ticker = self.client.get_ticker(coin)
                if ticker:
                    current_data[coin] = ticker
            except Exception as e:
                logger.error(f"❌ {coin} 수집 실패: {e}")
                continue
        
        return current_data
    
    def collect_minute_candles(self) -> Dict[str, pd.DataFrame]:
        """
        모든 코인의 최근 1분 캔들 데이터 수집
        
        Returns:
            {코인: OHLCV DataFrame} 딕셔너리
        """
        candles = {}
        
        for coin in self.coins:
            try:
                df = self.client.get_ohlcv(coin, timeframe='1m', limit=1)
                if df is not None and len(df) > 0:
                    candles[coin] = df
            except Exception as e:
                logger.error(f"❌ {coin} 캔들 수집 실패: {e}")
                continue
        
        return candles
    
    def save_snapshot(self, output_dir: str = 'data/current') -> bool:
        """
        현재 시점의 스냅샷 저장
        
        Args:
            output_dir: 저장 디렉토리
        
        Returns:
            저장 성공 여부
        """
        try:
            # 현재 시세 수집
            current_data = self.collect_current_minute()
            
            # JSON으로 저장
            timestamp = datetime.now().isoformat()
            filename = f"{output_dir}/snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            snapshot = {
                'timestamp': timestamp,
                'coins_count': len(current_data),
                'data': current_data
            }
            
            self.client.save_current_data_json(snapshot, filename)
            return True
        
        except Exception as e:
            logger.error(f"❌ 스냅샷 저장 실패: {e}")
            return False


# 테스트 코드
if __name__ == "__main__":
    # API 키 (실제로는 .env 파일에서 로드)
    API_KEY = None
    API_SECRET = None
    
    # Upbit 클라이언트 초기화
    upbit = UpbitClient(api_key=API_KEY, api_secret=API_SECRET)
    
    # 거래 가능한 코인 조회
    coins = upbit.get_available_coins(limit=10)
    print(f"조회된 코인: {coins}")
    
    # 현재 시세 조회
    if coins:
        ticker = upbit.get_ticker(coins[0])
        print(f"현재 시세: {ticker}")
    
    # OHLCV 데이터 조회
    if coins:
        df = upbit.get_ohlcv(coins[0], timeframe='1m', limit=10)
        if df is not None:
            print(f"\nOHLCV 데이터:\n{df}")
    
    logger.info("✅ 테스트 완료")
