# backend/app/tools/tool_adapter.py
"""Safe mock tool adapter — no real shell commands, no network calls."""


class MockToolAdapter:
    """Provides mock security tool outputs for demo purposes."""

    TOOLS = {
        "nmap": {
            "name": "Nmap Port Scanner",
            "description": "Network port scanner (simulated)",
            "tool_type": "recon",
            "safe": True,
        },
        "nikto": {
            "name": "Nikto Web Scanner",
            "description": "Web server vulnerability scanner (simulated)",
            "tool_type": "recon",
            "safe": True,
        },
        "sqlmap": {
            "name": "SQLMap",
            "description": "SQL injection detection tool (simulated)",
            "tool_type": "exploitation",
            "safe": True,
        },
        "burp": {
            "name": "Burp Suite Proxy",
            "description": "HTTP proxy and scanner (simulated)",
            "tool_type": "analysis",
            "safe": True,
        },
        "dirbuster": {
            "name": "DirBuster",
            "description": "Directory brute-force scanner (simulated)",
            "tool_type": "recon",
            "safe": True,
        },
        "jwt_tool": {
            "name": "JWT Tool",
            "description": "JWT token analysis and attack tool (simulated)",
            "tool_type": "exploitation",
            "safe": True,
        },
        "xsstrike": {
            "name": "XSStrike",
            "description": "XSS detection suite (simulated)",
            "tool_type": "exploitation",
            "safe": True,
        },
        "wappalyzer": {
            "name": "Wappalyzer",
            "description": "Technology fingerprinting (simulated)",
            "tool_type": "recon",
            "safe": True,
        },
    }

    def list_tools(self) -> list[dict]:
        """Return list of available (mock) tools."""
        return [{"id": k, **v} for k, v in self.TOOLS.items()]

    def run_tool(self, tool_id: str, target: str) -> dict:
        """Run a mock tool — always returns canned output, never executes anything."""
        tool = self.TOOLS.get(tool_id)
        if not tool:
            return {"error": f"Unknown tool: {tool_id}"}

        return {
            "tool": tool_id,
            "target": target,
            "status": "completed",
            "output": f"[MOCK] {tool['name']} scan of {target} completed. "
                      f"This is simulated output for demonstration purposes.",
            "safe": True,
        }
