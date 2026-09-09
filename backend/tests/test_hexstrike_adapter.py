import pytest
import uuid
import httpx
from unittest.mock import AsyncMock, patch

from app.tools.adapters.hexstrike import HexStrikeAdapter
from app.schemas.tools import ToolRequest, ToolExecutionState
from app.schemas.policy import ActionCapability
from app.core.config import settings

@pytest.fixture
def hexstrike_adapter(monkeypatch):
    monkeypatch.setattr(settings, "HEXSTRIKE_BASE_URL", "http://fake-hexstrike/api")
    monkeypatch.setattr(settings, "HEXSTRIKE_API_KEY", "test-key")
    return HexStrikeAdapter()


def create_request() -> ToolRequest:
    return ToolRequest(
        request_id=str(uuid.uuid4()),
        assessment_id="test",
        target="demo.local",
        capability=ActionCapability.RECON,
        parameters={"port": 80}
    )


@pytest.mark.asyncio
async def test_hexstrike_success(hexstrike_adapter):
    request = create_request()
    
    mock_request = httpx.Request("POST", "http://fake-hexstrike/api/execute")
    mock_response = httpx.Response(
        200, 
        json={"result": {"endpoints": ["/api/v1/test"]}, "output": "Scan complete"},
        request=mock_request
    )
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await hexstrike_adapter.execute(request)
        
        assert result.status == ToolExecutionState.SUCCESS
        assert result.structured_data == {"endpoints": ["/api/v1/test"]}
        assert result.output == "Scan complete"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["capability"] == ActionCapability.RECON
        assert kwargs["json"]["target"] == "demo.local"


@pytest.mark.asyncio
async def test_hexstrike_unavailable(hexstrike_adapter):
    request = create_request()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        result = await hexstrike_adapter.execute(request)
        
        assert result.status == ToolExecutionState.UNAVAILABLE
        assert result.error_code == "HEXSTRIKE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_hexstrike_timeout(hexstrike_adapter):
    request = create_request()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        result = await hexstrike_adapter.execute(request)
        
        assert result.status == ToolExecutionState.TIMEOUT
        assert result.error_code == "HEXSTRIKE_TIMEOUT"


@pytest.mark.asyncio
async def test_hexstrike_http_error(hexstrike_adapter):
    request = create_request()
    
    mock_request = httpx.Request("POST", "http://fake-hexstrike/api/execute")
    mock_response = httpx.Response(500, text="Internal Server Error", request=mock_request)
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        # raise_for_status() will raise HTTPStatusError
        result = await hexstrike_adapter.execute(request)
        
        assert result.status == ToolExecutionState.FAILED
        assert result.error_code == "HEXSTRIKE_HTTP_500"
        assert "Internal Server Error" in result.error_message
