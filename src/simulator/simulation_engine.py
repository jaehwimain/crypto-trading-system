"""
src/simulator/simulation_engine.py
모의투자 엔진 – 실제 거래 로직과 동일한 방식으로 작동
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# 기존 모듈 임포트
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporter.telegram_reporter import TelegramReporter
from simulator.virtual_portfolio import VirtualPortfolio, Position
from api.upbit_client import UpbitClient

# 로깅 설정
logger = logging.getLogger(__name__)

@dataclass
class SimulationConfig:
    """모의투자 설정"""
    initial_capital: float
    coins: List[str]
    params: Dict = None
    target_profit_rate: float = 0.05  # +5%
    target_loss_rate: float = -0.05   # -5%
    check_interval: int = 60  # 60초마다 확인


class SimulationEngine:
    """
    실제 거래 엔진과 동일한 로직으로 모의투자 실행
    – 실제 TradingBot의 signal 생성 및 포지션 크기 결정 로직 재사용
    """

    _active_simulation: Optional['SimulationEngine'] = None

    def __init__(self, config: SimulationConfig, trading_bot_instance=None):
        """
        Args:
            config: SimulationConfig 객체
            trading_bot_instance: 실제 TradingBot 인스턴스 (신호 생성, 파라미터 참조용)
        """
        self.config = config
        self.trading_bot = trading_bot_instance
        self.portfolio = VirtualPortfolio(config.initial_capital)
        self.telegram_reporter = TelegramReporter()
        self.upbit_client = UpbitClient()
        
        # 설정: 파라미터가 제공되지 않으면 현재 최적 파라미터 로드
        if config.params is None:
            self.config.params = self._load_current_params()
        
        self.start_time = datetime.now()
        self.is_running = False
        self.stop_reason = None
        self.simulation_id = self._generate_simulation_id()
        
        logger.info(f"[모의투자] 시뮬레이션 ID: {self.simulation_id}")
        logger.info(f"[모의투자] 초기 자본: {config.initial_capital:,.0f} KRW")
        logger.info(f"[모의투자] 코인 수: {len(config.coins)}")
        logger.info(f"[모의투자] 파라미터: {self.config.params}")

    def _load_current_params(self) -> Dict:
        """현재 최적 파라미터 로드"""
        params_file = "parameters/current_params.json"
        if os.path.exists(params_file):
            with open(params_file, 'r') as f:
                return json.load(f)
        else:
            logger.warning("현재 파라미터 파일 없음, 기본값 사용")
            return {
                "rsi_upper": 70,
                "rsi_lower": 30,
                "ma_period": 20,
                "stop_loss": -0.025,
                "take_profit": 0.05,
                "min_confidence": 0.5
            }

    def _generate_simulation_id(self) -> str:
        """모의투자 세션 ID 생성"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    async def start(self):
        """모의투자 시작"""
        if self.is_running:
            logger.warning("[모의투자] 이미 진행 중인 시뮬레이션이 있습니다.")
            return False
        
        self.is_running = True
        SimulationEngine._active_simulation = self
        logger.info(f"[모의투자] 시작 – {self.portfolio.get_portfolio_value():,.0f} KRW")
        
        # Telegram에 시작 알림
        await self.telegram_reporter.send_simulation_start_response(
            self.portfolio.initial_capital
        )
        
        # 거래 루프 시작
        await self._execute_trading_loop()
        
        return True

    async def _execute_trading_loop(self):
        """
        모의투자 거래 루프
        – 실제 거래 엔진의 신호 생성·거래 실행 로직을 재사용
        """
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 각 코인에 대해 신호 생성 및 거래 실행
                for coin in self.config.coins:
                    try:
                        # 1. 현재 가격 조회
                        current_price = await self.upbit_client.get_current_price(coin)
                        if current_price is None:
                            logger.warning(f"[모의투자] {coin} 가격 조회 실패")
                            continue
                        
                        # 2. 포트폴리오의 기존 포지션 가격 업데이트
                        self.portfolio.update_price(coin, current_price)
                        
                        # 3. 신호 생성 (실제 TradingBot 로직 사용)
                        signal = await self._generate_signal(coin, current_price)
                        
                        if signal is None:
                            continue
                        
                        signal_type = signal['type']  # 'BUY', 'SELL', 'HOLD'
                        confidence = signal.get('confidence', 0)
                        
                        # 4. 최소 신뢰도 확인
                        min_confidence = self.config.params.get('min_confidence', 0.5)
                        if confidence < min_confidence:
                            logger.debug(f"[모의투자] {coin} 신뢰도 낮음 ({confidence:.2f})")
                            continue
                        
                        # 5. 거래 실행
                        if signal_type == 'BUY':
                            await self._execute_buy(coin, current_price, confidence)
                        elif signal_type == 'SELL':
                            await self._execute_sell(coin, current_price, confidence)
                        
                    except Exception as e:
                        logger.error(f"[모의투자] {coin} 처리 중 오류: {e}")
                        continue
                
                # 6. 수익률 확인 및 자동 종료 확인
                profit_rate = self.portfolio.get_profit_rate()
                elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
                
                logger.info(
                    f"[모의투자] 현황 – 수익률: {profit_rate:+.2%} | "
                    f"자산: {self.portfolio.get_portfolio_value():,.0f} KRW | "
                    f"경과: {int(elapsed_seconds / 60)}분"
                )
                
                # 목표 수익률 달성 확인
                if profit_rate >= self.config.target_profit_rate:
                    self.stop_reason = f"목표 수익률 달성 (+{self.config.target_profit_rate:.1%})"
                    await self.stop()
                    break
                
                # 손실 한도 확인
                if profit_rate <= self.config.target_loss_rate:
                    self.stop_reason = f"손실 한도 도달 ({self.config.target_loss_rate:.1%})"
                    await self.stop()
                    break
                
                # 대기
                await asyncio.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"[모의투자] 거래 루프 오류: {e}")
                await asyncio.sleep(5)

    async def _generate_signal(self, coin: str, current_price: float) -> Optional[Dict]:
        """
        신호 생성
        – 실제 TradingBot의 신호 생성 로직을 그대로 사용
        """
        if self.trading_bot is None:
            # TradingBot이 없으면 간단한 신호 생성 (RSI 기반)
            return await self._simple_signal_rsi(coin, current_price)
        
        # 실제 TradingBot의 신호 생성 메서드 호출 (존재하면)
        try:
            signal = await self.trading_bot._generate_signal_for_coin(coin)
            return signal
        except AttributeError:
            # 메서드가 없으면 기본 신호 생성
            return await self._simple_signal_rsi(coin, current_price)

    async def _simple_signal_rsi(self, coin: str, current_price: float) -> Optional[Dict]:
        """
        기본 신호 생성 (RSI 기반)
        – 실제 파라미터 사용
        """
        try:
            # 1분 캔들 데이터 조회
            candles = await self.upbit_client.get_candles(coin, interval='1m', limit=100)
            if not candles or len(candles) < 14:
                return None
            
            # RSI 계산
            rsi = self._calculate_rsi(candles)
            
            rsi_lower = self.config.params.get('rsi_lower', 30)
            rsi_upper = self.config.params.get('rsi_upper', 70)
            
            if rsi < rsi_lower:
                return {
                    'type': 'BUY',
                    'coin': coin,
                    'price': current_price,
                    'confidence': (rsi_lower - rsi) / rsi_lower,  # RSI가 낮을수록 신뢰도 ↑
                    'indicator': f'RSI={rsi:.2f}'
                }
            
            if rsi > rsi_upper:
                return {
                    'type': 'SELL',
                    'coin': coin,
                    'price': current_price,
                    'confidence': (rsi - rsi_upper) / (100 - rsi_upper),  # RSI가 높을수록 신뢰도 ↑
                    'indicator': f'RSI={rsi:.2f}'
                }
            
            return {'type': 'HOLD', 'coin': coin, 'confidence': 0}
            
        except Exception as e:
            logger.error(f"[모의투자] RSI 신호 생성 오류 ({coin}): {e}")
            return None

    def _calculate_rsi(self, candles: List[Dict], period: int = 14) -> float:
        """RSI 계산"""
        closes = [c['close'] for c in candles]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    async def _execute_buy(self, coin: str, current_price: float, confidence: float):
        """
        매수 실행
        – 현재 보유 자금으로 자동 계산된 수량 매수
        """
        try:
            # 포트폴리오의 현금에서 매수 가능 금액 계산
            available_cash = self.portfolio.current_cash
            
            # 매수에 사용할 금액 (현금의 일정 비율, 예: 10%)
            buy_amount = available_cash * 0.1
            
            if buy_amount < 5000:  # 최소 5,000 KRW
                logger.debug(f"[모의투자] {coin} 매수 금액 부족 ({buy_amount:,.0f} KRW)")
                return
            
            # 매수
            self.portfolio.buy(coin, current_price, buy_amount)
            logger.info(
                f"[모의투자] BUY {coin} @ {current_price:,.0f} KRW "
                f"| 금액: {buy_amount:,.0f} KRW | 신뢰도: {confidence:.2%}"
            )
            
        except Exception as e:
            logger.error(f"[모의투자] {coin} 매수 오류: {e}")

    async def _execute_sell(self, coin: str, current_price: float, confidence: float):
        """
        매도 실행
        – 보유 포지션이 있으면 전체 매도
        """
        try:
            if coin not in self.portfolio.positions:
                logger.debug(f"[모의투자] {coin} 보유 포지션 없음")
                return
            
            position = self.portfolio.positions[coin]
            quantity = position.quantity
            
            # 매도
            self.portfolio.sell(coin, current_price, quantity)
            logger.info(
                f"[모의투자] SELL {coin} @ {current_price:,.0f} KRW "
                f"| 수량: {quantity:.4f} | 신뢰도: {confidence:.2%}"
            )
            
        except Exception as e:
            logger.error(f"[모의투자] {coin} 매도 오류: {e}")

    async def stop(self, reason: str = None):
        """모의투자 중지 및 결과 보고"""
        if not self.is_running:
            logger.warning("[모의투자] 실행 중인 시뮬레이션이 없습니다.")
            return
        
        self.is_running = False
        if reason:
            self.stop_reason = reason
        
        # 최종 요약
        summary = self.portfolio.get_summary()
        
        logger.info(f"[모의투자] 중지 – 사유: {self.stop_reason}")
        logger.info(
            f"[모의투자] 결과 – 수익률: {summary['profit_rate']:+.2%} | "
            f"최종 자산: {summary['final_value']:,.0f} KRW | "
            f"거래 횟수: {summary['total_trades']} | "
            f"승률: {summary['win_rate']:.2%}"
        )
        
        # 결과 저장
        await self._save_results(summary)
        
        # Telegram 보고
        await self.telegram_reporter.send_simulation_stop_response(summary)
        
        SimulationEngine._active_simulation = None

    async def _save_results(self, summary: Dict):
        """모의투자 결과 DB/파일에 저장"""
        try:
            results_dir = "data/simulation"
            os.makedirs(results_dir, exist_ok=True)
            
            result_record = {
                'simulation_id': self.simulation_id,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'elapsed_time_minutes': (datetime.now() - self.start_time).total_seconds() / 60,
                'initial_capital': self.config.initial_capital,
                'final_value': summary['final_value'],
                'profit': summary['profit'],
                'profit_rate': summary['profit_rate'],
                'total_trades': summary['total_trades'],
                'win_count': summary['win_count'],
                'loss_count': summary['loss_count'],
                'win_rate': summary['win_rate'],
                'current_params': self.config.params,
                'stop_reason': self.stop_reason,
                'trades': summary['trades']
            }
            
            # JSON 파일 저장
            result_file = f"{results_dir}/{self.simulation_id}.json"
            with open(result_file, 'w') as f:
                json.dump(result_record, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[모의투자] 결과 저장: {result_file}")
            
        except Exception as e:
            logger.error(f"[모의투자] 결과 저장 오류: {e}")

    async def get_status(self) -> Dict:
        """현재 모의투자 상태 반환"""
        if not self.is_running:
            return {'status': 'inactive'}
        
        portfolio_status = self.portfolio.get_status()
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'status': 'active',
            'simulation_id': self.simulation_id,
            'elapsed_minutes': int(elapsed_seconds / 60),
            'profit_rate': self.portfolio.get_profit_rate(),
            'portfolio_value': self.portfolio.get_portfolio_value(),
            'current_cash': self.portfolio.current_cash,
            'total_trades': len(self.portfolio.trades),
            'win_rate': portfolio_status.get('win_rate', 0),
            'positions': {
                coin: {
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'profit_rate': pos.get_profit_rate()
                }
                for coin, pos in self.portfolio.positions.items()
            }
        }

    async def get_summary(self) -> Dict:
        """모의투자 최종 요약"""
        return self.portfolio.get_summary()

    @staticmethod
    def get_active_simulation() -> Optional['SimulationEngine']:
        """현재 활성 시뮬레이션 반환"""
        return SimulationEngine._active_simulation

    @staticmethod
    async def start_simulation(
        initial_capital: float,
        coins: List[str] = None,
        params: Dict = None,
        trading_bot_instance = None
    ) -> bool:
        """새 모의투자 시작"""
        if SimulationEngine._active_simulation is not None:
            logger.warning("[모의투자] 이미 진행 중인 시뮬레이션이 있습니다.")
            return False
        
        if coins is None:
            coins = ['BTC', 'ETH', 'SOL', 'ADA', 'XRP']
        
        config = SimulationConfig(
            initial_capital=initial_capital,
            coins=coins,
            params=params
        )
        
        engine = SimulationEngine(config, trading_bot_instance)
        await engine.start()
        return True

    @staticmethod
    async def stop_simulation(reason: str = "사용자 요청") -> Optional[Dict]:
        """활성 모의투자 중지"""
        if SimulationEngine._active_simulation is None:
            logger.warning("[모의투자] 실행 중인 시뮬레이션이 없습니다.")
            return None
        
        await SimulationEngine._active_simulation.stop(reason)
        return await SimulationEngine._active_simulation.get_summary()
