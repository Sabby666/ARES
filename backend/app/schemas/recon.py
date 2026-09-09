# backend/app/schemas/recon.py
"""Typed ReconResult schema for Phase 9 RECON Agent output."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ReconExecutionMode(str, Enum):
    SIMULATED = "SIMULATED"
    REAL = "REAL"


class ReconEndpoint(BaseModel):
    path: str
    method: str
    status: int
    tech: List[str] = Field(default_factory=list)


class ReconTechnology(BaseModel):
    name: str
    version: str = ""
    category: str = ""


class ReconResult(BaseModel):
    """Structured, typed result produced by ReconAgent from a ToolResult."""

    # Target provenance
    target: str
    source: str  # e.g. "MockReconAdapter", "HexStrikeAdapter"
    execution_mode: ReconExecutionMode
    tool_execution_reference: Optional[str] = None  # execution_id from ToolResult

    # Reachability
    reachable: bool = True
    status_code: Optional[int] = None

    # Discovery data
    endpoints_discovered: int = 0
    endpoints: List[ReconEndpoint] = Field(default_factory=list)
    technologies: List[ReconTechnology] = Field(default_factory=list)
    headers: Dict[str, str] = Field(default_factory=dict)
    open_ports: List[int] = Field(default_factory=list)
    dns_records: List[Dict[str, str]] = Field(default_factory=list)
    tls: Optional[Dict[str, Any]] = None

    # Observations and metadata
    observations: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_controller_dict(self) -> dict:
        """Serialize to the flat dict the Controller and Analyzer expect."""
        return {
            "target": self.target,
            "source": self.source,
            "execution_mode": self.execution_mode.value,
            "reachable": self.reachable,
            "status_code": self.status_code,
            "endpoints_discovered": self.endpoints_discovered,
            "endpoints": [e.model_dump() for e in self.endpoints],
            "technologies": [t.model_dump() for t in self.technologies],
            "headers": self.headers,
            "open_ports": self.open_ports,
            "dns_records": self.dns_records,
            "tls": self.tls,
            "observations": self.observations,
            "tool_execution_reference": self.tool_execution_reference,
        }
