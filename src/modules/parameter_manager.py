# src/modules/parameter_manager.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import json
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CoinParameterManager:
    """50개 코인의 파라미터 관리"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.params_file = data_dir / "initial_params.json"
    
    def initialize_default_params(self, coins: list) -> Dict[str, Dict]:
        """50개 코인의 기본 파라미터 생성"""
        default_params = {}
        
        for coin in coins:
            default_params[coin] = {
                "weights": {f"indicator_{i}": 1.0/30 for i in range(30)},  # 30개 지표, 균등 분배
                "entry_threshold": 65,
                "stop_loss_pct": -2.0,
                "take_profit_pct": 5.0,
                "position_size_pct": 10.0,
                "max_positions": 5
            }
        
        return default_params
    
    def save_params(self, params: Dict[str, Dict], filename: str = None):
        """파라미터를 JSON으로 저장"""
        if filename is None:
            filename = self.params_file
        else:
            filename = self.data_dir / filename
        
        with open(filename, 'w') as f:
            json.dump(params, f, indent=2)
        
        logger.info(f"파라미터 저장: {filename}")
    
    def load_params(self, filename: str = None) -> Dict[str, Dict]:
        """JSON에서 파라미터 로드"""
        if filename is None:
            filename = self.params_file
        else:
            filename = self.data_dir / filename
        
        if not filename.exists():
            logger.error(f"파라미터 파일 없음: {filename}")
            return {}
        
        with open(filename, 'r') as f:
            params = json.load(f)
        
        logger.info(f"파라미터 로드: {filename}")
        return params
    
    def get_coin_params(self, params: Dict, coin: str) -> Dict:
        """특정 코인의 파라미터 조회"""
        return params.get(coin, {})
    
    def update_coin_params(self, params: Dict, coin: str, new_params: Dict) -> Dict:
        """특정 코인의 파라미터 업데이트"""
        if coin not in params:
            params[coin] = {}
        
        params[coin].update(new_params)
        return params
    
    def validate_params(self, params: Dict) -> bool:
        """파라미터 검증"""
        for coin, coin_params in params.items():
            if 'entry_threshold' not in coin_params:
                logger.error(f"{coin}: entry_threshold 없음")
                return False
            
            # 가중치 합 검증
            if 'weights' in coin_params:
                weights_sum = sum(coin_params['weights'].values())
                if abs(weights_sum - 1.0) > 0.01:
                    logger.error(f"{coin}: 가중치 합이 1.0이 아님 ({weights_sum})")
                    return False
        
        return True

if __name__ == "__main__":
    from config import DATA_DIR, COINS
    
    manager = CoinParameterManager(DATA_DIR)
    
    # 기본 파라미터 생성
    default_params = manager.initialize_default_params(COINS)
    
    # 검증
    is_valid = manager.validate_params(default_params)
    print(f"파라미터 검증: {'✅ 통과' if is_valid else '❌ 실패'}")
    
    # 저장
    manager.save_params(default_params)
    
    # 로드
    loaded_params = manager.load_params()
    print(f"로드된 코인 수: {len(loaded_params)}")
