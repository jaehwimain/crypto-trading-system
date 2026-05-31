"""
src/optimizer/parameter_validator.py
파라미터 백테스트 및 검증
"""

import logging
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """백테스트 결과"""
    win_count: int
    loss_count: int
    win_rate: float
    total_trades: int
    total_profit: float
    profit_rate: float
    sharpe_ratio: float
    max_drawdown: float


class ParameterValidator:
    """
    파라미터를 받아서 백테스트 실행
    – 승률, 수익률 등 지표 계산
    """

    def __init__(self):
        pass

    def backtest(
        self,
        candles: List[Dict],
        params: Dict
    ) -> BacktestResult:
        """
        파라미터로 백테스트 실행
        
        Args:
            candles: 캔들 데이터 리스트 (1분 캔들)
            params: 거래 파라미터
                {
                    'rsi_upper': 70,
                    'rsi_lower': 30,
                    'ma_period': 20,
                    'stop_loss': -0.025,
                    'take_profit': 0.05,
                    'min_confidence': 0.5
                }
        
        Returns:
            BacktestResult
        """
        try:
            df = pd.DataFrame(candles)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            if len(df) < params.get('ma_period', 20) + 14:
                logger.warning("[ParameterValidator] 캔들 데이터 부족")
                return self._empty_result()
            
            # 지표 계산
            df['rsi'] = self._calculate_rsi(df['close'], period=14)
            df['ma'] = df['close'].rolling(window=params['ma_period']).mean()
            
            # 신호 생성
            trades = []
            positions = {}  # coin -> {'entry_price': ..., 'entry_idx': ...}
            
            for idx in range(params['ma_period'] + 14, len(df)):
                price = df.iloc[idx]['close']
                rsi = df.iloc[idx]['rsi']
                ma = df.iloc[idx]['ma']
                
                # 매수 신호
                if rsi < params['rsi_lower'] and price < ma:
                    if 'position' not in positions:
                        positions['position'] = {
                            'entry_price': price,
                            'entry_idx': idx,
                            'max_price': price
                        }
                
                # 매도 신호 (기존 포지션이 있으면)
                if 'position' in positions:
                    pos = positions['position']
                    pos['max_price'] = max(pos['max_price'], price)
                    
                    # 익절
                    profit_rate = (price - pos['entry_price']) / pos['entry_price']
                    if profit_rate >= params['take_profit']:
                        trades.append({
                            'entry_price': pos['entry_price'],
                            'exit_price': price,
                            'profit_rate': profit_rate,
                            'profit': price - pos['entry_price'],
                            'type': 'win' if profit_rate > 0 else 'loss'
                        })
                        del positions['position']
                    
                    # 손절
                    elif profit_rate <= params['stop_loss']:
                        trades.append({
                            'entry_price': pos['entry_price'],
                            'exit_price': price,
                            'profit_rate': profit_rate,
                            'profit': price - pos['entry_price'],
                            'type': 'loss'
                        })
                        del positions['position']
                    
                    # 매도 신호 (RSI > 70)
                    elif rsi > params['rsi_upper']:
                        trades.append({
                            'entry_price': pos['entry_price'],
                            'exit_price': price,
                            'profit_rate': profit_rate,
                            'profit': price - pos['entry_price'],
                            'type': 'win' if profit_rate > 0 else 'loss'
                        })
                        del positions['position']
            
            # 결과 계산
            if not trades:
                return self._empty_result()
            
            win_count = sum(1 for t in trades if t['type'] == 'win')
            loss_count = len(trades) - win_count
            total_profit = sum(t['profit'] for t in trades)
            profit_rate = total_profit / (trades[0]['entry_price'] * len(trades)) if trades else 0
            
            result = BacktestResult(
                win_count=win_count,
                loss_count=loss_count,
                win_rate=win_count / len(trades) if trades else 0,
                total_trades=len(trades),
                total_profit=total_profit,
                profit_rate=profit_rate,
                sharpe_ratio=self._calculate_sharpe(trades),
                max_drawdown=self._calculate_max_drawdown(trades)
            )
            
            logger.info(
                f"[ParameterValidator] 백테스트 결과 – "
                f"거래 {result.total_trades}건, 승률 {result.win_rate:.2%}, "
                f"수익률 {result.profit_rate:+.2%}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[ParameterValidator] 백테스트 오류: {e}")
            return self._empty_result()

    def _calculate_rsi(self, closes: pd.Series, period: int = 14) -> pd.Series:
        """RSI 계산"""
        deltas = closes.diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        
        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    def _calculate_sharpe(self, trades: List[Dict], risk_free_rate: float = 0.0) -> float:
        """Sharpe 지수"""
        if not trades:
            return 0
        
        returns = [t['profit_rate'] for t in trades]
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0
        
        sharpe = (avg_return - risk_free_rate) / std_dev
        return sharpe

    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """최대 낙폭"""
        if not trades:
            return 0
        
        cumulative_profit = 0
        peak = 0
        max_drawdown = 0
        
        for trade in trades:
            cumulative_profit += trade['profit']
            if cumulative_profit > peak:
                peak = cumulative_profit
            
            drawdown = (peak - cumulative_profit) / (peak + 1)
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown

    def _empty_result(self) -> BacktestResult:
        """빈 결과 반환"""
        return BacktestResult(
            win_count=0,
            loss_count=0,
            win_rate=0,
            total_trades=0,
            total_profit=0,
            profit_rate=0,
            sharpe_ratio=0,
            max_drawdown=0
        )

    def compare_results(
        self,
        current: BacktestResult,
        new: BacktestResult
    ) -> Tuple[bool, str]:
        """
        현재 파라미터 vs 새 파라미터 비교
        
        Returns:
            (개선됨, 이유)
        """
        # 승률 개선 3% 이상
        win_rate_improved = (new.win_rate - current.win_rate) >= 0.03
        
        # 수익률 개선 5% 이상
        profit_improved = (new.profit_rate - current.profit_rate) >= 0.05
        
        # 거래 횟수 50% 이상 감소 (노이즈 제거)
        trades_reduced = (current.total_trades - new.total_trades) / (current.total_trades + 1) >= 0.5
        
        if win_rate_improved or profit_improved:
            reason = f"승률 {current.win_rate:.2%} → {new.win_rate:.2%}, 수익률 {current.profit_rate:+.2%} → {new.profit_rate:+.2%}"
            return True, reason
        
        if trades_reduced and new.win_rate >= current.win_rate:
            reason = f"거래 감소 ({current.total_trades} → {new.total_trades}), 승률 유지"
            return True, reason
        
        return False, f"개선 없음 (승률 {new.win_rate:.2%}, 수익률 {new.profit_rate:+.2%})"
