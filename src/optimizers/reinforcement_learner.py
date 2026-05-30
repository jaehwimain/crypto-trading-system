import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from typing import Dict, Tuple
import logging
import pickle
from collections import defaultdict

logger = logging.getLogger(__name__)

class QLearningAgent:
    """Q-Learning 강화학습 에이전트"""
    
    def __init__(self, num_states: int = 5**10, num_actions: int = 4):
        self.num_states = num_states
        self.num_actions = num_actions
        
        # Q-Table: (state, action) -> Q값
        self.q_table = defaultdict(lambda: np.zeros(num_actions))
        
        # 학습 파라미터
        self.learning_rate = 0.01
        self.discount_factor = 0.9
        self.epsilon = 0.3
        self.epsilon_decay = 0.99
        
        # 통계
        self.episode_rewards = []
        self.episode_count = 0
    
    def discretize_state(self, indicators: Dict[str, float]) -> int:
        """연속적 지표를 이산 상태로 변환"""
        try:
            state_parts = []
            keys = sorted(indicators.keys())[:10]  # 10개 핵심 지표만
            
            for key in keys:
                value = indicators[key]
                # 0~100 범위를 5단계로 변환
                discrete_value = int((value / 100) * 4)
                discrete_value = min(4, max(0, discrete_value))
                state_parts.append(discrete_value)
            
            # 5진법으로 상태 코드 생성
            state = 0
            for part in state_parts:
                state = state * 5 + part
            
            return state
        except:
            return 0
    
    def select_action(self, state: int) -> int:
        """ε-greedy 알고리즘으로 행동 선택"""
        if np.random.random() < self.epsilon:
            # 탐험: 랜덤 행동
            return np.random.randint(0, self.num_actions)
        else:
            # 활용: 최고 Q값 행동
            q_values = self.q_table[state]
            return np.argmax(q_values)
    
    def update_q_value(self, state: int, action: int, reward: float, next_state: int) -> None:
        """Q값 업데이트"""
        current_q = self.q_table[state][action]
        max_next_q = np.max(self.q_table[next_state])
        
        new_q = current_q + self.learning_rate * (
            reward + self.discount_factor * max_next_q - current_q
        )
        
        self.q_table[state][action] = new_q
    
    def learn(self, state: int, action: int, reward: float, next_state: int) -> None:
        """한 스텝 학습"""
        self.update_q_value(state, action, reward, next_state)
        self.episode_rewards.append(reward)
    
    def decay_epsilon(self) -> None:
        """탐험 확률 감소"""
        self.epsilon *= self.epsilon_decay
    
    def save(self, filepath: str) -> None:
        """Q-Table 저장"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.q_table, f)
        logger.info(f"Q-Table saved: {filepath}")
    
    def load(self, filepath: str) -> None:
        """Q-Table 로드"""
        try:
            with open(filepath, 'rb') as f:
                self.q_table = pickle.load(f)
            logger.info(f"Q-Table loaded: {filepath}")
        except:
            logger.warning(f"Q-Table not found: {filepath}")

class ReinforcementLearner:
    """강화학습을 통한 실시간 파라미터 조정"""
    
    def __init__(self, data_loader, config):
        self.data_loader = data_loader
        self.config = config
        self.agents = {}  # 코인별 에이전트
    
    def create_agent(self, coin: str) -> QLearningAgent:
        """코인별 에이전트 생성"""
        agent = QLearningAgent()
        self.agents[coin] = agent
        logger.info(f"Agent created for {coin}")
        return agent
    
    def simulate_trading_episode(self, coin: str, df: pd.DataFrame, agent: QLearningAgent, num_steps: int = 100) -> Dict:
        """한 에피소드 거래 시뮬레이션"""
        try:
            if df.empty or len(df) < num_steps:
                return {"total_reward": 0, "trades": 0, "win_rate": 0}
            
            close = df['close'].astype(float).values
            
            total_reward = 0
            trades = 0
            wins = 0
            
            for step in range(num_steps - 1):
                # 현재 지표 시뮬레이션
                indicators = {
                    f'ind_{i}': np.random.uniform(0, 100) 
                    for i in range(10)
                }
                
                state = agent.discretize_state(indicators)
                action = agent.select_action(state)
                
                # 시뮬레이션 거래
                if action > 0:  # 진입 신호
                    trades += 1
                    
                    # 다음 가격으로 청산
                    entry_price = close[step]
                    exit_price = close[step + 1]
                    profit_pct = ((exit_price - entry_price) / entry_price) * 100
                    
                    # 보상 계산
                    if profit_pct > 0:
                        reward = min(profit_pct, 10)
                        wins += 1
                    else:
                        reward = max(profit_pct, -10)
                    
                    total_reward += reward
                    
                    # 다음 상태
                    next_indicators = {
                        f'ind_{i}': np.random.uniform(0, 100) 
                        for i in range(10)
                    }
                    next_state = agent.discretize_state(next_indicators)
                    
                    # Q값 업데이트
                    agent.learn(state, action, reward, next_state)
                else:
                    # 스킵
                    total_reward += 0
            
            win_rate = (wins / trades * 100) if trades > 0 else 0
            
            return {
                "total_reward": total_reward,
                "trades": trades,
                "win_rate": win_rate
            }
        
        except Exception as e:
            logger.error(f"Episode simulation error: {e}")
            return {"total_reward": 0, "trades": 0, "win_rate": 0}
    
    def train_agent(self, coin: str, num_episodes: int = 10) -> Dict:
        """에이전트 학습"""
        logger.info(f"Training agent for {coin} ({num_episodes} episodes)")
        
        df = self.data_loader.load_historical_data(coin)
        if df.empty:
            logger.warning(f"No data for {coin}")
            return {}
        
        agent = self.create_agent(coin)
        
        best_reward = -float('inf')
        episode_results = []
        
        for episode in range(num_episodes):
            result = self.simulate_trading_episode(coin, df, agent, num_steps=50)
            episode_results.append(result)
            
            total_reward = result["total_reward"]
            if total_reward > best_reward:
                best_reward = total_reward
            
            logger.info(
                f"{coin} Episode {episode+1}: "
                f"Reward={total_reward:.2f}, Trades={result['trades']}, "
                f"WinRate={result['win_rate']:.1f}%"
            )
            
            agent.decay_epsilon()
        
        avg_reward = np.mean([r["total_reward"] for r in episode_results])
        
        return {
            "coin": coin,
            "episodes": num_episodes,
            "best_reward": best_reward,
            "avg_reward": avg_reward,
            "epsilon": agent.epsilon,
            "q_table_size": len(agent.q_table)
        }
    
    def train_all_coins(self, coins: list, num_episodes: int = 10) -> Dict[str, Dict]:
        """모든 코인 학습"""
        logger.info("=" * 50)
        logger.info("Phase 4: Reinforcement Learning")
        logger.info("=" * 50)
        
        training_results = {}
        
        for coin in coins:
            try:
                result = self.train_agent(coin, num_episodes)
                if result:
                    training_results[coin] = result
            except Exception as e:
                logger.error(f"Training error {coin}: {e}")
                continue
        
        logger.info(f"Training complete: {len(training_results)} coins trained")
        logger.info("=" * 50)
        
        return training_results

if __name__ == "__main__":
    from config import DATA_DIR, COINS
    from modules.data_loader import DataLoader
    
    data_loader = DataLoader(DATA_DIR)
    learner = ReinforcementLearner(data_loader, None)
    
    # 테스트: BTC 학습
    result = learner.train_agent("BTC", num_episodes=5)
    print(f"BTC Training Result: {result}")
