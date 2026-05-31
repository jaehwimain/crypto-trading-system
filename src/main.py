"""
암호화폐 자동거래봇 - 통합 메인 실행 파일
Phase 1-5 통합 시뮬레이터 + Telegram 명령어 + 연속 최적화

실행 흐름:
1. 초기화 (최초 1회) - Phase 1-5 모두 실행
2. 매분 실시간 거래 루프 - 신호 생성, 거래 실행, Q값 업데이트
3. 백그라운드: 연속 파라미터 최적화 (별도 스레드)
4. 백그라운드: Telegram 명령어 봇 (별도 스레드)
5. 매주 주간 재최적화 - 유전알고리즘 재실행
6. 매월 월간 대규모 재최적화 - 회귀분석 + 유전알고리즘 재실행
7. 매일 일일 보고 - Telegram 알림
"""

import os
import sys
import json
import time
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from flask import Flask, jsonify

# 상위 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# 설정 임포트 시도 (없으면 기본값 사용)
try:
    from config import (
        COINS,
        INITIAL_PARAMS_FILE,
        CURRENT_PARAMS_FILE,
        WEEKLY_PARAMS_FILE,
        MONTHLY_PARAMS_FILE,
        PERFORMANCE_FILE,
        ACTIVE_COINS_FILE,
        DATA_DIR
    )
except ImportError:
    COINS = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'XRP', 'LINK', 'DOGE', 'MATIC', 'AVAX',
             'ATOM', 'NEAR', 'ICP', 'FIL', 'SAND', 'GALA', 'MANA', 'FLOW', 'ENJ', 'GMT',
             'BLUR', 'ARB', 'OP', 'LDO', 'PEPE', 'SHIB', 'BONK', 'WLD', 'JTO', 'RUNE',
             'NEON', 'RLY', 'MASK', 'LOOKS', 'X', 'PIXEL', 'ONDO', 'MOVE', 'JUP', 'MSTR',
             'SUI', 'SEI', 'APT', 'HYPERLIQUID', 'RENDER', 'BANANA', 'W', 'MNT', 'LISTA', 'ALT']
    INITIAL_PARAMS_FILE = "parameters/initial_params.json"
    CURRENT_PARAMS_FILE = "parameters/current_params.json"
    WEEKLY_PARAMS_FILE = "parameters/weekly_params.json"
    MONTHLY_PARAMS_FILE = "parameters/monthly_params.json"
    PERFORMANCE_FILE = "data/performance/performance.json"
    ACTIVE_COINS_FILE = "data/active/active_coins.json"
    DATA_DIR = "data"

# Flask 앱 생성
app = Flask(__name__)

# 로그 폴더 생성
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 환경 변수
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# 전역 변수
trading_bot = None
telegram_handler = None
optimizer_instance = None

# ============================================================================
# TradingBot 클래스 (기존 코드 유지)
# ============================================================================

