"""
config.py - 시스템 전체 설정값
모든 파라미터를 한 곳에서 관리
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# ============================================
# 📂 경로 설정
# ============================================
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ============================================
# 🔑 API 키 및 인증
# ============================================
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Google Cloud
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "crypto-trading-system")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "crypto-trading-data")

# ============================================
# 💰 트레이딩 설정
# ============================================
INITIAL_CAPITAL = 500000  # 초기 자본금 (500K KRW)
MAX_POSITIONS = 5  # 최대 동시 포지션 수
POSITION_SIZE_PERCENT = 0.05  # 각 포지션 크기 (5%)

# 손절/익절
STOP_LOSS_PERCENT = 0.07  # 손절 7%
TAKE_PROFIT_PERCENT = 0.15  # 익절 15%
TRAILING_STOP_PERCENT = 0.03  # 트레일링 스탑 3%

# ============================================
# 📊 데이터 수집 설정
# ============================================
TOP_COINS_FOR_ANALYSIS = 50  # 분석할 상위 코인 수
MIN_TRADING_VOLUME = 1_000_000  # 최소 거래량 (1M KRW)

# 타임프레임 (분 단위) - 5분 중심 ⭐
TIMEFRAMES = {
    "1d": "1d",         # 일봉 (추세)
    "4h": "4h",         # 4시간 (모멘텀)
    "1h": "1h",         # 1시간 (신호 강도)
    "15m": "15m",       # 15분
    "5m": "5m"          # 5분 (진입/청산 타이밍) ⭐⭐ 메인
}

# 캔들 개수
CANDLE_LIMIT = {
    "1d": 365,          # 1년
    "4h": 180,          # 30일
    "1h": 100,          # 5일
    "15m": 96,          # 1일 (4개/시간 × 24시간)
    "5m": 288           # 1일 (12개/시간 × 24시간) ⭐
}

# ============================================
# ⏰ 분석 주기 설정 (매우 중요!)
# ============================================
ANALYSIS_INTERVAL_SECONDS = 300  # 5분 (5분봉 기반)

# 각 타임프레임별 업데이트 간격
TIMEFRAME_UPDATE_INTERVALS = {
    "1d": 86400,        # 24시간 (1회/일)
    "4h": 14400,        # 4시간
    "1h": 3600,         # 1시간
    "15m": 900,         # 15분
    "5m": 300           # 5분 ⭐ (매번)
}

# ============================================
# 🎯 다중 타임프레임 가중치
# ============================================
TIMEFRAME_WEIGHTS = {
    "1d": 0.25,         # 일봉: 추세 (25%)
    "4h": 0.25,         # 4시간: 모멘텀 (25%)
    "1h": 0.20,         # 1시간: 신호 (20%)
    "15m": 0.15,        # 15분 (15%)
    "5m": 0.15          # 5분: 진입/청산 타이밍 (15%) ⭐
}

assert sum(TIMEFRAME_WEIGHTS.values()) == 1.0, "타임프레임 가중치 합이 1.0이 아닙니다"

# ============================================
# 📈 기술지표 설정
# ============================================
EMA_PERIODS = [9, 21, 50]       # EMA 기간
RSI_PERIOD = 14                  # RSI 기간
MACD_PERIODS = (12, 26, 9)      # MACD (fast, slow, signal)
BOLLINGER_PERIOD = 20            # Bollinger Band 기간
BOLLINGER_STD = 2                # Bollinger Band 표준편차
ATR_PERIOD = 14                  # ATR 기간
VOLUME_PERIOD = 20               # 거래량 SMA 기간

# ============================================
# 🎯 점수화 설정 (indicator_scorer.py와 동기화)
# ============================================
INDICATOR_WEIGHTS = {
    # EMA 추세 (5%)
    "ema_trend": 0.05,
    
    # RSI (10%)
    "rsi": 0.05,
    "rsi_signal": 0.03,
    "rsi_momentum": 0.02,
    
    # MACD (10%)
    "macd": 0.04,
    "macd_signal": 0.02,
    "macd_histogram": 0.02,
    "macd_momentum": 0.02,
    
    # Bollinger Bands (8%)
    "bb_percent": 0.04,
    "bb_width": 0.04,
    
    # ATR (6%)
    "atr": 0.03,
    "atr_percent": 0.03,
    
    # 거래량 (10%)
    "volume_ratio": 0.04,
    "volume_std": 0.03,
    "price_change": 0.03,
    
    # ADX (8%)
    "adx": 0.04,
    "plus_di": 0.02,
    "minus_di": 0.02,
    
    # Stochastic (7%)
    "stoch_k": 0.03,
    "stoch_d": 0.02,
    "stoch_momentum": 0.02,
    
    # CCI (5%)
    "cci": 0.05,
    
    # ROC (8%)
    "roc_12": 0.03,
    "roc_25": 0.03,
    "roc_avg": 0.02,
    
    # Momentum (8%)
    "momentum_5": 0.02,
    "momentum_10": 0.02,
    "momentum_20": 0.02,
    "momentum_avg": 0.02,
    
    # 추가 지표 (15%) ← 0.10 추가됨
    "price_change_pct": 0.03,
    "is_bullish": 0.03,
    "range_pct": 0.03,
    "volatility": 0.03,
    "williams_r": 0.03,
}

# 검증: 합이 1.0인지 확인
_weights_sum = sum(INDICATOR_WEIGHTS.values())
assert abs(_weights_sum - 1.0) < 0.001, f"가중치 합이 {_weights_sum}입니다 (1.0이어야 함)"

# ============================================
# 🤖 AI 설정
# ============================================
AI_CONFIDENCE_THRESHOLD = 0.65  # AI 신뢰도 기준
AI_CONFIDENCE_THRESHOLD_LEVEL2 = 0.80  # Level 2 (주의)
AI_CONFIDENCE_THRESHOLD_LEVEL3 = 0.90  # Level 3 (위험)

# Claude API
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
CLAUDE_MAX_TOKENS = 500
CLAUDE_TEMPERATURE = 0.7

# 뉴스 분석
NEWS_BATCH_SIZE = 5  # 한 번에 분석할 뉴스 개수
NEWS_CACHE_HOURS = 24  # 뉴스 캐시 유지 시간

# ============================================
# 📊 리스크 관리 설정
# ============================================
# 누적 손실 레벨 (월 누적 기준)
RISK_LEVELS = {
    "NORMAL": {"loss_range": (0, -0.02), "min_score": 70, "min_ai_conf": 0.65, "max_pos": 5},
    "CAUTION": {"loss_range": (-0.02, -0.05), "min_score": 75, "min_ai_conf": 0.80, "max_pos": 3},
    "DANGER": {"loss_range": (-0.05, -0.10), "min_score": 85, "min_ai_conf": 0.90, "max_pos": 1},
    "CRITICAL": {"loss_range": (-0.10, float('-inf')), "min_score": 100, "min_ai_conf": 1.0, "max_pos": 0},
}

# ============================================
# 🎮 시뮬레이션 설정
# ============================================
SIMULATION_CAPITAL = INITIAL_CAPITAL  # 가상 자본금
SLIPPAGE_PERCENT = 0.005  # 슬리피지 0.5%
TRANSACTION_FEE_PERCENT = 0.001  # 거래 수수료 0.1%
EXECUTION_PROBABILITY = 0.95  # 거래 체결 확률 95%

# Walk-Forward 검증
TRAINING_DAYS = 7  # 훈련 기간 (7일)
VALIDATION_DAYS = 3  # 검증 기간 (3일)

# ============================================
# 📅 시장 상태 분류
# ============================================
MARKET_STATES = [
    "STRONG_UPTREND",      # BTC 주도 강한 상승
    "UPTREND",             # 일반적 상승
    "ALTSEASON",           # 알트코인 시즌
    "CONSOLIDATION",       # 횡보
    "DOWNTREND",           # 하강
    "CRASH",               # 급락
    "EXTREME_FEAR",        # 극도 공포
    "EXTREME_GREED",       # 극도 탐욕
    "LOW_VOLUME",          # 거래량 실종
    "NEWS_EVENT"           # 뉴스 이벤트
]

# ============================================
# 🔗 데이터 소스 설정
# ============================================
# Upbit API
UPBIT_BASE_URL = "https://api.upbit.com/v1"

# 뉴스 API
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSAPI_BASE_URL = "https://newsapi.org/v2"

# Fear & Greed Index
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"

# ============================================
# 📝 로깅 설정
# ============================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10_485_760  # 10MB
LOG_BACKUP_COUNT = 10  # 10개 파일 유지

# ============================================
# ⏰ 스케줄 설정
# ============================================
ANALYSIS_INTERVAL_SECONDS = 300  # 5분마다 분석
MARKET_UPDATE_INTERVAL = 60  # 1분마다 시장 데이터 갱신
WEIGHT_UPDATE_DAY = 0  # 월요일 (0 = 월요일, 6 = 일요일)
WEIGHT_UPDATE_HOUR = 9  # 09:00 KST

# ============================================
# 📊 데이터 보관 설정
# ============================================
DATA_RETENTION_DAYS = 90  # 90일 이상 과거 데이터 보관
BACKUP_FREQUENCY_HOURS = 6  # 6시간마다 백업

# ============================================
# 🔍 검증
# ============================================
def validate_config():
    """설정값 검증"""
    errors = []
    
    if not UPBIT_ACCESS_KEY:
        errors.append("❌ UPBIT_ACCESS_KEY가 설정되지 않았습니다")
    if not UPBIT_SECRET_KEY:
        errors.append("❌ UPBIT_SECRET_KEY가 설정되지 않았습니다")
    if not CLAUDE_API_KEY:
        errors.append("❌ CLAUDE_API_KEY가 설정되지 않았습니다")
    if INITIAL_CAPITAL <= 0:
        errors.append("❌ INITIAL_CAPITAL은 0보다 커야 합니다")
    if MAX_POSITIONS <= 0:
        errors.append("❌ MAX_POSITIONS는 0보다 커야 합니다")
    
    if errors:
        for error in errors:
            print(error)
        raise ValueError("설정값 검증 실패")
    
    print("✅ 설정값 검증 완료")

if __name__ == "__main__":
    validate_config()
    print("✅ config.py 로드 성공")
