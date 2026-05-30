# src/main.py
import logging
from pathlib import Path
from config import BASE_DIR, DATA_DIR, COINS, LOG_LEVEL, LOG_FORMAT
from modules.data_loader import DataLoader
from modules.parameter_manager import CoinParameterManager
from modules.performance_tracker import PerformanceTracker

# 로깅 설정
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def initialize_phase1():
    """Phase 1: 기초 인프라 초기화"""
    logger.info("=" * 50)
    logger.info("🚀 Phase 1: 기초 인프라 초기화")
    logger.info("=" * 50)
    
    # 1. DataLoader 초기화
    logger.info("\n1️⃣ 데이터 로더 초기화...")
    data_loader = DataLoader(DATA_DIR)
    
    # 2. ParameterManager 초기화
    logger.info("\n2️⃣ 파라미터 관리자 초기화...")
    param_manager = CoinParameterManager(DATA_DIR)
    
    # 50개 코인 기본 파라미터 생성
    default_params = param_manager.initialize_default_params(COINS)
    
    # 파라미터 검증
    if param_manager.validate_params(default_params):
        logger.info(f"✅ 50개 코인 파라미터 생성 완료")
        param_manager.save_params(default_params)
    else:
        logger.error("❌ 파라미터 검증 실패")
        return False
    
    # 3. PerformanceTracker 초기화
    logger.info("\n3️⃣ 성과 추적 시스템 초기화...")
    tracker = PerformanceTracker(DATA_DIR)
    logger.info("✅ 성과 추적 시스템 준비 완료")
    
    # 4. 데이터 검증
    logger.info("\n4️⃣ 데이터 검증...")
    loaded_coins = 0
    for coin in COINS[:5]:  # 처음 5개 코인만 테스트
        df = data_loader.load_historical_data(coin, limit=100)
        if not df.empty:
            loaded_coins += 1
            logger.info(f"  ✓ {coin}: {len(df)} 행")
        else:
            logger.warning(f"  ✗ {coin}: 데이터 없음")
    
    logger.info(f"\n✅ {loaded_coins}개 코인 데이터 로드 성공")
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ Phase 1 초기화 완료!")
    logger.info("=" * 50)
    
    return True

def main():
    """메인 실행"""
    logger.info(f"시작: {Path(__file__).name}")
    
    # Phase 1 초기화
    success = initialize_phase1()
    
    if not success:
        logger.error("❌ 초기화 실패")
        return
    
    logger.info("\n🎯 다음 단계: Phase 2 (회귀분석) 구현")

if __name__ == "__main__":
    main()
