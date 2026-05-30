# src/modules/performance_tracker.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """거래 기록 및 성과 추적"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.performance_file = data_dir / "realtime_performance.json"
        self.trades: List[Dict] = []
    
    def record_trade(self, coin: str, entry_price: float, exit_price: float, 
                     entry_time: str, exit_time: str, method: str = "unknown"):
        """거래 기록"""
        profit_loss_pct = ((exit_price - entry_price) / entry_price) * 100
        
        trade = {
            "coin": coin,
            "entry_time": entry_time,
            "entry_price": entry_price,
            "exit_time": exit_time,
            "exit_price": exit_price,
            "profit_loss_pct": round(profit_loss_pct, 2),
            "method": method,
            "recorded_at": datetime.utcnow().isoformat()
        }
        
        self.trades.append(trade)
        logger.info(f"{coin} 거래 기록: {profit_loss_pct:.2f}%")
    
    def calculate_metrics(self) -> Dict:
        """성과 지표 계산"""
        if not self.trades:
            return {
                "total_trades": 0,
                "win_count": 0,
                "loss_count": 0,
                "win_rate": 0.0,
                "total_profit": 0.0,
                "avg_profit_pct": 0.0
            }
        
        profit_losses = [t["profit_loss_pct"] for t in self.trades]
        wins = [p for p in profit_losses if p > 0]
        losses = [p for p in profit_losses if p <= 0]
        
        return {
            "total_trades": len(self.trades),
            "win_count": len(wins),
            "loss_count": len(losses),
            "win_rate": round(len(wins) / len(self.trades) * 100, 2),
            "total_profit": round(sum(profit_losses), 2),
            "avg_profit_pct": round(sum(profit_losses) / len(self.trades), 2)
        }
    
    def save_performance(self, filename: str = None):
        """성과 저장"""
        if filename is None:
            filename = self.performance_file
        else:
            filename = self.data_dir / filename
        
        data = {
            "trades": self.trades,
            "summary": self.calculate_metrics(),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"성과 저장: {filename}")
    
    def load_performance(self, filename: str = None):
        """성과 로드"""
        if filename is None:
            filename = self.performance_file
        else:
            filename = self.data_dir / filename
        
        if not filename.exists():
            logger.warning(f"성과 파일 없음: {filename}")
            return {"trades": [], "summary": {}}
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.trades = data.get("trades", [])
        logger.info(f"성과 로드: {len(self.trades)} 거래")
        
        return data
    
    def get_daily_summary(self) -> Dict:
        """일일 요약"""
        today = datetime.utcnow().date().isoformat()
        today_trades = [t for t in self.trades if t["recorded_at"].startswith(today)]
        
        if not today_trades:
            return {"date": today, "trades": 0, "profit": 0.0, "win_rate": 0.0}
        
        profit_losses = [t["profit_loss_pct"] for t in today_trades]
        wins = len([p for p in profit_losses if p > 0])
        
        return {
            "date": today,
            "trades": len(today_trades),
            "profit": round(sum(profit_losses), 2),
            "win_rate": round(wins / len(today_trades) * 100, 2)
        }

if __name__ == "__main__":
    from config import DATA_DIR
    
    tracker = PerformanceTracker(DATA_DIR)
    
    # 테스트: 거래 기록
    tracker.record_trade("BTC", 65000, 65300, "2026-05-30T10:00:00Z", "2026-05-30T11:00:00Z", "regression")
    tracker.record_trade("ETH", 3000, 2910, "2026-05-30T10:15:00Z", "2026-05-30T11:15:00Z", "regression")
    
    # 성과 계산 및 저장
    metrics = tracker.calculate_metrics()
    print(f"성과: {metrics}")
    
    tracker.save_performance()
