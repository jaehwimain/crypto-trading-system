import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class UnifiedSimulator:
    """Phase 2, 3, 4를 통합한 최종 시뮬레이터"""
    
    def __init__(self, data_loader, param_manager, performance_tracker):
        self.data_loader = data_loader
        self.param_manager = param_manager
        self.performance_tracker = performance_tracker
    
    def simulate_all_coins(self, coins: List[str]) -> Dict:
        """모든 코인에 대해 통합 시뮬레이션 실행"""
        logger.info("=" * 50)
        logger.info("Phase 5: Unified Simulator")
        logger.info("=" * 50)
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_coins": len(coins),
            "coins_data": {},
            "summary": {}
        }
        
        total_profit = 0
        total_trades = 0
        total_wins = 0
        
        for coin in coins:
            try:
                coin_result = self._simulate_coin(coin)
                
                if coin_result:
                    results["coins_data"][coin] = coin_result
                    total_profit += coin_result.get("profit", 0)
                    total_trades += coin_result.get("trades", 0)
                    total_wins += coin_result.get("wins", 0)
                    
                    logger.info(
                        f"{coin}: Trades={coin_result['trades']}, "
                        f"Profit={coin_result['profit']:.2f}%, "
                        f"WinRate={coin_result['win_rate']:.1f}%"
                    )
            except Exception as e:
                logger.error(f"Error simulating {coin}: {e}")
                continue
        
        # 요약 통계
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        results["summary"] = {
            "total_trades": total_trades,
            "total_wins": total_wins,
            "total_losses": total_trades - total_wins,
            "win_rate": round(win_rate, 2),
            "total_profit": round(total_profit, 2),
            "avg_profit_per_coin": round(total_profit / len(coins), 2) if len(coins) > 0 else 0
        }
        
        logger.info("=" * 50)
        logger.info(f"Summary: Trades={total_trades}, WinRate={win_rate:.1f}%, Profit={total_profit:.2f}%")
        logger.info("=" * 50)
        
        return results
    
    def _simulate_coin(self, coin: str) -> Dict:
        """단일 코인 시뮬레이션"""
        df = self.data_loader.load_historical_data(coin, limit=200)
        
        if df.empty or len(df) < 50:
            return None
        
        close = df['close'].astype(float).values
        
        # 간단한 거래 시뮬레이션
        trades = 0
        wins = 0
        losses = 0
        total_profit = 0
        
        # 진입 신호: 랜덤 (실제로는 지표 기반)
        entry_probability = 0.15
        
        for i in range(len(close) - 10):
            if np.random.random() < entry_probability:
                # 진입
                entry_price = close[i]
                
                # 10봉 후 청산 (실제로는 손절/익절 기반)
                exit_price = close[i + 10]
                
                profit_pct = ((exit_price - entry_price) / entry_price) * 100
                
                trades += 1
                total_profit += profit_pct
                
                if profit_pct > 0:
                    wins += 1
                else:
                    losses += 1
        
        win_rate = (wins / trades * 100) if trades > 0 else 0
        
        return {
            "coin": coin,
            "trades": trades,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "profit": round(total_profit, 2),
            "avg_profit_per_trade": round(total_profit / trades, 2) if trades > 0 else 0
        }
