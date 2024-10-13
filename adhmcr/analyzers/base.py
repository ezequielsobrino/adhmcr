from abc import ABC, abstractmethod
from typing import Dict, List
from ..models.data_flow_info import DataFlowInfo

class LanguageAnalyzer(ABC):
    @abstractmethod
    def analyze_semantics(self, content: str) -> Dict[str, Dict]:
        pass

    @abstractmethod
    def analyze_data_flow(self, content: str) -> DataFlowInfo:
        pass

    @abstractmethod
    def analyze_dependencies(self, content: str) -> List[str]:
        pass