from dataclasses import dataclass, field
from typing import List

@dataclass
class DataFlowInfo:
    defined: List[str] = field(default_factory=list)
    used: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)