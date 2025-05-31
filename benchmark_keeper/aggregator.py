"""Defines methods to aggregate results from multiple benchmarks, possibly by ranking runs"""

from typing import List, Dict, Any, Mapping, Callable
from abc import ABC, abstractmethod
from functools import reduce

class Aggregator(ABC):
    @abstractmethod
    def aggregate(self, results: List[Mapping[str, Mapping[str, Any]]]) -> List[float]:
        """
        Aggregates benchmark results from multiple runs.

        Args:
            results (List[Mapping[str, Any]]): List of benchmark results where each result is a mapping of benchmark names to their metrics.

        Returns:
            List[float]: A list of aggregated metrics for each benchmark.
        """
        pass

    def unit(self) -> str:
        """
        Returns the unit of the aggregated metrics.
        This can be overridden by subclasses to provide specific units.
        
        Returns:
            str: The unit of the aggregated metrics.
        """
        return "unit"
    
    def lower_is_better(self) -> bool:
        """
        Indicates whether lower values are better for the aggregated metrics.
        This can be overridden by subclasses to specify if lower is better.

        Returns:
            bool: True if lower values are better, False otherwise.
        """
        return True
    
class IndependentAggregator(Aggregator):
    """
    Aggregates benchmark results from multiple runs independently.
    """
    def __init__(self, agg_func: Callable[[Mapping[str, Mapping[str, Any]]], float]):
        self.agg_func = agg_func

    def aggregate(self, results: List[Mapping[str, Mapping[str, Any]]]) -> List[float]:
        return list(map(self.agg_func, results))
    
    
def select_metric(run: Mapping[str, Mapping[str, Any]], metric: str) -> Mapping[str, Any]:
    return {k: v[metric] for k, v in run.items()}
    
class RankingAggregator(Aggregator):
    """
    Aggregates benchmark results from multiple runs by ranking them.
    """
    def __init__(self, score_func: Callable[[Mapping[str, Any]], float]):
        self.score_func = score_func

    def aggregate(self, results: List[Mapping[str, Mapping[str, Any]]]) -> List[float]:
        score = [0.0] * len(results)

        common_benchmarks = reduce(lambda x, y: x.intersection(y), [set(res.keys()) for res in results])
        if not common_benchmarks:
            return score

        for bench in common_benchmarks:
            sr = sorted(list(range(len(results))), key=lambda x: self.score_func(results[x][bench]))
            for rank, idx in enumerate(sr):
                score[idx] += rank # Could square this to change weighting

        # Normalize scores with len(results)
        for i in range(len(score)):
            score[i] /= len(common_benchmarks)
        
        return score
    
    def unit(self):
        return "mean rank"



# Configurable presets

def configure_ranking_agg(metric):
    return RankingAggregator(lambda x: x[metric])

aggregator_presets: Mapping[str, Callable[..., Aggregator]] = {
    "ranking": configure_ranking_agg,
    "mean": lambda metric: IndependentAggregator(lambda x: sum(select_metric(x, metric).values())/len(x)),
}