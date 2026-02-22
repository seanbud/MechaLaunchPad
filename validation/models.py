from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class Severity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class ValidationResult:
    rule_id: str
    passed: bool
    severity: Severity = Severity.INFO
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    fix_hint: Optional[str] = None

@dataclass
class FBXData:
    """Simplified data extracted from FBX for validation."""
    filename: str
    tris: int
    meshes: List[Dict[str, Any]] = field(default_factory=list) # [{name, parent_bone, poly_count, transform}]
    armature_name: str = ""
    bones: List[str] = field(default_factory=list)
