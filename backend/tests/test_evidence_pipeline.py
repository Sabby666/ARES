import pytest
from app.services.evidence_manager import EvidenceManager
from app.schemas.tools import ToolResult, ToolExecutionState
from app.agents.validation_agent import ValidationAgent
from app.core.config import settings

@pytest.mark.asyncio
async def test_evidence_manager_mock_source():
    settings.TOOL_PROVIDER = "mock"
    result = ToolResult(
        request_id="test-1",
        execution_id="exec-1",
        capability="RECON",
        status=ToolExecutionState.SUCCESS,
        adapter="MockReconAdapter",
        structured_data={"endpoints_discovered": 1, "endpoints": ["http://demo.local/admin"]}
    )
    
    # We mock db as a simple list collector for this test
    class MockDB:
        def __init__(self):
            self.items = []
        def add(self, item):
            self.items.append(item)
            
    db = MockDB()
    records = await EvidenceManager.extract_from_tool_result(db, "assessment-1", result)
    
    assert len(records) == 1
    assert records[0].source_type == "MOCK"
    assert records[0].source == "MockReconAdapter"
    assert "http://demo.local/admin" in records[0].content


@pytest.mark.asyncio
async def test_validation_agent_deterministic():
    import uuid as _uuid
    from app.schemas.policy import PolicyDecision, PolicyDecisionResult
    validator = ValidationAgent()
    findings = [
        {"id": "f1", "title": "t1", "confidence": 0.90},
        {"id": "f2", "title": "t2", "confidence": 0.70},
        {"id": "f3", "title": "t3", "confidence": 0.40},
    ]
    
    mock_decision = PolicyDecision(
        decision_id=str(_uuid.uuid4()),
        action_id=str(_uuid.uuid4()),
        decision=PolicyDecisionResult.ALLOW,
        reason="test",
        reason_code="TEST",
    )
    
    result = await validator.validate(
        target="demo.local", 
        assessment_id="test", 
        policy_decision=mock_decision, 
        findings=findings
    )
    
    assert result[0]["status"] == "VALIDATED"
    assert result[1]["status"] == "VALIDATED"
    assert result[2]["status"] == "REJECTED"
