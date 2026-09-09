import pytest
import asyncio
import json
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.llm import get_llm_provider
from app.llm.mock_provider import MockProvider
from app.llm.omniroute_provider import OmniRouteProvider
from app.core.config import settings
from app.llm.schemas import AnalysisResultSchema
from app.agents.analyzer_agent import AnalyzerAgent

@pytest.mark.asyncio
async def test_get_llm_provider_mock():
    settings.LLM_PROVIDER = "mock"
    provider = get_llm_provider()
    assert isinstance(provider, MockProvider)

@pytest.mark.asyncio
async def test_get_llm_provider_omniroute():
    settings.LLM_PROVIDER = "omniroute"
    provider = get_llm_provider()
    assert isinstance(provider, OmniRouteProvider)
    # restore
    settings.LLM_PROVIDER = "mock"

@pytest.mark.asyncio
async def test_mock_provider_analyze():
    """Phase 10: MockProvider is input-driven — findings reference actual recon data."""
    provider = MockProvider()
    # Provide real recon_data so the input-driven MockProvider can produce findings
    recon_data = {
        "target": "http://localhost",
        "endpoints": [
            {"path": "/.env", "method": "GET", "status": 200, "tech": ["Text"]},
        ],
        "headers": {"Server": "nginx/1.24.0", "Content-Security-Policy": "MISSING"},
        "observations": ["Exposed .env file detected at /.env"],
        "technologies": [],
        "open_ports": [80],
        "execution_mode": "SIMULATED",
        "source": "MockReconAdapter",
    }
    res = await provider.analyze_recon_data(recon_data)
    assert len(res.findings) >= 1
    # The .env finding must be present and reference the actual endpoint
    env_finding = next((f for f in res.findings if ".env" in f.title), None)
    assert env_finding is not None
    assert env_finding.severity == "Critical"
    assert env_finding.evidence_status in ("OBSERVED", "INFERRED")
    # All findings must have Phase 10 honesty fields
    for f in res.findings:
        assert f.evidence_status in ("OBSERVED", "INFERRED", "POTENTIAL")
        assert isinstance(f.evidence_requirements, str)
        assert isinstance(f.suggested_validation_context, str)

@pytest.mark.asyncio
async def test_mock_provider_reasoning():
    """Phase 10: MockProvider.reason_about_findings derives risk_score from actual findings."""
    from app.llm.schemas import CandidateFindingSchema
    provider = MockProvider()
    # Provide actual finding dicts so risk_score is input-derived
    findings = [
        {"title": "Sensitive File Exposure — .env", "severity": "Critical", "confidence": 0.96},
    ]
    res = await provider.reason_about_findings(findings, {"target": "http://localhost"})
    assert len(res.attack_chains) >= 1
    assert 0.0 <= res.risk_score <= 10.0
    assert isinstance(res.reasoning_summary, str)


# Test helpers for mocking httpx stream
class MockStreamResponse:
    def __init__(self, status_code, content_type, lines=None, json_data=None, raise_exc=None):
        self.status_code = status_code
        self.headers = {"content-type": content_type}
        self.lines = lines or []
        self.json_data = json_data
        self.raise_exc = raise_exc
        
    async def aiter_lines(self):
        for line in self.lines:
            yield line
            
    async def aread(self):
        pass
        
    def json(self):
        if self.json_data:
            return self.json_data
        raise json.JSONDecodeError("Expecting value", "", 0)
        
    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://test")
            raise httpx.HTTPStatusError(f"Error {self.status_code}", request=request, response=self)

    async def aclose(self):
        pass

