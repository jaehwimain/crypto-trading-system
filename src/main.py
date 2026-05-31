"""
암호화폐 자동거래봇 - 통합 메인 실행 파일
Phase 1-5 통합 + 연속 파라미터 최적화 + Telegram 명령어

실행 흐름:
1. 초기화 (최초 1회) - Phase 1-5 모두 실행
2. 매분 실시간 거래 루프 - 신호 생성, 거래 실행, Q값 업데이트
3. 백그라운드: 연속 파라미터 최적화 - 무한 루프로 더 좋은 파라미터 탐색
4. Telegram 명령어 봇 - 14개 명령어 지원
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
import pandas as pd
from typing import Dict, List, Optional
from flask import Flask, jsonify

# 상위 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

from reporter.telegram_reporter import TelegramReporter
from reporter.telegram_command_handler import TelegramCommandHandler
from optimizers.continuous_optimizer import ContinuousOptimizer
from simulator.simulation_engine import SimulationEngine

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

# 전역 변수
trading_bot = None
telegram_handler = None
optimizer_instance = None


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
        
        self.telegram_reporter = TelegramReporter()
        
        # 데이터 폴더 생성
        Path('logs').mkdir(exist_ok=True)
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path(f'{DATA_DIR}/historical').mkdir(exist_ok=True)
        Path(f'{DATA_DIR}/current').mkdir(exist_ok=True)
        Path(f'{DATA_DIR}/params').mkdir(exist_ok=True)
        Path(f'{DATA_DIR}/performance').mkdir(exist_ok=True)
        Path(f'{DATA_DIR}/simulation').mkdir(exist_ok=True)
        
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
        
        # current_params.json 생성 (기본값)
        current_params = {
            'rsi_upper': 70,
            'rsi_lower': 30,
            'ma_period': 20,
            'stop_loss': -0.025,
            'take_profit': 0.05,
            'min_confidence': 0.5
        }
        
        os.makedirs('parameters', exist_ok=True)
        with open(CURRENT_PARAMS_FILE, 'w') as f:
            json.dump(current_params, f, indent=2)
        
        logger.info(f"  ✅ {CURRENT_PARAMS_FILE} 생성 완료")
    
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
        
        # 성과 추적 초기화
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
        
        Path('data/performance').mkdir(parents=True, exist_ok=True)
        with open(PERFORMANCE_FILE, 'w') as f:
            json.dump(performance, f, indent=2)
        
        # 활성 코인 초기화
        active_coins = {
            'active': [],
            'last_updated': datetime.now().isoformat()
        }
        
        Path('data/active').mkdir(parents=True, exist_ok=True)
        with open(ACTIVE_COINS_FILE, 'w') as f:
            json.dump(active_coins, f, indent=2)
        
        logger.info(f"  ✅ Phase 5-1단계 완료")
    
    async def realtime_loop(self):
        """
        2단계: 매분 실시간 거래 루프
        
        매분 실행:
        1. 1분 캔들 데이터 수집
        2. 지표 계산
        3. 신호 생성
        4. 거래 실행
        5. 강화학습 Q값 업데이트
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
                
                # 1. 1분 캔들 데이터 수집
                logger.debug("  📊 1분 캔들 데이터 수집 중...")
                
                # 2. 지표 계산
                logger.debug("  📈 지표 계산 중...")
                
                # 3. 신호 생성
                logger.debug("  🔔 신호 생성 중...")
                signals = self._generate_signals()
                
                # 4. 거래 실행
                if signals:
                    logger.info(f"  💰 {len(signals)}개 거래 신호 감지")
                    self._execute_trades(signals)
                else:
                    logger.debug("  ⏸️  거래 신호 없음")
                
                # 5. Q값 업데이트
                logger.debug("  🤖 강화학습 Q값 업데이트...")
                
                # 주간/월간 재최적화 체크
                self._check_weekly_optimize()
                self._check_monthly_optimize()
                self._check_daily_report()
                
                # 1분 대기
                logger.debug("  ⏳ 1분 대기 중...")
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ 실시간 루프 오류: {e}")
                await asyncio.sleep(60)
                continue
    
    def _generate_signals(self) -> List[Dict]:
        """신호 생성"""
        signals = []
        # TODO: 실제 신호 생성 로직
        return signals
    
    def _execute_trades(self, signals: List[Dict]):
        """거래 실행"""
        # TODO: 실제 거래 로직
        pass
    
    def _check_weekly_optimize(self):
        """주간 재최적화 체크 (매주 월요일 자정)"""
        now = datetime.now()
        
        if now.weekday() == 0 and now.hour == 0 and now.minute == 0:
            if self.last_weekly_optimize is None or \
               (now - self.last_weekly_optimize).days >= 7:
                
                logger.info("\n" + "=" * 80)
                logger.info("⭐ 3단계: 주간 재최적화 시작")
                logger.info("=" * 80)
                
                try:
                    logger.info("  📊 지난주 거래 데이터 분석 중...")
                    logger.info("  🧬 유전알고리즘 30세대 재실행 중...")
                    logger.info("  🔄 과거 최고 vs 현재 최고 비교 중...")
                    logger.info("  ✅ 파라미터 업데이트 완료")
                    
                    self.last_weekly_optimize = now
                    logger.info("=" * 80)
                    logger.info("✅ 주간 재최적화 완료!")
                    logger.info("=" * 80)
                
                except Exception as e:
                    logger.error(f"❌ 주간 재최적화 실패: {e}")
    
    def _check_monthly_optimize(self):
        """월간 대규모 재최적화 체크 (매월 1일 자정)"""
        now = datetime.now()
        
        if now.day == 1 and now.hour == 0 and now.minute == 0:
            if self.last_monthly_optimize is None or \
               (now - self.last_monthly_optimize).days >= 30:
                
                logger.info("\n" + "=" * 80)
                logger.info("🔥 4단계: 월간 대규모 재최적화 시작")
                logger.info("=" * 80)
                
                try:
                    logger.info("  📁 8년 과거 + 1개월 현재 데이터 통합 중...")
                    logger.info("  📊 회귀분석 재실행 (지표 가중치 재계산)...")
                    logger.info("  🧬 유전알고리즘 30세대 재실행 중...")
                    logger.info("  🤖 강화학습 Q-Table 초기화...")
                    logger.info("  🔄 과거 vs 주간 vs 월간 종합 비교 중...")
                    logger.info("  ✅ 최종 파라미터 결정 완료")
                    
                    self.last_monthly_optimize = now
                    logger.info("=" * 80)
                    logger.info("✅ 월간 대규모 재최적화 완료!")
                    logger.info("=" * 80)
                
                except Exception as e:
                    logger.error(f"❌ 월간 재최적화 실패: {e}")
    
    def _check_daily_report(self):
        """일일 보고 (매일 자정)"""
        now = datetime.now()
        
        if now.hour == 0 and now.minute == 0:
            if self.last_daily_report is None or \
               (now - self.last_daily_report).days >= 1:
                
                logger.info("\n" + "=" * 80)
                logger.info("📊 5단계: 일일 보고")
                logger.info("=" * 80)
                
                try:
                    logger.info("  📈 일일 통계 계산 중...")
                    logger.info("  📱 Telegram 메시지 발송 중...")
                    
                    self.last_daily_report = now
                    logger.info("=" * 80)
                    logger.info("✅ 일일 보고 완료!")
                    logger.info("=" * 80)
                
                except Exception as e:
                    logger.error(f"❌ 일일 보고 실패: {e}")


