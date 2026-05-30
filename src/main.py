import logging
from pathlib import Path
from config import BASE_DIR, DATA_DIR, COINS, LOG_LEVEL, LOG_FORMAT
from modules.data_loader import DataLoader
from modules.parameter_manager import CoinParameterManager
from modules.performance_tracker import PerformanceTracker
from optimizers.regression_optimizer import RegressionOptimizer

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def initialize_phase1():
    logger.info("=" * 50)
    logger.info("Phase 1: Basic Infrastructure")
    logger.info("=" * 50)
    
    logger.info("\n1. DataLoader initialization...")
    data_loader = DataLoader(DATA_DIR)
    
    logger.info("\n2. Parameter Manager initialization...")
    param_manager = CoinParameterManager(DATA_DIR)
    default_params = param_manager.initialize_default_params(COINS)
    
    if param_manager.validate_params(default_params):
        logger.info("OK: 50 coins parameters created")
        param_manager.save_params(default_params)
    else:
        logger.error("ERROR: Parameter validation failed")
        return False, None
    
    logger.info("\n3. Performance Tracker initialization...")
    tracker = PerformanceTracker(DATA_DIR)
    logger.info("OK: Performance tracker ready")
    
    logger.info("\n4. Data validation...")
    loaded_coins = 0
    for coin in COINS[:5]:
        df = data_loader.load_historical_data(coin, limit=100)
        if not df.empty:
            loaded_coins += 1
            logger.info(f"  OK {coin}: {len(df)} rows")
        else:
            logger.warning(f"  FAIL {coin}: No data")
    
    logger.info(f"\nOK: {loaded_coins} coins loaded")
    logger.info("=" * 50)
    logger.info("Phase 1 initialization complete!")
    logger.info("=" * 50)
    
    return True, data_loader

def run_phase2(data_loader):
    logger.info("\n" + "=" * 50)
    logger.info("Phase 2: Regression Optimization")
    logger.info("=" * 50)
    
    param_manager = CoinParameterManager(DATA_DIR)
    optimizer = RegressionOptimizer(data_loader, None)
    
    test_coins = COINS[:5]
    logger.info(f"\nAnalyzing {len(test_coins)} coins...")
    optimized_params = optimizer.optimize_all_coins(test_coins)
    
    if optimized_params:
        existing_params = param_manager.load_params()
        existing_params.update(optimized_params)
        param_manager.save_params(existing_params, "optimized_params.json")
        logger.info(f"OK: Optimized params saved")
    
    logger.info("=" * 50)
    logger.info("Phase 2 complete!")
    logger.info("=" * 50)
    
    return optimized_params

def main():
    logger.info(f"Starting: {Path(__file__).name}\n")
    
    success, data_loader = initialize_phase1()
    
    if not success or data_loader is None:
        logger.error("ERROR: Phase 1 initialization failed")
        return
    
    logger.info("\nRunning Phase 2 (test with 5 coins)...")
    optimized = run_phase2(data_loader)
    
    if optimized:
        logger.info(f"\nOK: {len(optimized)} coins optimized")
    
    logger.info("\n" + "="*50)
    logger.info("Initialization and optimization complete!")
    logger.info("="*50)

if __name__ == "__main__":
    main()
