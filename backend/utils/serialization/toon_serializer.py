"""
TOON (Text Object Oriented Notation) Serializer

A human-readable text-based serialization format for structured data.
"""

from typing import Any, Dict, List, Union
from pathlib import Path


def dump_toon(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Serialize data structure to TOON format and write to file.
    
    Args:
        data: Data structure to serialize (dict, list, primitive)
        file_path: Path to output file
        indent: Number of spaces for indentation
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(_serialize_toon(data, indent=indent))


def load_toon(file_path: Union[str, Path]) -> Any:
    """
    Load and deserialize TOON format file.
    
    Args:
        file_path: Path to TOON file
        
    Returns:
        Deserialized data structure
    """
    file_path = Path(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return _parse_toon(content)


def _serialize_toon(data: Any, indent: int = 2, level: int = 0) -> str:
    """Recursively serialize data to TOON format"""
    prefix = " " * (indent * level)
    
    if data is None:
        return "null"
    elif isinstance(data, bool):
        return "true" if data else "false"
    elif isinstance(data, (int, float)):
        return str(data)
    elif isinstance(data, str):
        # Escape special characters and wrap in quotes if needed
        if "\n" in data or '"' in data or "\\" in data:
            # Use triple quotes for multi-line strings
            escaped = data.replace("\\", "\\\\").replace('"""', '\\"""')
            return f'"""\n{escaped}\n"""'
        elif " " in data or data == "":
            return f'"{data}"'
        else:
            return data
    elif isinstance(data, list):
        if not data:
            return "[]"
        lines = ["["]
        for i, item in enumerate(data):
            item_str = _serialize_toon(item, indent, level + 1)
            if i < len(data) - 1:
                lines.append(f"{prefix}{' ' * indent}{item_str},")
            else:
                lines.append(f"{prefix}{' ' * indent}{item_str}")
        lines.append(f"{prefix}]")
        return "\n".join(lines)
    elif isinstance(data, dict):
        if not data:
            return "{}"
        lines = ["{"]
        items = list(data.items())
        for i, (key, value) in enumerate(items):
            # Format key
            if isinstance(key, str) and (key.replace("_", "").replace("-", "").isalnum() or key == ""):
                key_str = key
            else:
                key_str = f'"{key}"'
            
            # Format value
            value_str = _serialize_toon(value, indent, level + 1)
            
            # Handle multi-line values
            if "\n" in value_str:
                if i < len(items) - 1:
                    lines.append(f"{prefix}{' ' * indent}{key_str}:")
                    for line in value_str.split("\n"):
                        lines.append(f"{prefix}{' ' * indent * 2}{line}")
                    lines.append(f"{prefix}{' ' * indent},")
                else:
                    lines.append(f"{prefix}{' ' * indent}{key_str}:")
                    for line in value_str.split("\n"):
                        lines.append(f"{prefix}{' ' * indent * 2}{line}")
            else:
                if i < len(items) - 1:
                    lines.append(f"{prefix}{' ' * indent}{key_str}: {value_str},")
                else:
                    lines.append(f"{prefix}{' ' * indent}{key_str}: {value_str}")
        
        lines.append(f"{prefix}}}")
        return "\n".join(lines)
    else:
        # Fallback for other types (datetime, etc.)
        return f'"{str(data)}"'


def _parse_toon(content: str) -> Any:
    """Parse TOON format content to Python data structure"""
    content = content.strip()
    
    if not content:
        return None
    
    # Try to parse as different types
    if content == "null":
        return None
    elif content == "true":
        return True
    elif content == "false":
        return False
    elif content == "[]":
        return []
    elif content == "{}":
        return {}
    
    # Try to parse as number
    try:
        if "." in content:
            return float(content)
        else:
            return int(content)
    except ValueError:
        pass
    
    # Try to parse as string
    if content.startswith('"""') and content.endswith('"""'):
        # Multi-line string
        return content[3:-3].strip().replace('\\"""', '"""').replace("\\\\", "\\")
    elif content.startswith('"') and content.endswith('"'):
        # Quoted string
        return content[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    
    # Try to parse as list
    if content.startswith("[") and content.endswith("]"):
        return _parse_toon_list(content[1:-1].strip())
    
    # Try to parse as dict
    if content.startswith("{") and content.endswith("}"):
        return _parse_toon_dict(content[1:-1].strip())
    
    # Default: return as string
    return content


def _parse_toon_list(content: str) -> List[Any]:
    """Parse TOON list format"""
    if not content.strip():
        return []
    
    items = []
    current_item = ""
    depth = 0
    in_string = False
    string_char = None
    
    i = 0
    while i < len(content):
        char = content[i]
        
        if not in_string:
            if char in ['"', "'"]:
                in_string = True
                string_char = char
                current_item += char
            elif char == "[":
                depth += 1
                current_item += char
            elif char == "]":
                depth -= 1
                current_item += char
            elif char == "{":
                depth += 1
                current_item += char
            elif char == "}":
                depth -= 1
                current_item += char
            elif char == "," and depth == 0:
                if current_item.strip():
                    items.append(_parse_toon(current_item.strip()))
                current_item = ""
            else:
                current_item += char
        else:
            current_item += char
            if char == string_char and (i == 0 or content[i-1] != "\\"):
                in_string = False
                string_char = None
        
        i += 1
    
    if current_item.strip():
        items.append(_parse_toon(current_item.strip()))
    
    return items


def _parse_toon_dict(content: str) -> Dict[str, Any]:
    """Parse TOON dict format"""
    if not content.strip():
        return {}
    
    result = {}
    current_key = None
    current_value = ""
    depth = 0
    in_string = False
    string_char = None
    in_key = True
    
    i = 0
    while i < len(content):
        char = content[i]
        
        if not in_string:
            if char in ['"', "'"]:
                in_string = True
                string_char = char
                if in_key:
                    current_key = char
                else:
                    current_value += char
            elif char == ":" and depth == 0 and in_key:
                # End of key
                if current_key:
                    current_key = _parse_toon(current_key.strip())
                in_key = False
            elif char == "," and depth == 0 and not in_key:
                # End of value
                if current_key is not None:
                    result[current_key] = _parse_toon(current_value.strip())
                current_key = None
                current_value = ""
                in_key = True
            elif char in ["[", "{"]:
                depth += 1
                if in_key:
                    current_key = (current_key or "") + char
                else:
                    current_value += char
            elif char in ["]", "}"]:
                depth -= 1
                if in_key:
                    current_key = (current_key or "") + char
                else:
                    current_value += char
            else:
                if in_key:
                    current_key = (current_key or "") + char
                else:
                    current_value += char
        else:
            if in_key:
                current_key = (current_key or "") + char
            else:
                current_value += char
            if char == string_char and (i == 0 or content[i-1] != "\\"):
                in_string = False
                string_char = None
        
        i += 1
    
    # Add last key-value pair
    if current_key is not None and current_value.strip():
        if isinstance(current_key, str):
            current_key = _parse_toon(current_key.strip())
        result[current_key] = _parse_toon(current_value.strip())
    
    return result

