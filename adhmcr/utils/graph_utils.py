import networkx as nx
from typing import Dict

def build_graph(graph: nx.DiGraph, file_path: str, semantic_info: Dict):
    graph.add_node(file_path, type='file')
    
    for class_name, class_info in semantic_info['classes'].items():
        class_node = f"{file_path}::{class_name}"
        graph.add_node(class_node, type='class')
        graph.add_edge(file_path, class_node)
        for method in class_info.methods:
            method_node = f"{class_node}::{method}"
            graph.add_node(method_node, type='function')
            graph.add_edge(class_node, method_node)
    
    for func_name in semantic_info['functions']:
        func_node = f"{file_path}::{func_name}"
        graph.add_node(func_node, type='function')
        graph.add_edge(file_path, func_node)