import asyncio
import uuid
from datetime import datetime, timezone
from app.schemas.tools import ToolRequest, ToolResult, ToolExecutionState
from app.tools.adapters.base import ToolAdapter


class MockReconAdapter(ToolAdapter):
    """
    Provides fully deterministic mock recon data for testing.
    No random sampling — returns the complete fixed fixture set.
    source: mock
    execution_mode: SIMULATED
    """

    MOCK_ENDPOINTS = [
        {"path": "/", "method": "GET", "status": 200, "tech": ["HTML5"]},
        {"path": "/login", "method": "GET", "status": 200, "tech": ["HTML5", "JavaScript"]},
        {"path": "/login", "method": "POST", "status": 302, "tech": ["Express.js"]},
        {"path": "/api/users", "method": "GET", "status": 200, "tech": ["REST", "JSON"]},
        {"path": "/api/users", "method": "POST", "status": 201, "tech": ["REST", "JSON"]},
        {"path": "/api/admin", "method": "GET", "status": 403, "tech": ["REST", "JSON"]},
        {"path": "/api/admin/config", "method": "GET", "status": 200, "tech": ["REST", "JSON"]},
        {"path": "/api/search", "method": "GET", "status": 200, "tech": ["REST", "JSON"]},
        {"path": "/api/upload", "method": "POST", "status": 200, "tech": ["REST", "Multipart"]},
        {"path": "/dashboard", "method": "GET", "status": 200, "tech": ["React", "JavaScript"]},
        {"path": "/profile", "method": "GET", "status": 200, "tech": ["React", "JavaScript"]},
        {"path": "/logout", "method": "POST", "status": 302, "tech": ["Express.js"]},
        {"path": "/api/export", "method": "GET", "status": 200, "tech": ["REST", "CSV"]},
        {"path": "/robots.txt", "method": "GET", "status": 200, "tech": ["Text"]},
        {"path": "/.env", "method": "GET", "status": 200, "tech": ["Text"]},
    ]

    MOCK_TECHNOLOGIES = [
        {"name": "Node.js", "version": "18.17.0", "category": "Runtime"},
        {"name": "Express.js", "version": "4.18.2", "category": "Framework"},
        {"name": "React", "version": "18.2.0", "category": "Frontend"},
        {"name": "MongoDB", "version": "6.0", "category": "Database"},
        {"name": "nginx", "version": "1.24.0", "category": "Web Server"},
        {"name": "JWT", "version": "9.0.0", "category": "Authentication"},
    ]

    MOCK_HEADERS = {
        "Server": "nginx/1.24.0",
        "X-Powered-By": "Express",
        "Content-Type": "text/html; charset=utf-8",
        "X-Frame-Options": "MISSING",
        "Content-Security-Policy": "MISSING",
        "Strict-Transport-Security": "MISSING",
        "X-Content-Type-Options": "nosniff",
    }

    async def execute(self, request: ToolRequest) -> ToolResult:
        started_at = datetime.now(timezone.utc)
        await asyncio.sleep(1.0)

        # Deterministic — no random sampling
        endpoints = self.MOCK_ENDPOINTS
        technologies = self.MOCK_TECHNOLOGIES

        structured_data = {
            "target": request.target,
            "source": "MockReconAdapter",
            "execution_mode": "SIMULATED",
            "reachable": True,
            "status_code": 200,
            "endpoints_discovered": len(endpoints),
            "endpoints": endpoints,
            "technologies": technologies,
            "headers": self.MOCK_HEADERS,
            "open_ports": [80, 443, 3000, 8080],
            "dns_records": [
                {"type": "A", "value": "127.0.0.1"},
                {"type": "AAAA", "value": "::1"},
            ],
            "tls": {
                "enabled": True,
                "version": "TLSv1.3",
                "cipher": "TLS_AES_256_GCM_SHA384",
                "certificate_valid": True,
                "expiry_days": 245,
            },
            "observations": [
                "Exposed .env file detected at /.env",
                "Missing Content-Security-Policy header",
                "Missing Strict-Transport-Security header",
                "Admin endpoint accessible at /api/admin/config",
            ],
        }

        completed_at = datetime.now(timezone.utc)
        duration = int((completed_at - started_at).total_seconds() * 1000)

        return ToolResult(
            execution_id=str(uuid.uuid4()),
            request_id=request.request_id,
            capability=request.capability,
            adapter=self.__class__.__name__,
            status=ToolExecutionState.SUCCESS,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration,
            structured_data=structured_data,
            metadata={"source": "MockReconAdapter", "execution_mode": "SIMULATED"},
        )


class MockHttpAnalysisAdapter(ToolAdapter):
    """Scaffold for an HTTP Analysis adapter."""
    async def execute(self, request: ToolRequest) -> ToolResult:
        started_at = datetime.now(timezone.utc)
        await asyncio.sleep(0.5)
        completed_at = datetime.now(timezone.utc)
        
        return ToolResult(
            execution_id=str(uuid.uuid4()),
            request_id=request.request_id,
            capability=request.capability,
            adapter=self.__class__.__name__,
            status=ToolExecutionState.SUCCESS,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=int((completed_at - started_at).total_seconds() * 1000),
            structured_data={"vulnerabilities_found": []}
        )


class MockValidationAdapter(ToolAdapter):
    """Scaffold for a Validation adapter."""
    async def execute(self, request: ToolRequest) -> ToolResult:
        started_at = datetime.now(timezone.utc)
        await asyncio.sleep(0.5)
        completed_at = datetime.now(timezone.utc)
        
        return ToolResult(
            execution_id=str(uuid.uuid4()),
            request_id=request.request_id,
            capability=request.capability,
            adapter=self.__class__.__name__,
            status=ToolExecutionState.SUCCESS,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=int((completed_at - started_at).total_seconds() * 1000),
            structured_data={"validated": True}
        )
