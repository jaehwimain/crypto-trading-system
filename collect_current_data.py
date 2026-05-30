import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import os

exchange = ccxt.binance({
    'enableRateLimit': True,
    'rateLimit': 500
})

# 과거 데이터에서 수집한 코인들
COINS_TO_COLLECT = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'SOL/USDT',
    'ADA/USDT', 'DOGE/USDT', 'AVAX/USDT', 'MATIC/USDT', 'LINK/USDT',
    'LTC/USDT', 'UNI/USDT', 'XLIM/USDT', 'ATOM/USDT', 'VET/USDT',
    'ICP/USDT', 'ALGO/USDT', 'ARB/USDT', 'OP/USDT', 'NEAR/USDT',
    'FIL/USDT', 'AAVE/USDT', 'MAKER/USDT', 'CRV/USDT', 'SNX/USDT',
    'GRT/USDT', 'SUSHI/USDT', 'YFI/USDT', 'ZK/USDT', 'BLUR/USDT',
    'RENDER/USDT', 'JUP/USDT', 'STRK/USDT', 'APE/USDT', 'SAND/USDT',
    'MANA/USDT', 'GALA/USDT', 'ENS/USDT', 'PENDLE/USDT', 'LIDO/USDT',
    'GMX/USDT', 'PERP/USDT', 'DYDX/USDT', 'MASK/USDT', 'COMP/USDT',
    'BAL/USDT', 'RDNT/USDT', 'TIA/USDT', 'SEI/USDT', 'ORDI/USDT'
]

def fetch_current_candles(symbol, timeframe='5m', limit=100):
    """현재 5분 캔들 수집 (최근 100개)"""
    try:
        candles = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return candles
    except Exception as e:
        print(f"  ❌ {symbol} 수집 실패: {str(e)[:50]}")
        return None

def candles_to_dataframe(candles, symbol):
    """캔들을 DataFrame으로 변환"""
    if not candles:
        return pd.DataFrame()
    
    df = pd.DataFrame(
        candles,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df['symbol'] = symbol
    
    return df

def append_to_parquet(df, symbol):
    """기존 Parquet에 현재 데이터 추가"""
    if len(df) == 0:
        return False
    
    symbol_clean = symbol.replace('/', '_')
    filename = f'data/current/{symbol_clean}_current.parquet'
    
    os.makedirs('data/current', exist_ok=True)
    
    # 기존 파일 있으면 읽고 병합, 없으면 새로 저장
    if os.path.exists(filename):
        existing_df = pd.read_parquet(filename)
        df = pd.concat([existing_df, df], ignore_index=True)
        df = df.drop_duplicates(subset=['timestamp'], keep='last')
        df = df.sort_values('timestamp').reset_index(drop=True)
    
    df.to_parquet(filename, compression='snappy', index=False)
    return True

def collect_all_current_data():
    """모든 코인의 현재 데이터 수집"""
    print("\n" + "=" * 70)
    print("📊 현재 5분 캔들 데이터 수집")
    print(f"시간: {datetime.utcnow().isoformat()}")
    print("=" * 70)
    
    success_count = 0
    fail_count = 0
    
    for i, symbol in enumerate(COINS_TO_COLLECT, 1):
        print(f"\n[{i:2d}/{len(COINS_TO_COLLECT)}] {symbol:12s}", end=' ')
        
        try:
            candles = fetch_current_candles(symbol, limit=100)
            
            if not candles:
                fail_count += 1
                print("❌")
                continue
            
            df = candles_to_dataframe(candles, symbol)
            
            if append_to_parquet(df, symbol):
                print(f"✅ ({len(candles)} 캔들)")
                success_count += 1
            else:
                fail_count += 1
                print("❌")
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ {str(e)[:30]}")
            fail_count += 1
            continue
    
    print("\n" + "=" * 70)
    print(f"✅ 완료! 성공: {success_count}/{len(COINS_TO_COLLECT)}")
    print("=" * 70)

if __name__ == "__main__":
    collect_all_current_data()
