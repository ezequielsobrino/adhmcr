import os
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
import networkx as nx
from git import Repo

from .analyzers.python_analyzer import PythonAnalyzer
from .models.file_info import FileInfo
from .utils.file_utils import read_file_content
from .utils.graph_utils import build_graph
from .llm.groq import GroqLLM

load_dotenv()

class ADHMCR:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        self.llm = GroqLLM(api_key=os.environ.get("GROQ_API_KEY"), verbose=True)
        self.graph = nx.DiGraph()
        self.files: Dict[str, FileInfo] = {}
        self.language_analyzers = {
            '.py': PythonAnalyzer()
        }
        self.build_repo_graph()

    def build_repo_graph(self):
        for root, dirs, files in os.walk(self.repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.repo_path)
                _, ext = os.path.splitext(file)
                
                if ext in self.language_analyzers:
                    content = read_file_content(file_path)
                    if content is not None:
                        analyzer = self.language_analyzers[ext]
                        semantic_info = analyzer.analyze_semantics(content)
                        data_flow_info = analyzer.analyze_data_flow(content)
                        
                        self.files[relative_path] = FileInfo(
                            path=relative_path,
                            content=content,
                            functions=semantic_info['functions'],
                            classes=semantic_info['classes'],
                            data_flow=data_flow_info
                        )
                        
                        build_graph(self.graph, relative_path, semantic_info)

    def get_context(self, task: str) -> str:
        prompt = f"""
Task: {task}
Repository structure:
{self.get_repo_structure()}
        
Semantic information:
{self.get_semantic_info()}
        
Data flow information:
{self.get_data_flow_info()}
        
Based on this information, provide:
1. A list of relevant files with their full paths, in the following format:
   File: /path/to/file1.py
   File: /path/to/file2.py
   ...
2. A list of relevant classes and functions for this task.
3. A brief explanation of why each item is relevant.
4. A high-level plan to approach this task.
5. A prioritized list of specific changes to make, including file paths.
6. An analysis of potential impacts on other parts of the codebase.
7. Insights on how the changes might affect the data flow in the system.
"""
        return self.llm.generate(prompt)

    def suggest_changes(self, task: str, file_path: str) -> str:
        file_path = file_path.strip('`')
        file_info = self.files.get(file_path)
        if not file_info:
            return f"Error: File {file_path} not found in the repository."

        prompt = f"""
Task: {task}
File content:
```python
{file_info.content}
```

Semantic information:
{self._format_file_semantic_info(file_info)}

Data flow information:
Defined variables: {', '.join(file_info.data_flow.defined)}
Used variables: {', '.join(file_info.data_flow.used)}
Modified variables: {', '.join(file_info.data_flow.modified)}

Suggest specific changes to this file to accomplish the task. 
Provide the changes as a single code block that represents the entire updated file content.
After the code block, provide a brief explanation for each change and any potential impacts on other parts of the codebase.
Consider how the changes might affect the data flow and semantic structure of the code.

Format your response as follows:

```python
# Updated file content here
```

Explanation of changes:
1. [Brief explanation of first change]
2. [Brief explanation of second change]
...

Potential impacts:
- [Description of potential impact]
- [Description of another potential impact]
...
"""
        return self.llm.generate(prompt)

    def analyze_dependencies(self, file_path: str) -> List[str]:
        file_info = self.files.get(file_path)
        if not file_info:
            return []
        
        _, ext = os.path.splitext(file_path)
        analyzer = self.language_analyzers.get(ext)
        if not analyzer:
            return []
        
        return analyzer.analyze_dependencies(file_info.content)
    
    def get_repo_structure(self) -> str:
        structure = []
        for node, data in self.graph.nodes(data=True):
            if data['type'] == 'file':
                structure.append(f"File: {node}")
                for child in self.graph.successors(node):
                    child_type = self.graph.nodes[child]['type']
                    child_name = child.split('::')[-1]
                    structure.append(f"  {child_type.capitalize()}: {child_name}")
        return "\n".join(structure)

    def get_semantic_info(self) -> str:
        info = []
        for file_info in self.files.values():
            info.append(f"File: {file_info.path}")
            for class_name, class_data in file_info.classes.items():
                info.append(f"  Class: {class_name}")
                info.append(f"    Base classes: {', '.join(class_data.base_classes)}")
                info.append(f"    Methods: {', '.join(class_data.methods)}")
                info.append(f"    Attributes: {', '.join(class_data.attributes)}")
            for func_name, func_data in file_info.functions.items():
                info.append(f"  Function: {func_name}")
                info.append(f"    Arguments: {', '.join(func_data.args)}")
                info.append(f"    Returns: {func_data.returns}")
                if func_data.docstring:
                    info.append(f"    Docstring: {func_data.docstring}")
        return "\n".join(info)

    def get_data_flow_info(self) -> str:
        info = []
        for file_info in self.files.values():
            info.append(f"File: {file_info.path}")
            info.append(f"  Defined variables: {', '.join(file_info.data_flow.defined)}")
            info.append(f"  Used variables: {', '.join(file_info.data_flow.used)}")
            info.append(f"  Modified variables: {', '.join(file_info.data_flow.modified)}")
        return "\n".join(info)

    def _format_file_semantic_info(self, file_info: FileInfo) -> str:
        formatted = []
        for class_name, class_data in file_info.classes.items():
            formatted.append(f"Class: {class_name}")
            formatted.append(f"  Base classes: {', '.join(class_data.base_classes)}")
            formatted.append(f"  Methods: {', '.join(class_data.methods)}")
            formatted.append(f"  Attributes: {', '.join(class_data.attributes)}")
        for func_name, func_data in file_info.functions.items():
            formatted.append(f"Function: {func_name}")
            formatted.append(f"  Arguments: {', '.join(func_data.args)}")
            formatted.append(f"  Returns: {func_data.returns}")
            if func_data.docstring:
                formatted.append(f"  Docstring: {func_data.docstring}")
        return "\n".join(formatted)

    def execute_task(self, task: str):
        context = self.get_context(task)
        files_to_change = re.findall(r'File: (\S+)', context)
        for file_path in files_to_change:
            changes = self.suggest_changes(task, file_path)
            deps = self.analyze_dependencies(file_path)