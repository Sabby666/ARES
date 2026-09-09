import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Evidence
from app.schemas.tools import ToolResult
from app.core.config import settings

class EvidenceManager:
    """Service layer to normalize ToolResults into Evidence records."""
    
    @staticmethod
    async def extract_from_tool_result(db: AsyncSession, assessment_id: str, tool_result: ToolResult) -> list[Evidence]:
        """
        Parses a ToolResult and converts its structured data into Evidence records.
        """
        evidence_records = []
        source_type = "MOCK" if settings.TOOL_PROVIDER == "mock" else "REAL"

        data = tool_result.structured_data or {}
        
        # Recon data extraction
        if "endpoints_discovered" in data:
            evidence_records.append(Evidence(
                assessment_id=assessment_id,
                agent="ToolGateway",
                action="recon_endpoints",
                evidence_type="TOOL_OUTPUT",
                content=json.dumps(data.get("endpoints", [])),
                source=tool_result.adapter,
                source_type=source_type
            ))
            
        if "open_ports" in data:
            evidence_records.append(Evidence(
                assessment_id=assessment_id,
                agent="ToolGateway",
                action="recon_ports",
                evidence_type="TOOL_OUTPUT",
                content=json.dumps(data.get("open_ports", [])),
                source=tool_result.adapter,
                source_type=source_type
            ))
            
        if "technologies" in data:
            evidence_records.append(Evidence(
                assessment_id=assessment_id,
                agent="ToolGateway",
                action="recon_tech",
                evidence_type="TOOL_OUTPUT",
                content=json.dumps(data.get("technologies", [])),
                source=tool_result.adapter,
                source_type=source_type
            ))

        # Fallback if no specific recon structure is found
        if not evidence_records and tool_result.structured_data:
            evidence_records.append(Evidence(
                assessment_id=assessment_id,
                agent="ToolGateway",
                action="tool_execution",
                evidence_type="TOOL_OUTPUT",
                content=json.dumps(tool_result.structured_data),
                source=tool_result.adapter,
                source_type=source_type
            ))
            
        for ev in evidence_records:
            db.add(ev)
            
        return evidence_records
