# src/config.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================
# 📂 경로 설정 (중요!)
# ============================================
# src/config.py 파일의 위치
SRC_DIR = Path(__file__).parent.absolute()
# src 상위 (프로젝트 루트)
BASE_DIR = SRC_DIR.parent.absolute()
# 프로젝트 루트의 data 폴더
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# sys.path에 src 추가
sys.path.insert(0, str(SRC_DIR))

# ============================================
# 🔑 API 키
# ============================================
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ============================================
# 💰 거래 설정
# ============================================
INITIAL_CAPITAL = 500000  # 초기 자본금
DEFAULT_POSITION_SIZE_PCT = 10  # 포지션 크기
DEFAULT_STOP_LOSS_PCT = -2.0  # 손절
DEFAULT_TAKE_PROFIT_PCT = 5.0  # 익절
MAX_POSITIONS_PER_COIN = 5  # 코인당 최대 포지션

# ============================================
# 📊 데이터 설정
# ============================================
TIMEFRAME = "1m"  # 1분 캔들
BACKTEST_YEARS = 8  # 백테스트 기간
TOP_COINS = 50  # 분석할 코인 수

# 50개 코인 목록
COINS = [
    "BTC", "ETH", "BNB", "SOL", "ADA", "DOGE", "AVAX", "XRP", "LINK", "MATIC",
    "DOT", "LTC", "UNI", "TRX", "BCH", "PEPE", "ARB", "OP", "ATOM", "XLM",
    "ICP", "NEAR", "CRO", "ALGO", "APE", "BLUR", "FET", "FTX", "HBAR", "ANKR",
    "INJ", "LUNC", "LUNA", "MANA", "SAND", "SHIB", "STETH", "SUI", "TAO", "TON",
    "WBTC", "USDC", "USDT", "DAI", "AAVE", "CURVE", "GMX", "GALA", "RENDER", "STX"
]

# ============================================
# 📈 기술지표 설정
# ============================================
EMA_PERIODS = [9, 21, 50]
RSI_PERIOD = 14
MACD_PERIODS = (12, 26, 9)
BOLLINGER_PERIOD = 20
ATR_PERIOD = 14

# ============================================
# 🔄 회귀분석 설정 (Phase 2)
# ============================================
REGRESSION_TOP_INDICATORS = 15  # 상위 15개 지표만 사용

# ============================================
# 🧬 유전 알고리즘 설정 (Phase 3)
# ============================================
GA_POPULATION_SIZE = 100
GA_GENERATIONS = 30
GA_MUTATION_RATE = 0.05
GA_CROSSOVER_RATE = 0.8

# ============================================
# 🤖 강화학습 설정 (Phase 4)
# ============================================
RL_LEARNING_RATE = 0.01
RL_DISCOUNT_FACTOR = 0.9
RL_EPSILON_START = 0.3
RL_EPSILON_DECAY = 0.99
RL_NUM_STATES = 5**10  # 10개 지표 × 5단계
RL_NUM_ACTIONS = 4  # 스킵, 진입 10%, 15%, 20%

# ============================================
# ⏰ 스케줄 설정
# ============================================
ANALYSIS_INTERVAL_SECONDS = 60  # 1분마다 분석
DAILY_REPORT_HOUR = 0  # 자정
WEEKLY_OPTIMIZE_HOUR = 0  # 월요일 자정

# ============================================
# 📝 로깅 설정
# ============================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
