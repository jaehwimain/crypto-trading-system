"""
가상 포트폴리오 관리
모의투자 시뮬레이션을 위한 포트폴리오 클래스
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """포지션 정보"""
    coin: str
    entry_price: float
    entry_time: str
    quantity: float
    current_price: float = 0.0
    
    def get_profit_rate(self) -> float:
        """현재 수익률 계산"""
        if self.entry_price <= 0:
            return 0.0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100
    
    def get_profit_amount(self) -> float:
        """현재 수익금 계산"""
        return (self.current_price - self.entry_price) * self.quantity


class VirtualPortfolio:
    """가상 포트폴리오"""
    
    def __init__(self, initial_capital: float):
        """
        초기화
        
        Args:
            initial_capital: 초기 자본금 (예: 100000)
        """
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.positions: Dict[str, Position] = {}
        
        self.trades: List[Dict] = []  # 거래 기록
        self.start_time = datetime.now()
        self.end_time = None
        
        self.total_profit = 0.0
        self.total_trades = 0
        self.win_count = 0
        self.loss_count = 0
        
        logger.info(f"✅ 가상 포트폴리오 생성: {initial_capital:,.0f}원")
    
    def get_portfolio_value(self) -> float:
        """현재 포트폴리오 총 자산 계산"""
        position_value = sum(
            pos.current_price * pos.quantity 
            for pos in self.positions.values()
        )
        return self.current_cash + position_value
    
    def get_profit_rate(self) -> float:
        """현재 수익률 계산"""
        if self.initial_capital <= 0:
            return 0.0
        current_value = self.get_portfolio_value()
        return ((current_value - self.initial_capital) / self.initial_capital) * 100
    
    def buy(self, coin: str, price: float, amount: float) -> bool:
        """
        매수
        
        Args:
            coin: 코인명 (예: 'BTC')
            price: 매수가
            amount: 매수 금액
        
        Returns:
            성공 여부
        """
        if amount > self.current_cash:
            logger.warning(f"❌ 잔액 부족: {amount:,.0f}원 필요, {self.current_cash:,.0f}원 보유")
            return False
        
        quantity = amount / price
        
        # 기존 포지션이 있으면 평균가 계산
        if coin in self.positions:
            old_pos = self.positions[coin]
            new_quantity = old_pos.quantity + quantity
            new_entry_price = (
                (old_pos.entry_price * old_pos.quantity + price * quantity) / new_quantity
            )
            self.positions[coin].quantity = new_quantity
            self.positions[coin].entry_price = new_entry_price
        else:
            self.positions[coin] = Position(
                coin=coin,
                entry_price=price,
                entry_time=datetime.now().isoformat(),
                quantity=quantity,
                current_price=price
            )
        
        self.current_cash -= amount
        self.total_trades += 1
        
        logger.info(f"💰 매수: {coin} {quantity:.6f}개 @ {price:,.0f}원 (금액: {amount:,.0f}원)")
        
        return True
    
    def sell(self, coin: str, price: float, quantity: Optional[float] = None) -> bool:
        """
        매도
        
        Args:
            coin: 코인명
            price: 매도가
            quantity: 매도량 (None이면 전량 매도)
        
        Returns:
            성공 여부
        """
        if coin not in self.positions:
            logger.warning(f"❌ 보유중인 {coin} 포지션 없음")
            return False
        
        position = self.positions[coin]
        
        # 전량 매도 또는 부분 매도
        sell_quantity = quantity if quantity else position.quantity
        
        if sell_quantity > position.quantity:
            logger.warning(f"❌ 매도량 초과: {sell_quantity:.6f}개 (보유: {position.quantity:.6f}개)")
            return False
        
        sell_amount = price * sell_quantity
        profit_amount = (price - position.entry_price) * sell_quantity
        profit_rate = ((price - position.entry_price) / position.entry_price) * 100
        
        # 거래 기록
        trade_record = {
            'coin': coin,
            'entry_price': position.entry_price,
            'exit_price': price,
            'quantity': sell_quantity,
            'entry_time': position.entry_time,
            'exit_time': datetime.now().isoformat(),
            'profit_amount': profit_amount,
            'profit_rate': profit_rate,
            'status': 'WIN' if profit_amount > 0 else 'LOSS'
        }
        self.trades.append(trade_record)
        
        # 통계 업데이트
        self.total_profit += profit_amount
        if profit_amount > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
        
        # 포트폴리오 업데이트
        self.current_cash += sell_amount
        
        if sell_quantity == position.quantity:
            del self.positions[coin]
        else:
            position.quantity -= sell_quantity
        
        status = "✅ WIN" if profit_amount > 0 else "❌ LOSS"
        logger.info(f"🎯 매도: {coin} {sell_quantity:.6f}개 @ {price:,.0f}원 ({profit_rate:+.2f}%) {status}")
        
        return True
    
    def update_price(self, coin: str, current_price: float):
        """
        가격 업데이트
        
        Args:
            coin: 코인명
            current_price: 현재가
        """
        if coin in self.positions:
            self.positions[coin].current_price = current_price
    
    def get_status(self) -> Dict:
        """포트폴리오 상태 반환"""
        elapsed_time = datetime.now() - self.start_time
        minutes = int(elapsed_time.total_seconds() / 60)
        
        total_completed = self.win_count + self.loss_count
        win_rate = (self.win_count / total_completed * 100) if total_completed > 0 else 0.0
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': self.get_portfolio_value(),
            'current_cash': self.current_cash,
            'profit_rate': self.get_profit_rate(),
            'total_profit': self.total_profit,
            'elapsed_minutes': minutes,
            'total_trades': self.total_trades,
            'win_count': self.win_count,
            'loss_count': self.loss_count,
            'win_rate': win_rate,
            'open_positions': len(self.positions),
            'positions': {
                coin: {
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'quantity': pos.quantity,
                    'profit_rate': pos.get_profit_rate(),
                    'profit_amount': pos.get_profit_amount()
                }
                for coin, pos in self.positions.items()
            }
        }
    
    def get_summary(self) -> Dict:
        """최종 결과 요약"""
        self.end_time = datetime.now()
        elapsed_time = self.end_time - self.start_time
        
        total_completed = self.win_count + self.loss_count
        win_rate = (self.win_count / total_completed * 100) if total_completed > 0 else 0.0
        
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'elapsed_seconds': elapsed_time.total_seconds(),
            'elapsed_minutes': int(elapsed_time.total_seconds() / 60),
            'initial_capital': self.initial_capital,
            'final_value': self.get_portfolio_value(),
            'total_profit': self.total_profit,
            'profit_rate': self.get_profit_rate(),
            'total_trades': self.total_trades,
            'win_count': self.win_count,
            'loss_count': self.loss_count,
            'win_rate': win_rate,
            'trades': self.trades,
            'success': self.get_profit_rate() >= 5.0 or self.get_profit_rate() <= -5.0
        }
