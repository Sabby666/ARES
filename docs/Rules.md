# Rules: Non-Negotiable Development Rules

1. **Never fabricate functionality**: Do not claim something is implemented if it is not.
2. **Strict Scope**: Never silently change PRD requirements or architecture.
3. **Database Integrity**: Never change database schema casually. Follow `Schema.md`.
4. **Code Reuse**: Check existing code before creating duplicate functionality. Reuse existing components where appropriate.
5. **UI Consistency**: Follow `Design.md` for all UI work (Dark SOC aesthetic).
6. **Architecture Adherence**: Follow `TechSpec.md` for technical architecture.
7. **UX Adherence**: Follow `AppFlow.md` for user behaviour.
8. **Plan Adherence**: Follow `ImplementationPlan.md` for development sequence.
9. **State Tracking**: Update `Tracker.md` after meaningful work (e.g., phase completion, schema changes, blockers).
10. **Incremental Work**: Keep changes incremental and run tests after meaningful implementation changes.
11. **Secret Management**: Never store secrets in source code. Use environment variables for credentials (e.g., `LLM_API_KEY`).
12. **Frontend Security**: Never expose unrestricted shell execution to the frontend.
13. **Backend Security**: Never allow arbitrary user-controlled command execution. No `shell=True` in subprocesses.
14. **Ethical Constraints**: Never scan unauthorized systems. Enforce target allowlisting and scope validation strictly in the Policy Gateway.
15. **Tool Orchestration**: Keep security-tool execution controlled. Prefer safe adapters over raw shell commands.
16. **Dependency Management**: Do not introduce unnecessary dependencies. Do not over-engineer.
17. **Future Proofing**: Keep future Major compatibility in mind. Preserve backwards compatibility when practical.
18. **Research Fidelity**: Use the ARES research paper as reference, not as a reason to fabricate unimplemented functionality.
19. **Honesty**: Distinguish research-paper functionality from implemented project functionality. Never report research-paper metrics as our own results. Never fabricate test results or security findings.
20. **Human Oversight**: Prefer explicit human oversight for risky operations. Keep the system restricted to authorized lab environments.
