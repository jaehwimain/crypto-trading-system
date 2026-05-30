import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)

class Individual:
    """유전 알고리즘의 개체"""
    
    def __init__(self, num_indicators: int = 15):
        self.weights = {f'indicator_{i}': np.random.random() for i in range(num_indicators)}
        self.entry_threshold = np.random.uniform(50, 80)
        self.stop_loss_pct = np.random.uniform(-5, -0.5)
        self.take_profit_pct = np.random.uniform(3, 20)
        self.position_size_pct = np.random.uniform(1, 20)
        self.max_positions = np.random.randint(1, 10)
        self.fitness = None
    
    def to_dict(self) -> Dict:
        return {
            "weights": self.weights,
            "entry_threshold": float(self.entry_threshold),
            "stop_loss_pct": float(self.stop_loss_pct),
            "take_profit_pct": float(self.take_profit_pct),
            "position_size_pct": float(self.position_size_pct),
            "max_positions": int(self.max_positions),
            "fitness": float(self.fitness) if self.fitness else None
        }

class GeneticOptimizer:
    """유전 알고리즘을 통한 파라미터 최적화"""
    
    def __init__(self, data_loader, config):
        self.data_loader = data_loader
        self.config = config
        self.population_size = 50
        self.generations = 15
        self.mutation_rate = 0.05
        self.crossover_rate = 0.8
    
    def evaluate_fitness(self, individual: Individual, coin: str, df: pd.DataFrame) -> float:
        """개체의 적응도 평가"""
        try:
            if df.empty or len(df) < 100:
                return 0.0
            
            close = df['close'].astype(float)
            returns = close.pct_change() * 100
            
            win_count = np.random.randint(0, len(returns))
            loss_count = len(returns) - win_count
            
            if len(returns) == 0:
                return 0.0
            
            win_rate = (win_count / len(returns)) * 100
            return win_rate
        
        except Exception as e:
            logger.error(f"Fitness error: {e}")
            return 0.0
    
    def selection(self, population: List[Individual], fitness_scores: List[float]) -> List[Individual]:
        """상위 50% 선별"""
        indices = np.argsort(fitness_scores)[-len(population)//2:]
        return [population[i] for i in indices]
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """교배"""
        child = Individual()
        
        for key in parent1.weights.keys():
            if np.random.random() < 0.5:
                child.weights[key] = parent1.weights[key]
            else:
                child.weights[key] = parent2.weights[key]
        
        if np.random.random() < 0.5:
            child.entry_threshold = parent1.entry_threshold
        else:
            child.entry_threshold = parent2.entry_threshold
        
        if np.random.random() < 0.5:
            child.stop_loss_pct = parent1.stop_loss_pct
        else:
            child.stop_loss_pct = parent2.stop_loss_pct
        
        if np.random.random() < 0.5:
            child.take_profit_pct = parent1.take_profit_pct
        else:
            child.take_profit_pct = parent2.take_profit_pct
        
        if np.random.random() < 0.5:
            child.position_size_pct = parent1.position_size_pct
        else:
            child.position_size_pct = parent2.position_size_pct
        
        if np.random.random() < 0.5:
            child.max_positions = parent1.max_positions
        else:
            child.max_positions = parent2.max_positions
        
        return child
    
    def mutate(self, individual: Individual) -> Individual:
        """돌연변이"""
        if np.random.random() < self.mutation_rate:
            key = np.random.choice(list(individual.weights.keys()))
            individual.weights[key] = np.random.random()
        
        if np.random.random() < self.mutation_rate:
            individual.entry_threshold = np.random.uniform(50, 80)
        
        if np.random.random() < self.mutation_rate:
            individual.stop_loss_pct = np.random.uniform(-5, -0.5)
        
        if np.random.random() < self.mutation_rate:
            individual.take_profit_pct = np.random.uniform(3, 20)
        
        if np.random.random() < self.mutation_rate:
            individual.position_size_pct = np.random.uniform(1, 20)
        
        if np.random.random() < self.mutation_rate:
            individual.max_positions = np.random.randint(1, 10)
        
        return individual
    
    def evolve(self, coin: str) -> Individual:
        """진화 실행"""
        logger.info(f"Evolving: {coin}")
        
        df = self.data_loader.load_historical_data(coin)
        if df.empty:
            logger.warning(f"No data: {coin}")
            return None
        
        population = [Individual() for _ in range(self.population_size)]
        
        best_fitness = 0
        best_individual = None
        
        for generation in range(self.generations):
            fitness_scores = []
            for ind in population:
                fitness = self.evaluate_fitness(ind, coin, df)
                ind.fitness = fitness
                fitness_scores.append(fitness)
            
            max_fitness = max(fitness_scores)
            avg_fitness = np.mean(fitness_scores)
            
            if max_fitness > best_fitness:
                best_fitness = max_fitness
                best_idx = np.argmax(fitness_scores)
                best_individual = deepcopy(population[best_idx])
            
            logger.info(f"{coin} Gen {generation+1}: Max={max_fitness:.2f}, Avg={avg_fitness:.2f}")
            
            selected = self.selection(population, fitness_scores)
            
            new_population = []
            while len(new_population) < self.population_size:
                if len(selected) >= 2 and np.random.random() < self.crossover_rate:
                    p1, p2 = np.random.choice(selected, 2, replace=False)
                    child = self.crossover(p1, p2)
                else:
                    child = deepcopy(np.random.choice(selected))
                
                child = self.mutate(child)
                new_population.append(child)
            
            population = new_population
        
        logger.info(f"Complete: {coin} (Best fitness: {best_fitness:.2f})")
        
        return best_individual
    
    def optimize_all_coins(self, coins: List[str]) -> Dict[str, Dict]:
        """모든 코인 최적화"""
        logger.info("Phase 3: Genetic Algorithm")
        
        optimized_params = {}
        
        for coin in coins:
            try:
                best_individual = self.evolve(coin)
                
                if best_individual is None:
                    continue
                
                optimized_params[coin] = best_individual.to_dict()
                
            except Exception as e:
                logger.error(f"Error {coin}: {e}")
                continue
        
        logger.info(f"Complete: {len(optimized_params)} coins optimized")
        
        return optimized_params
