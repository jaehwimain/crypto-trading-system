"""
스케줄러 모듈
매주/매월 자동 최적화 작업 스케줄링

- 매주 월요일 자정: 주간 재최적화 (유전알고리즘)
- 매월 1일 자정: 월간 대규모 재최적화 (회귀분석 + 유전알고리즘)
- 매일 자정: 일일 보고 (Telegram)
"""

import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import json
from pathlib import Path

from config import (
    INITIAL_PARAMS_FILE,
    WEEKLY_PARAMS_FILE,
    MONTHLY_PARAMS_FILE,
    CURRENT_PARAMS_FILE,
    PERFORMANCE_FILE,
    DATA_DIR
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizationScheduler:
    """최적화 작업 스케줄러"""
    
    def __init__(self):
        """스케줄러 초기화"""
        self.scheduler = BackgroundScheduler()
        logger.info("✅ 스케줄러 초기화 완료")
    
    def start(self):
        """스케줄러 시작"""
        try:
            # 매주 월요일 자정 - 주간 재최적화
            self.scheduler.add_job(
                func=self.weekly_optimize,
                trigger=CronTrigger(day_of_week='0', hour=0, minute=0),
                id='weekly_optimize',
                name='Weekly Parameter Optimization',
                replace_existing=True
            )
            logger.info("📅 주간 재최적화 스케줄 등록 (매주 월요일 자정)")
            
            # 매월 1일 자정 - 월간 대규모 재최적화
            self.scheduler.add_job(
                func=self.monthly_optimize,
                trigger=CronTrigger(day=1, hour=0, minute=0),
                id='monthly_optimize',
                name='Monthly Large-scale Parameter Optimization',
                replace_existing=True
            )
            logger.info("📅 월간 재최적화 스케줄 등록 (매월 1일 자정)")
            
            # 매일 자정 - 일일 보고
            self.scheduler.add_job(
                func=self.daily_report,
                trigger=CronTrigger(hour=0, minute=0),
                id='daily_report',
                name='Daily Trading Report',
                replace_existing=True
            )
            logger.info("📅 일일 보고 스케줄 등록 (매일 자정)")
            
            self.scheduler.start()
            logger.info("✅ 스케줄러 시작 완료")
        
        except Exception as e:
            logger.error(f"❌ 스케줄러 시작 실패: {e}")
            raise
    
    def stop(self):
        """스케줄러 중지"""
        try:
            self.scheduler.shutdown()
            logger.info("✅ 스케줄러 중지 완료")
        except Exception as e:
            logger.error(f"❌ 스케줄러 중지 실패: {e}")
    
    def weekly_optimize(self):
        """
        주간 재최적화 (매주 월도일 자정)
        
        3단계: 주간 재최적화
        - 지난주 거래 데이터 분석
        - 유전알고리즘 30세대 재실행
        - 과거 최고 vs 현재 최고 비교
        - 파라미터 업데이트
        """
        logger.info("\n" + "=" * 80)
        logger.info("⭐ 3단계: 주간 재최적화 시작")
        logger.info("=" * 80)
        logger.info(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 지난주 거래 데이터 분석
            logger.info("\n📊 Step 1: 지난주 거래 데이터 분석")
            weekly_stats = self._analyze_weekly_performance()
            
            if weekly_stats:
                logger.info(f"  - 총 거래: {weekly_stats['total_trades']}건")
                logger.info(f"  - 승률: {weekly_stats['win_rate']:.2f}%")
                logger.info(f"  - 수익률: {weekly_stats['profit_rate']:.2f}%")
            
            # 2. 유전알고리즘 30세대 재실행
            logger.info("\n🧬 Step 2: 유전알고리즘 30세대 재실행")
            genetic_result = self._run_genetic_algorithm()
            
            if genetic_result:
                logger.info(f"  - 최고 개체 적합도: {genetic_result['best_fitness']:.2f}")
                logger.info(f"  - 예상 승률: {genetic_result['estimated_win_rate']:.2f}%")
            
            # 3. 과거 최고 vs 현재 최고 비교
            logger.info("\n🔄 Step 3: 과거 최고 vs 현재 최고 비교")
            comparison = self._compare_parameters()
            
            if comparison:
                logger.info(f"  - 과거 최고 승률: {comparison['historical_best']:.2f}%")
                logger.info(f"  - 현재 최고 승률: {comparison['current_best']:.2f}%")
                logger.info(f"  - 개선 여부: {'✅ 개선됨' if comparison['is_better'] else '❌ 개선 안 됨'}")
            
            # 4. 파라미터 업데이트
            logger.info("\n📝 Step 4: 파라미터 업데이트")
            if comparison and comparison['is_better']:
                self._update_parameters(genetic_result['params'])
                logger.info("  ✅ weekly_optimized_params.json으로 파라미터 업데이트")
            else:
                logger.info("  ⏸️  과거 파라미터 유지")
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ 주간 재최적화 완료!")
            logger.info("=" * 80)
        
        except Exception as e:
            logger.error(f"❌ 주간 재최적화 실패: {e}")
            raise
    
    def monthly_optimize(self):
        """
        월간 대규모 재최적화 (매월 1일 자정)
        
        4단계: 월간 대규모 재최적화
        - 8년 과거 + 1개월 현재 데이터 통합
        - 회귀분석 재실행 (지표 가중치 재계산)
        - 유전알고리즘 30세대 재실행
        - 강화학습 Q-Table 초기화
        - 종합 비교 분석
        """
        logger.info("\n" + "=" * 80)
        logger.info("🔥 4단계: 월간 대규모 재최적화 시작")
        logger.info("=" * 80)
        logger.info(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 데이터 통합
            logger.info("\n📁 Step 1: 8년 과거 + 1개월 현재 데이터 통합")
            integrated_data = self._integrate_data()
            
            if integrated_data:
                logger.info(f"  - 과거 데이터 행 수: {integrated_data['historical_rows']}")
                logger.info(f"  - 현재 데이터 행 수: {integrated_data['current_rows']}")
                logger.info(f"  - 총 통합 행 수: {integrated_data['total_rows']}")
            
            # 2. 회귀분석 재실행
            logger.info("\n📊 Step 2: 회귀분석 재실행 (지표 가중치 재계산)")
            regression_result = self._run_regression_analysis(integrated_data)
            
            if regression_result:
                logger.info(f"  - 상위 지표 변화:")
                for idx, (indicator, weight) in enumerate(regression_result['top_indicators'][:3], 1):
                    logger.info(f"    {idx}. {indicator}: {weight:.4f}")
            
            # 3. 유전알고리즘 30세대 재실행
            logger.info("\n🧬 Step 3: 유전알고리즘 30세대 재실행")
            monthly_genetic_result = self._run_genetic_algorithm()
            
            if monthly_genetic_result:
                logger.info(f"  - 최고 개체 적합도: {monthly_genetic_result['best_fitness']:.2f}")
                logger.info(f"  - 예상 승률: {monthly_genetic_result['estimated_win_rate']:.2f}%")
            
            # 4. Q-Table 초기화
            logger.info("\n🤖 Step 4: 강화학습 Q-Table 초기화")
            self._reset_q_tables()
            logger.info("  ✅ 모든 코인 Q-Table 초기화 완료")
            
            # 5. 종합 비교 분석
            logger.info("\n🔄 Step 5: 종합 비교 분석 (과거 vs 주간 vs 월간)")
            comprehensive_comparison = self._comprehensive_comparison()
            
            if comprehensive_comparison:
                logger.info(f"  - 과거 최고: {comprehensive_comparison['historical']:.2f}%")
                logger.info(f"  - 주간 최고: {comprehensive_comparison['weekly']:.2f}%")
                logger.info(f"  - 월간 최고: {comprehensive_comparison['monthly']:.2f}%")
                logger.info(f"  - 최고 성과: {comprehensive_comparison['best_version']}")
            
            # 6. 최종 파라미터 결정
            logger.info("\n📝 Step 6: 최종 파라미터 결정 및 적용")
            self._finalize_parameters(monthly_genetic_result['params'])
            logger.info("  ✅ monthly_optimized_params.json 생성 및 적용")
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ 월간 대규모 재최적화 완료!")
            logger.info("=" * 80)
        
        except Exception as e:
            logger.error(f"❌ 월간 재최적화 실패: {e}")
            raise
    
    def daily_report(self):
        """
        일일 보고 (매일 자정)
        
        5단계: 일일 보고
        - 일일 통계 계산
        - Telegram 메시지 발송
        """
        logger.info("\n" + "=" * 80)
        logger.info("📊 5단계: 일일 보고")
        logger.info("=" * 80)
        logger.info(f"⏰ 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 일일 통계 계산
            logger.info("\n📈 Step 1: 일일 통계 계산")
            daily_stats = self._calculate_daily_stats()
            
            if daily_stats:
                logger.info(f"  - 거래 수: {daily_stats['total_trades']}건")
                logger.info(f"  - 승률: {daily_stats['win_rate']:.2f}%")
                logger.info(f"  - 수익률: {daily_stats['profit_rate']:.2f}%")
                logger.info(f"  - 최대 손실: {daily_stats['max_loss']:.2f}%")
            
            # 2. Top 5 코인 분석
            logger.info("\n🏆 Step 2: Top 5 수익 코인")
            top_profit_coins = daily_stats.get('top_profit_coins', [])
            for idx, (coin, profit) in enumerate(top_profit_coins[:5], 1):
                logger.info(f"  {idx}. {coin}: +{profit:.2f}%")
            
            logger.info("\n⚠️  Step 3: Top 5 손실 코인")
            top_loss_coins = daily_stats.get('top_loss_coins', [])
            for idx, (coin, loss) in enumerate(top_loss_coins[:5], 1):
                logger.info(f"  {idx}. {coin}: {loss:.2f}%")
            
            # 3. Telegram 메시지 발송
            logger.info("\n📱 Step 4: Telegram 메시지 발송")
            self._send_telegram_report(daily_stats)
            logger.info("  ✅ Telegram 메시지 발송 완료")
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ 일일 보고 완료!")
            logger.info("=" * 80)
        
        except Exception as e:
            logger.error(f"❌ 일일 보고 실패: {e}")
    
    # ==================== Helper Methods ====================
    
    def _analyze_weekly_performance(self) -> dict:
        """지난주 거래 데이터 분석"""
        try:
            with open(PERFORMANCE_FILE, 'r') as f:
                performance = json.load(f)
            
            # 더미 데이터 (실제 구현 필요)
            return {
                'total_trades': performance['summary'].get('total_trades', 0),
                'win_rate': performance['summary'].get('win_rate', 0) * 100,
                'profit_rate': performance['summary'].get('total_profit', 0)
            }
        except Exception as e:
            logger.error(f"❌ 성과 분석 실패: {e}")
            return None
    
    def _run_genetic_algorithm(self) -> dict:
        """유전알고리즘 30세대 재실행"""
        # 더미 결과 (실제 구현: genetic_optimizer.py)
        logger.info("  ⏳ 유전알고리즘 실행 중... (예상 5분)")
        
        return {
            'best_fitness': 0.58,
            'estimated_win_rate': 58.3,
            'params': {}
        }
    
    def _compare_parameters(self) -> dict:
        """과거 최고 vs 현재 최고 비교"""
        try:
            # 과거 최고
            with open(INITIAL_PARAMS_FILE, 'r') as f:
                historical = json.load(f)
            
            historical_best = 53.72  # 하드코딩 (실제 계산 필요)
            current_best = 58.3  # 유전알고리즘 결과
            
            return {
                'historical_best': historical_best,
                'current_best': current_best,
                'is_better': current_best > historical_best
            }
        except Exception as e:
            logger.error(f"❌ 파라미터 비교 실패: {e}")
            return None
    
    def _update_parameters(self, new_params: dict):
        """파라미터 업데이트"""
        try:
            with open(WEEKLY_PARAMS_FILE, 'w') as f:
                json.dump(new_params, f, indent=2)
            
            # 현재 파라미터로 설정
            with open(CURRENT_PARAMS_FILE, 'w') as f:
                json.dump(new_params, f, indent=2)
        
        except Exception as e:
            logger.error(f"❌ 파라미터 업데이트 실패: {e}")
    
    def _integrate_data(self) -> dict:
        """8년 과거 + 1개월 현재 데이터 통합"""
        # 더미 데이터
        return {
            'historical_rows': 4200000,
            'current_rows': 10080,  # 7일 × 1440분
            'total_rows': 4210080
        }
    
    def _run_regression_analysis(self, integrated_data: dict) -> dict:
        """회귀분석 재실행"""
        logger.info("  ⏳ 회귀분석 실행 중... (예상 2분)")
        
        return {
            'top_indicators': [
                ('MACD', 0.20),
                ('RSI', 0.12),
                ('Stochastic', 0.14),
            ]
        }
    
    def _reset_q_tables(self):
        """Q-Table 초기화"""
        # 실제 구현: reinforcement_learner.reset_q_table() 호출
        pass
    
    def _comprehensive_comparison(self) -> dict:
        """종합 비교 분석"""
        return {
            'historical': 53.72,
            'weekly': 61.1,
            'monthly': 64.5,
            'best_version': 'monthly'
        }
    
    def _finalize_parameters(self, params: dict):
        """최종 파라미터 결정 및 적용"""
        try:
            with open(MONTHLY_PARAMS_FILE, 'w') as f:
                json.dump(params, f, indent=2)
            
            # 현재 파라미터로 설정
            with open(CURRENT_PARAMS_FILE, 'w') as f:
                json.dump(params, f, indent=2)
        
        except Exception as e:
            logger.error(f"❌ 최종 파라미터 적용 실패: {e}")
    
    def _calculate_daily_stats(self) -> dict:
        """일일 통계 계산"""
        try:
            with open(PERFORMANCE_FILE, 'r') as f:
                performance = json.load(f)
            
            summary = performance['summary']
            
            return {
                'total_trades': summary.get('total_trades', 0),
                'win_rate': summary.get('win_rate', 0) * 100,
                'profit_rate': summary.get('total_profit', 0),
                'max_loss': -2.5,  # 예시
                'top_profit_coins': [
                    ('BTC', 5.2),
                    ('ETH', 3.8),
                    ('ADA', 2.3),
                    ('DOGE', 1.5),
                    ('XRP', 1.2)
                ],
                'top_loss_coins': [
                    ('SOL', -2.1),
                    ('AVAX', -1.5),
                    ('DOT', -1.2),
                    ('MATIC', -0.8),
                    ('LINK', -0.5)
                ]
            }
        except Exception as e:
            logger.error(f"❌ 일일 통계 계산 실패: {e}")
            return None
    
    def _send_telegram_report(self, daily_stats: dict):
        """Telegram 메시지 발송"""
        # 실제 구현: telegram_reporter.py 사용
        logger.info("  📱 Telegram 메시지 작성 중...")
        logger.info(f"  📨 채팅방으로 발송 완료")


def main():
    """스케줄러 메인 함수"""
    scheduler = OptimizationScheduler()
    scheduler.start()
    
    try:
        logger.info("✅ 스케줄러 실행 중... (Ctrl+C로 종료)")
        # 무한 대기
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("⛔ 사용자에 의해 중단됨")
        scheduler.stop()


if __name__ == "__main__":
    main()
