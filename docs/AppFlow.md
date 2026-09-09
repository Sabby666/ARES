# AppFlow: User Journey & Application Behavior

## 1. First-Time User Experience
The user opens the ARES dashboard. They are presented with a professional dark-themed SOC UI displaying zero assessments, prompting them to initiate a "New Assessment".

## 2. Authentication
*(Deferred to Major Project. Currently operates in trusted single-user lab mode.)*

## 3. Dashboard
- Displays summary statistics: Total Assessments, Running, Completed, Findings by Severity.
- Recent Assessments table.
- Agent system health status.

## 4. New Assessment
- User navigates to `/assessments/new`.
- Input fields: Assessment Name, Target URL, Scope description.
- **UI Warning**: Displays an ethical testing notice indicating only allowlisted targets are permitted.

## 5. Target Configuration & 6. Scope Configuration
- Target is validated client-side and server-side.

## 7. Policy Validation
- **Screen**: Assessment Detail (Status: `CREATED`).
- **Backend Action**: `PolicyAgent` checks the Target URL against the allowlist.
- **Next State**: If failed, state becomes `BLOCKED`. If passed, moves to `RECON`.

## 8. Assessment Start & 9. Live Agent Workflow
- The user is redirected to `/assessments/{id}`.
- WebSockets connect automatically.
- Animated pipeline visualizer shows current stage.

## 10. Recon Stage
- `ReconAgent` triggers HexStrike recon modules via Tool Gateway.
- **UI Result**: Activity feed shows "Discovered open ports...", "Identified web server...".

## 11. Analysis Stage
- `AnalyzerAgent` correlates recon data against known patterns.

## 12. LLM Reasoning Stage
- `LLMReasoner` sends data via `OmniRoute`.
- Generates exploit chains and confidence scores.
- **UI Result**: Activity feed shows "LLM evaluating potential SQLi on /login".

## 13. Tool Execution
- Instructed by LLM/Analyzer, specific safe HexStrike modules run to verify hypotheses.

## 14. Evidence Capture & 15. Finding Generation
- Tool output is captured. If vulnerable, a structured Finding is saved to the database.

## 16. Finding Validation
- `ValidationAgent` reviews findings to eliminate false positives.

## 17. Report Generation & 18. Report Viewing
- Pipeline completes. State changes to `COMPLETED`.
- User clicks "View Report" to open a generated HTML report in a new tab.

## 19. Assessment History
- Listed on Dashboard and Reports pages. User can click any past assessment to view the static log.

## 20. Agent Monitoring
- `/agents` page displays real-time agent status, capability descriptions, and mock/real tool mappings.

## 21. Error States & 22. Blocked-Target Flow
- If Target is out of scope, pipeline immediately halts. Status badge turns red (`BLOCKED`). UI clearly explains policy violation.

## 23. Empty States & 24. Loading States
- Ghost elements or spinners for loading. Clear "No Findings Yet" graphics (using Lucide icons).

## 25. Stop/Cancel Flow
- User can click a "Halt" button to abruptly terminate the async pipeline and kill running tool adapters.