class MockAsyncClient:
    def __init__(self, mock_response=None, raise_exc=None):
        self.mock_response = mock_response
        self.raise_exc = raise_exc
        self.calls = 0

    def build_request(self, *args, **kwargs):
        return httpx.Request("POST", "http://test")

    async def send(self, request, stream=False):
        self.calls += 1
        if isinstance(self.raise_exc, list):
            if self.calls <= len(self.raise_exc):
                exc = self.raise_exc[self.calls-1]
                if exc:
                    raise exc
        elif self.raise_exc:
            raise self.raise_exc
            
        if isinstance(self.mock_response, list):
            return self.mock_response[self.calls-1]
        return self.mock_response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_omniroute_json_response(mock_client):
    valid_json = {
        "findings": [{"title": "XSS", "category": "XSS", "severity": "High", "confidence": 0.9, "endpoint": "/", "description": "test", "reasoning": "test", "recommendation": "test"}]
    }
    response_data = {"choices": [{"message": {"content": json.dumps(valid_json)}}]}
    mock_response = MockStreamResponse(200, "application/json", json_data=response_data)
    mock_client.return_value = MockAsyncClient(mock_response=mock_response)
    
    provider = OmniRouteProvider()
    provider.max_retries = 0
    res = await provider.analyze_recon_data({})
    assert len(res.findings) == 1
    assert res.findings[0].title == "XSS"

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_omniroute_sse_response_one_event(mock_client):
    valid_json = {
        "findings": [{"title": "XSS", "category": "XSS", "severity": "High", "confidence": 0.9, "endpoint": "/", "description": "test", "reasoning": "test", "recommendation": "test"}]
    }
    lines = [
        f"data: {{\"choices\": [{{\"delta\": {{\"content\": {json.dumps(json.dumps(valid_json))}}}}}]}}",
        "data: [DONE]"
    ]
    mock_response = MockStreamResponse(200, "text/event-stream", lines=lines)
    mock_client.return_value = MockAsyncClient(mock_response=mock_response)
    
    provider = OmniRouteProvider()
    provider.max_retries = 0
    res = await provider.analyze_recon_data({})
    assert len(res.findings) == 1

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_omniroute_sse_response_multiple_events(mock_client):
    lines = [
        "data: {\"choices\": [{\"delta\": {\"content\": \"{\\\"findings\\\": [\"}}]}",
        "data: {\"choices\": [{\"delta\": {\"content\": \"{\\\"title\\\": \\\"SQLi\\\", \\\"category\\\": \\\"Inj\\\", \\\"severity\\\": \\\"High\\\", \\\"confidence\\\": 0.9, \\\"endpoint\\\": \\\"/\\\", \\\"description\\\": \\\"test\\\", \\\"reasoning\\\": \\\"test\\\", \\\"recommendation\\\": \\\"test\\\"}]}\"}}]}",
        "data: [DONE]"
    ]
    mock_response = MockStreamResponse(200, "text/event-stream", lines=lines)
    mock_client.return_value = MockAsyncClient(mock_response=mock_response)
    
    provider = OmniRouteProvider()
    provider.max_retries = 0
    res = await provider.analyze_recon_data({})
    assert len(res.findings) == 1
    assert res.findings[0].title == "SQLi"

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_omniroute_sse_malformed(mock_client):
    lines = [
        "data: not json",
        "data: {\"choices\": [{\"delta\": {\"content\": \"{\\\"findings\\\": []}\"}}]}",
        "data: [DONE]"
    ]
    mock_response = MockStreamResponse(200, "text/event-stream", lines=lines)
    mock_client.return_value = MockAsyncClient(mock_response=mock_response)
    
    provider = OmniRouteProvider()
    provider.max_retries = 0
    res = await provider.analyze_recon_data({})
    assert len(res.findings) == 0

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_omniroute_sse_empty(mock_client):
    lines = [
        "data: [DONE]"
    ]
    mock_response = MockStreamResponse(200, "text/event-stream", lines=lines)
    mock_client.return_value = MockAsyncClient(mock_response=mock_response)
    
    provider = OmniRouteProvider()
    provider.max_retries = 0
    with pytest.raises(RuntimeError, match="Empty or invalid SSE response"):
        await provider.analyze_recon_data({})

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_omniroute_http_429(mock_client):
    mock_429 = MockStreamResponse(429, "application/json")
    valid_json = {"findings": []}
    mock_200 = MockStreamResponse(200, "application/json", json_data={"choices": [{"message": {"content": json.dumps(valid_json)}}]})
    
    mock_client.return_value = MockAsyncClient(mock_response=[mock_429, mock_200])
    
    provider = OmniRouteProvider()
    provider.max_retries = 1
    res = await provider.analyze_recon_data({})
    assert len(res.findings) == 0

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_omniroute_timeout(mock_client):
    mock_client.return_value = MockAsyncClient(raise_exc=httpx.ReadTimeout("timeout"))
    
    provider = OmniRouteProvider()
    provider.max_retries = 0
    with pytest.raises(RuntimeError, match="LLM API connection failed"):
        await provider.analyze_recon_data({})

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_omniroute_malformed_model_json(mock_client):
    mock_response = MockStreamResponse(200, "application/json", json_data={"choices": [{"message": {"content": "bad json"}}]})
    mock_client.return_value = MockAsyncClient(mock_response=mock_response)
    
    provider = OmniRouteProvider()
    provider.max_retries = 0
    with pytest.raises(Exception):
        await provider.analyze_recon_data({})

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_omniroute_structured_pydantic_validation(mock_client):
    bad_json = {
        "findings": [{"title": "XSS", "description": "test", "confidence": "High", "evidence": "none"}]
    }
    mock_response = MockStreamResponse(200, "application/json", json_data={"choices": [{"message": {"content": json.dumps(bad_json)}}]})
    mock_client.return_value = MockAsyncClient(mock_response=mock_response)
    
    provider = OmniRouteProvider()
    provider.max_retries = 0
    with pytest.raises(Exception):
        await provider.analyze_recon_data({})

@pytest.mark.asyncio
@patch('app.llm.omniroute_provider.OmniRouteProvider.analyze_recon_data')
async def test_final_analyzer_integration(mock_analyze):
    """Phase 10: AnalyzerAgent.analyze() now accepts a typed ReconResult."""
    import uuid as _uuid
    from app.schemas.recon import ReconResult, ReconExecutionMode
    from app.llm.schemas import AnalysisResultSchema

    mock_analyze.return_value = AnalysisResultSchema(findings=[])

    settings.LLM_PROVIDER = "omniroute"
    agent = AnalyzerAgent()

    recon_result = ReconResult(
        target="http://test.local",
        source="MockReconAdapter",
        execution_mode=ReconExecutionMode.SIMULATED,
        tool_execution_reference=str(_uuid.uuid4()),
    )

    res = await agent.analyze(recon_result)
    assert len(res) == 0
    settings.LLM_PROVIDER = "mock"
