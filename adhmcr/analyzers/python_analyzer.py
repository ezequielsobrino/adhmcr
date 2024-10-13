import ast
from typing import Dict, List
from .base import LanguageAnalyzer
from ..models.data_flow_info import DataFlowInfo
from ..models.file_info import FunctionInfo, ClassInfo

class PythonAnalyzer(LanguageAnalyzer):
    def analyze_semantics(self, content: str) -> Dict[str, Dict[str, FunctionInfo | ClassInfo]]:
        tree = ast.parse(content)
        semantic_analyzer = SemanticAnalyzer()
        semantic_analyzer.visit(tree)
        return {
            'functions': semantic_analyzer.functions,
            'classes': semantic_analyzer.classes
        }

    def analyze_data_flow(self, content: str) -> DataFlowInfo:
        tree = ast.parse(content)
        data_flow_analyzer = DataFlowAnalyzer()
        data_flow_analyzer.visit(tree)
        return data_flow_analyzer.flow_info

    def analyze_dependencies(self, content: str) -> List[str]:
        tree = ast.parse(content)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"{node.module}.{node.names[0].name}")
        return imports

class SemanticAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.functions: Dict[str, FunctionInfo] = {}
        self.classes: Dict[str, ClassInfo] = {}
        self.current_function = None
        self.current_class = None

    def visit_FunctionDef(self, node):
        self.functions[node.name] = FunctionInfo(
            args=[arg.arg for arg in node.args.args],
            returns=self._get_return_type(node),
            docstring=ast.get_docstring(node)
        )
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None

    def visit_ClassDef(self, node):
        self.classes[node.name] = ClassInfo(
            methods=[],
            attributes=[],
            base_classes=[base.id for base in node.bases if isinstance(base, ast.Name)],
            docstring=ast.get_docstring(node)
        )
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_Attribute(self, node):
        if self.current_class and isinstance(node.ctx, ast.Store):
            self.classes[self.current_class].attributes.append(node.attr)

    def _get_return_type(self, node):
        for item in node.body:
            if isinstance(item, ast.Return):
                return self._infer_type(item.value)
        return 'None'

    def _infer_type(self, node):
        if isinstance(node, ast.Num):
            return type(node.n).__name__
        elif isinstance(node, ast.Str):
            return 'str'
        elif isinstance(node, ast.List):
            return 'List'
        elif isinstance(node, ast.Dict):
            return 'Dict'
        elif isinstance(node, ast.Name):
            return node.id
        else:
            return 'Unknown'

class DataFlowAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.flow_info = DataFlowInfo()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.flow_info.defined.append(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.flow_info.used.append(node.id)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.flow_info.modified.append(target.id)
        self.generic_visit(node)