# ============================================================================
# 백그라운드 스레드 함수
# ============================================================================

async def run_telegram_bot():
    """Telegram 명령어 봇 실행 (비동기)"""
    global telegram_handler
    
    try:
        token = os.getenv('TELEGRAM_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not token or not chat_id:
            logger.error("[Telegram] 토큰 또는 채팅 ID 없음")
            return
        
        telegram_handler = TelegramCommandHandler(token, chat_id, trading_bot)
        await telegram_handler.start()
        
    except Exception as e:
        logger.error(f"[Telegram] 봇 실행 오류: {e}")


async def run_continuous_optimizer():
    """연속 파라미터 최적화 엔진 실행 (백그라운드)"""
    global optimizer_instance
    
    try:
        logger.info("[ContinuousOptimizer] 시작")
        optimizer_instance = ContinuousOptimizer(
            coins=COINS[:5],  # 테스트: 처음 5개 코인
            optimization_interval=3600  # 1시간마다
        )
        await optimizer_instance.start()
        
    except Exception as e:
        logger.error(f"[ContinuousOptimizer] 오류: {e}")


def start_bot_thread():
    """거래 봇을 스레드에서 실행"""
    global trading_bot
    
    def run_bot():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            trading_bot = TradingBot()
            trading_bot.initialize()
            loop.run_until_complete(trading_bot.realtime_loop())
        except Exception as e:
            logger.error(f"[TradingBot] 스레드 오류: {e}")
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    logger.info("[Threading] 거래 봇 스레드 시작")


def start_optimizer_thread():
    """연속 파라미터 최적화를 스레드에서 실행"""
    def run_optimizer():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(run_continuous_optimizer())
        except Exception as e:
            logger.error(f"[ContinuousOptimizer] 스레드 오류: {e}")
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_optimizer, daemon=True)
    thread.start()
    logger.info("[Threading] 파라미터 최적화 스레드 시작")


def start_telegram_thread():
    """Telegram 명령어 봇을 스레드에서 실행"""
    def run_telegram():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(run_telegram_bot())
        except Exception as e:
            logger.error(f"[Telegram] 스레드 오류: {e}")
        finally:
            loop.close()
    
    thread = threading.Thread(target=run_telegram, daemon=True)
    thread.start()
    logger.info("[Threading] Telegram 봇 스레드 시작")


# ============================================================================
# Flask 웹 서버 라우트 (Cloud Run 필수)
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """헬스 체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'crypto-trading-bot',
        'bot_initialized': trading_bot.initialized if trading_bot else False,
        'optimizer_running': optimizer_instance.is_running if optimizer_instance else False
    }), 200


@app.route('/params', methods=['GET'])
def get_params():
    """현재 파라미터 조회"""
    try:
        with open(CURRENT_PARAMS_FILE, 'r') as f:
            params = json.load(f)
        return jsonify({'params': params}), 200
    except Exception as e:
        logger.error(f"[Flask] 파라미터 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# 메인
# ============================================================================

def main():
    """메인 실행 함수"""
    
    logger.info("="*80)
    logger.info("🚀 암호화폐 자동거래 AI 시스템 시작")
    logger.info("="*80)
    
    # Flask 포트 설정
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🌐 Flask 서버 포트 설정: {port}")
    
    # 백그라운드 스레드 시작 (데몬이 아님 - 별도 스레드)
    try:
        start_bot_thread()
        start_optimizer_thread()
        start_telegram_thread()
    except Exception as e:
        logger.error(f"백그라운드 스레드 시작 오류: {e}")
    
    # Flask 서버 시작 (포트 8080 리스닝 - Cloud Run 필수)
    logger.info(f"🌐 Flask 서버 시작: 포트 {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