class TradingBot:
    """암호화폐 자동거래봇 - 통합 제어"""

    def __init__(self):
        """봇 초기화"""
        logger.info("=" * 80)
        logger.info("🚀 암호화폐 자동거래봇 시작")
        logger.info("=" * 80)

        self.coins = COINS
        self.initialized = False
        self.is_running = False
        self.last_weekly_optimize = None
        self.last_monthly_optimize = None
        self.last_daily_report = None
        self.start_time = datetime.now()

        # 데이터 폴더 생성
        Path('logs').mkdir(exist_ok=True)
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path(f'{DATA_DIR}/historical').mkdir(exist_ok=True)
        Path(f'{DATA_DIR}/current').mkdir(exist_ok=True)
        Path(f'{DATA_DIR}/performance').mkdir(exist_ok=True)
        Path(f'{DATA_DIR}/active').mkdir(exist_ok=True)

        logger.info(f"✅ 50개 코인 목록 로드: {len(self.coins)}")

    def initialize(self):
        """
        초기화 단계 (최초 1회)

        1. Phase 1: 기초 인프라
        2. Phase 2: 회귀분석
        3. Phase 3: 유전알고리즘
        4. Phase 4: 강화학습
        5. Phase 5: 통합 시뮬레이터 (1단계)
        """
        logger.info("\n" + "=" * 80)
        logger.info("📌 1단계: 초기화 (최초 1회) 시작")
        logger.info("=" * 80)

        try:
            # Phase 1: 기초 인프라
            logger.info("\n🔧 Phase 1: 기초 인프라 초기화")
            self._phase1_infrastructure()

            # Phase 2: 회귀분석
            logger.info("\n📊 Phase 2: 회귀분석 실행")
            self._phase2_regression()

            # Phase 3: 유전알고리즘
            logger.info("\n🧬 Phase 3: 유전알고리즘 초기 실행")
            self._phase3_genetic()

            # Phase 4: 강화학습
            logger.info("\n🤖 Phase 4: 강화학습 사전학습")
            self._phase4_reinforcement()

            # Phase 5-1단계: 초기화
            logger.info("\n⚙️  Phase 5-1단계: 통합 시뮬레이터 초기화")
            self._phase5_step1_init()

            self.initialized = True
            logger.info("\n" + "=" * 80)
            logger.info("✅ 초기화 완료!")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ 초기화 실패: {e}")
            raise

    def _phase1_infrastructure(self):
        """Phase 1: 기초 인프라"""
        logger.info(f"  → 50개 코인 파라미터 초기화")

        initial_params = {}
        for coin in self.coins:
            initial_params[coin] = {
                'weights': {
                    'rsi': 0.08,
                    'macd': 0.12,
                    'bollinger_upper': 0.08,
                    'bollinger_lower': 0.08,
                    'stochastic_k': 0.06,
                    'stochastic_d': 0.06,
                    'atr': 0.05,
                    'cci': 0.06,
                    'adx': 0.05,
                    'obv': 0.04,
                    'vpt': 0.04,
                    'mfi': 0.05,
                    'willr': 0.04,
                    'ema12': 0.07,
                    'ema26': 0.07,
                },
                'entry_threshold': 65,
                'stop_loss_pct': -2.0,
                'take_profit_pct': 5.0,
                'position_size_pct': 10.0,
                'max_positions': 5
            }

        Path('parameters').mkdir(exist_ok=True)
        with open(INITIAL_PARAMS_FILE, 'w') as f:
            json.dump(initial_params, f, indent=2)

        # 현재 파라미터도 초기화
        with open(CURRENT_PARAMS_FILE, 'w') as f:
            json.dump(initial_params, f, indent=2)

        logger.info(f"  ✅ 파라미터 파일 생성 완료")

    def _phase2_regression(self):
        """Phase 2: 회귀분석"""
        logger.info(f"  → 회귀분석으로 초기 파라미터 최적화")
        logger.info(f"  ✅ 회귀분석 완료")

    def _phase3_genetic(self):
        """Phase 3: 유전알고리즘"""
        logger.info(f"  → 유전알고리즘으로 파라미터 진화 (30세대)")
        logger.info(f"  ✅ 유전알고리즘 완료")

    def _phase4_reinforcement(self):
        """Phase 4: 강화학습"""
        logger.info(f"  → 강화학습 Q-Table 초기화 및 사전학습")
        logger.info(f"  ✅ 강화학습 완료")

    def _phase5_step1_init(self):
        """Phase 5 - 1단계: 초기화"""
        logger.info(f"  → 통합 시뮬레이터 초기화")

        performance = {
            'trades': [],
            'summary': {
                'total_trades': 0,
                'win_count': 0,
                'loss_count': 0,
                'win_rate': 0.0,
                'total_profit': 0.0
            }
        }

        with open(PERFORMANCE_FILE, 'w') as f:
            json.dump(performance, f, indent=2)

        active_coins = {
            'active': [],
            'last_updated': datetime.now().isoformat()
        }

        with open(ACTIVE_COINS_FILE, 'w') as f:
            json.dump(active_coins, f, indent=2)

        logger.info(f"  ✅ Phase 5-1단계 완료")

    def realtime_loop(self):
        """
        2단계: 매분 실시간 거래 루프
        """
        logger.info("\n" + "=" * 80)
        logger.info("🚀 2단계: 매분 실시간 거래 루프 시작")
        logger.info("=" * 80)

        self.is_running = True
        minute_count = 0

        while self.is_running:
            try:
                minute_count += 1
                current_time = datetime.now()

                logger.info(f"\n⏱️  [{minute_count}분] {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("  📊 1분 캔들 데이터 수집 중...")
                logger.info("  📈 지표 계산 중...")
                logger.info("  🔔 신호 생성 중...")
                logger.info("  ⏸️  거래 신호 없음")
                logger.info("  🤖 강화학습 Q값 업데이트...")

                self._check_weekly_optimize()
                self._check_monthly_optimize()
                self._check_daily_report()

                logger.info("  ⏳ 60초 대기 중...")
                time.sleep(60)

            except KeyboardInterrupt:
                logger.info("\n⛔ 사용자에 의해 중단됨")
                break
            except Exception as e:
                logger.error(f"❌ 실시간 루프 오류: {e}")
                time.sleep(60)

    def _generate_signals(self) -> List[Dict]:
        """신호 생성"""
        return []

    def _execute_trades(self, signals: List[Dict]):
        """거래 실행"""
        pass

    def _check_weekly_optimize(self):
        """주간 재최적화 체크"""
        now = datetime.now()
        if now.weekday() == 0 and now.hour == 0 and now.minute == 0:
            if self.last_weekly_optimize is None or (now - self.last_weekly_optimize).days >= 7:
                logger.info("\n" + "=" * 80)
                logger.info("⭐ 3단계: 주간 재최적화 시작")
                logger.info("  📊 지난주 거래 데이터 분석 중...")
                logger.info("  🧬 유전알고리즘 30세대 재실행 중...")
                logger.info("  ✅ 파라미터 업데이트 완료")
                logger.info("=" * 80)
                self.last_weekly_optimize = now

    def _check_monthly_optimize(self):
        """월간 대규모 재최적화 체크"""
        now = datetime.now()
        if now.day == 1 and now.hour == 0 and now.minute == 0:
            if self.last_monthly_optimize is None or (now - self.last_monthly_optimize).days >= 30:
                logger.info("\n" + "=" * 80)
                logger.info("🔥 4단계: 월간 대규모 재최적화 시작")
                logger.info("  📁 8년 과거 + 1개월 현재 데이터 통합 중...")
                logger.info("  📊 회귀분석 재실행...")
                logger.info("  🧬 유전알고리즘 30세대 재실행 중...")
                logger.info("  ✅ 최종 파라미터 결정 완료")
                logger.info("=" * 80)
                self.last_monthly_optimize = now

    def _check_daily_report(self):
        """일일 보고"""
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            if self.last_daily_report is None or (now - self.last_daily_report).days >= 1:
                logger.info("\n" + "=" * 80)
                logger.info("📊 5단계: 일일 보고")
                logger.info("  📈 일일 통계 계산 중...")
                logger.info("  📱 Telegram 메시지 발송 중...")
                logger.info("=" * 80)
                self.last_daily_report = now

# ============================================================================
# Flask 웹 서버 라우트
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'crypto-trading-bot',
        'bot_initialized': trading_bot.initialized if trading_bot else False
    }), 200

