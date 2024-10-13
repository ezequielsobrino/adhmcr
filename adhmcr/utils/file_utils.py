from typing import Optional

def read_file_content(file_path: str) -> Optional[str]:
    encodings = ['utf-8', 'latin-1', 'ascii', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    print(f"Warning: Unable to read file {file_path} with any of the attempted encodings.")
    return None