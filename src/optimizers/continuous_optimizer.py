"""
src/optimizer/continuous_optimizer.py
무한 루프 파라미터 최적화 엔진
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer.data_accumulator import DataAccumulator
from optimizer.parameter_validator import ParameterValidator, BacktestResult

logger = logging.getLogger(__name__)

# 기본 파라미터
DEFAULT_PARAMS = {
    'rsi_upper': 70,
    'rsi_lower': 30,
    'ma_period': 20,
    'stop_loss': -0.025,
    'take_profit': 0.05,
    'min_confidence': 0.5
}


class ContinuousOptimizer:
    """
    무한 루프로 파라미터 최적화
    – 과거 + 현재 데이터로 더 좋은 파라미터 탐색
    – 개선되면 즉시 current_params.json 업데이트
    """

    def __init__(self, coins: List[str], optimization_interval: int = 3600):
        """
        Args:
            coins: 최적화할 코인 리스트
            optimization_interval: 최적화 주기 (초, 기본 1시간)
        """
        self.coins = coins
        self.optimization_interval = optimization_interval
        self.accumulators = {coin: DataAccumulator(coin) for coin in coins}
        self.validator = ParameterValidator()
        
        self.current_params = self._load_current_params()
        self.current_result = None
        self.is_running = False
        
        logger.info(f"[ContinuousOptimizer] 초기화: {len(coins)}개 코인")

    def _load_current_params(self) -> Dict:
        """현재 최적 파라미터 로드"""
        params_file = "parameters/current_params.json"
        if os.path.exists(params_file):
            try:
                with open(params_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        logger.warning("[ContinuousOptimizer] 파라미터 파일 없음, 기본값 사용")
        return DEFAULT_PARAMS.copy()

    def _save_current_params(self, params: Dict):
        """현재 파라미터 저장"""
        try:
            os.makedirs("parameters", exist_ok=True)
            with open("parameters/current_params.json", 'w') as f:
                json.dump(params, f, indent=2)
            self.current_params = params
            logger.info("[ContinuousOptimizer] 파라미터 저장 완료")
        except Exception as e:
            logger.error(f"[ContinuousOptimizer] 파라미터 저장 오류: {e}")

    async def start(self):
        """최적화 엔진 시작 (백그라운드 루프)"""
        self.is_running = True
        logger.info("[ContinuousOptimizer] 무한 최적화 루프 시작")
        
        while self.is_running:
            try:
                await self._optimization_cycle()
                await asyncio.sleep(self.optimization_interval)
            except Exception as e:
                logger.error(f"[ContinuousOptimizer] 최적화 사이클 오류: {e}")
                await asyncio.sleep(60)

    async def _optimization_cycle(self):
        """한 주기의 최적화 실행"""
        logger.info("[ContinuousOptimizer] 최적화 사이클 시작")
        
        # 1단계: 현재 파라미터로 백테스트
        current_result = await self._evaluate_params(self.current_params)
        
        if current_result.total_trades == 0:
            logger.warning("[ContinuousOptimizer] 거래 기록 없음, 스킵")
            return
        
        self.current_result = current_result
        logger.info(
            f"[ContinuousOptimizer] 현재 파라미터 성과 – "
            f"승률 {current_result.win_rate:.2%}, 수익률 {current_result.profit_rate:+.2%}"
        )
        
        # 2단계: 새로운 파라미터 후보 생성 (Grid Search)
        candidates = self._generate_parameter_candidates()
        
        best_new_result = current_result
        best_new_params = self.current_params
        
        for idx, candidate_params in enumerate(candidates):
            try:
                new_result = await self._evaluate_params(candidate_params)
                
                # 개선 확인
                improved, reason = self.validator.compare_results(current_result, new_result)
                
                if improved:
                    logger.info(
                        f"[ContinuousOptimizer] 개선 발견 ({idx+1}/{len(candidates)}) – {reason}"
                    )
                    
                    if new_result.win_rate > best_new_result.win_rate or \
                       new_result.profit_rate > best_new_result.profit_rate:
                        best_new_result = new_result
                        best_new_params = candidate_params
                
            except Exception as e:
                logger.error(f"[ContinuousOptimizer] 후보 평가 오류: {e}")
                continue
        
        # 3단계: 더 좋은 파라미터 발견 시 즉시 업데이트
        if best_new_result != current_result:
            logger.info(
                f"[ContinuousOptimizer] 🎉 더 좋은 파라미터 발견! "
                f"승률 {current_result.win_rate:.2%} → {best_new_result.win_rate:.2%}"
            )
            
            self._save_current_params(best_new_params)
            await self._log_optimization_record(best_new_params, best_new_result)
        else:
            logger.info("[ContinuousOptimizer] 이번 주기에 개선된 파라미터 없음")

    async def _evaluate_params(self, params: Dict) -> BacktestResult:
        """파라미터 평가 (모든 코인 백테스트)"""
        total_result = None
        
        for coin in self.coins:
            try:
                accumulator = self.accumulators[coin]
                candles = accumulator.get_latest_candles(limit=1000)
                
                if not candles:
                    logger.debug(f"[ContinuousOptimizer] {coin} 캔들 데이터 없음")
                    continue
                
                result = self.validator.backtest(candles, params)
                
                # 각 코인 결과 누적
                if total_result is None:
                    total_result = result
                else:
                    total_result.win_count += result.win_count
                    total_result.loss_count += result.loss_count
                    total_result.total_trades += result.total_trades
                    total_result.total_profit += result.total_profit
                
            except Exception as e:
                logger.error(f"[ContinuousOptimizer] {coin} 평가 오류: {e}")
                continue
        
        # 전체 승률 & 수익률 재계산
        if total_result and total_result.total_trades > 0:
            total_result.win_rate = total_result.win_count / total_result.total_trades
            total_result.profit_rate = total_result.total_profit / (total_result.win_count + 1) \
                if total_result.win_count > 0 else 0
        
        return total_result or self.validator._empty_result()

    def _generate_parameter_candidates(self, num_candidates: int = 20) -> List[Dict]:
        """
        새로운 파라미터 후보 생성 (Grid Search + Random Mutation)
        """
        candidates = []
        
        # Grid Search: RSI 범위 변동
        for rsi_upper in range(68, 76, 2):  # 68, 70, 72, 74
            for rsi_lower in range(25, 35, 2):  # 25, 27, 29, 31, 33
                if rsi_lower >= rsi_upper:
                    continue
                
                candidate = self.current_params.copy()
                candidate['rsi_upper'] = rsi_upper
                candidate['rsi_lower'] = rsi_lower
                candidates.append(candidate)
        
        # Grid Search: MA 기간 변동
        for ma_period in [15, 20, 25, 30]:
            candidate = self.current_params.copy()
            candidate['ma_period'] = ma_period
            candidates.append(candidate)
        
        # Grid Search: 손절 & 익절 조정
        for stop_loss in [-0.015, -0.020, -0.025, -0.030]:
            for take_profit in [0.04, 0.05, 0.06]:
                candidate = self.current_params.copy()
                candidate['stop_loss'] = stop_loss
                candidate['take_profit'] = take_profit
                candidates.append(candidate)
        
        # Random Mutation: 무작위 조합
        for _ in range(5):
            candidate = self.current_params.copy()
            candidate['rsi_upper'] = random.randint(68, 75)
            candidate['rsi_lower'] = random.randint(25, 32)
            candidate['ma_period'] = random.choice([15, 20, 25, 30])
            candidates.append(candidate)
        
        # 중복 제거
        unique_candidates = []
        seen = set()
        for c in candidates:
            key = (c['rsi_upper'], c['rsi_lower'], c['ma_period'], c['stop_loss'], c['take_profit'])
            if key not in seen:
                unique_candidates.append(c)
                seen.add(key)
        
        logger.info(f"[ContinuousOptimizer] {len(unique_candidates)}개 파라미터 후보 생성")
        return unique_candidates[:num_candidates]

    async def _log_optimization_record(self, params: Dict, result: BacktestResult):
        """최적화 기록 저장"""
        try:
            os.makedirs("data/params", exist_ok=True)
            
            record = {
                'timestamp': datetime.now().isoformat(),
                'params': params,
                'win_rate': result.win_rate,
                'profit_rate': result.profit_rate,
                'total_trades': result.total_trades,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown
            }
            
            records_file = "data/params/optimization_records.json"
            records = []
            
            if os.path.exists(records_file):
                with open(records_file, 'r') as f:
                    records = json.load(f)
            
            records.append(record)
            records = records[-100:]  # 최근 100개만 유지
            
            with open(records_file, 'w') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[ContinuousOptimizer] 최적화 기록 저장: {datetime.now().isoformat()}")
            
        except Exception as e:
            logger.error(f"[ContinuousOptimizer] 기록 저장 오류: {e}")

    def stop(self):
        """최적화 엔진 중지"""
        self.is_running = False
        logger.info("[ContinuousOptimizer] 최적화 엔진 중지")