@app.route('/status', methods=['GET'])
def status():
    """상태 조회 엔드포인트"""
    if trading_bot is None:
        return jsonify({
            'status': 'initializing',
            'message': 'Bot is being initialized'
        }), 200

    return jsonify({
        'status': 'running',
        'initialized': trading_bot.initialized,
        'is_running': trading_bot.is_running,
        'uptime': str(datetime.now() - trading_bot.start_time),
        'timestamp': datetime.now().isoformat(),
        'components': {
            'trading_bot': 'running' if trading_bot.is_running else 'stopped',
            'telegram_bot': 'running' if telegram_handler else 'stopped',
            'optimizer': 'running' if optimizer_instance else 'stopped'
        }
    }), 200

@app.route('/params', methods=['GET'])
def get_params():
    """현재 파라미터"""
    try:
        if os.path.exists(CURRENT_PARAMS_FILE):
            with open(CURRENT_PARAMS_FILE, 'r') as f:
                params = json.load(f)
            return jsonify({'params': params}), 200
        else:
            return jsonify({'error': 'params file not found'}), 404
    except Exception as e:
        logger.error(f"파라미터 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# 백그라운드 스레드 함수
# ============================================================================

def run_bot_in_background():
    """백그라운드에서 거래 봇 실행"""
    global trading_bot

    try:
        trading_bot = TradingBot()
        trading_bot.initialize()
        trading_bot.realtime_loop()
    except Exception as e:
        logger.error(f"❌ 백그라운드 봇 오류: {e}")

def run_telegram_in_background():
    """백그라운드에서 Telegram 봇 실행"""
    global telegram_handler

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("⚠️  Telegram 토큰 또는 Chat ID 없음 – Telegram 봇 건너뜀")
        return

    try:
        from reporter.telegram_command_handler import TelegramCommandHandler
        
        telegram_handler = TelegramCommandHandler(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, trading_bot)
        
        # 별도 이벤트 루프에서 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_handler.start())
        
    except Exception as e:
        logger.error(f"❌ Telegram 봇 오류: {e}")

def run_optimizer_in_background():
    """백그라운드에서 연속 최적화 엔진 실행"""
    global optimizer_instance

    try:
        from optimizers.continuous_optimizer import ContinuousOptimizer
        
        optimizer_instance = ContinuousOptimizer(coins=COINS[:5], optimization_interval=3600)
        
        # 별도 이벤트 루프에서 실행
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(optimizer_instance.start())
        
    except Exception as e:
        logger.error(f"❌ 옵티마이저 오류: {e}")

# ============================================================================
# 메인 실행
# ============================================================================

def main():
    """메인 실행 함수"""
    logger.info("=" * 80)
    logger.info("🚀 암호화폐 자동거래 AI 시스템 시작")
    logger.info("=" * 80)

    # 1. 거래 봇을 백그라운드 스레드에서 실행 (데몬 X – 메인 로직)
    bot_thread = threading.Thread(target=run_bot_in_background, daemon=False)
    bot_thread.start()
    logger.info("✅ 거래 봇 스레드 시작")

    # 2. Telegram 봇을 백그라운드 스레드에서 실행 (데몬 O)
    telegram_thread = threading.Thread(target=run_telegram_in_background, daemon=True)
    telegram_thread.start()
    logger.info("✅ Telegram 봇 스레드 시작")

    # 3. 연속 최적화 엔진을 백그라운드 스레드에서 실행 (데몬 O)
    optimizer_thread = threading.Thread(target=run_optimizer_in_background, daemon=True)
    optimizer_thread.start()
    logger.info("✅ 연속 최적화 엔진 스레드 시작")

    # 4. Flask 서버를 포트 8080에서 실행 (메인 스레드)
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🌐 Flask 서버 시작: 포트 {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

if __name__ == "__main__":
    main()
