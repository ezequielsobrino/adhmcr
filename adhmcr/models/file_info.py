from dataclasses import dataclass
from typing import Dict, List, Optional
from .data_flow_info import DataFlowInfo

@dataclass
class FunctionInfo:
    args: List[str]
    returns: str
    docstring: Optional[str]

@dataclass
class ClassInfo:
    methods: List[str]
    attributes: List[str]
    base_classes: List[str]
    docstring: Optional[str]

@dataclass
class FileInfo:
    path: str
    content: str
    functions: Dict[str, FunctionInfo]
    classes: Dict[str, ClassInfo]
    data_flow: DataFlowInfo