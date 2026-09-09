# backend/app/agents/controller.py
"""ARES Controller — orchestrates the full multi-agent assessment pipeline."""

import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

logger = logging.getLogger(__name__)

from app.models.models import Assessment, Finding, Evidence, ActivityLog, Report, AttackSurface, PentestAction
from app.agents.policy_agent import PolicyAgent
from app.agents.recon_agent import ReconAgent
from app.agents.analyzer_agent import AnalyzerAgent
from app.agents.llm_reasoner import LLMReasoner
from app.agents.validation_agent import ValidationAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.observation_agent import ObservationAgent
from app.services.evidence_manager import EvidenceManager
from app.services.reporting_service import ReportingService
from app.tools.gateway import ToolGateway
from app.core.config import settings

class AresController:
    """Orchestrates the ARES pipeline via an iterative agentic VAPT loop."""

    def __init__(self):
        self.policy = PolicyAgent()
        self.recon = ReconAgent()
        self.analyzer = AnalyzerAgent()
        self.reasoner = LLMReasoner()
        self.validator = ValidationAgent()
        self.planner = PlannerAgent()
        self.observation = ObservationAgent()
        self.tool_gateway = ToolGateway()
        self._active: dict[str, bool] = {}
        self._ws_callbacks: dict[str, list] = {}

    def register_ws(self, assessment_id: str, callback):
        self._ws_callbacks.setdefault(assessment_id, []).append(callback)

    def unregister_ws(self, assessment_id: str, callback):
        cbs = self._ws_callbacks.get(assessment_id, [])
        if callback in cbs:
            cbs.remove(callback)

    async def _broadcast(self, assessment_id: str, data: dict):
        for cb in self._ws_callbacks.get(assessment_id, []):
            try:
                await cb(data)
            except Exception:
                pass

    async def _log(self, db: AsyncSession, assessment_id: str, agent: str, message: str, log_type: str = "info"):
        entry = ActivityLog(assessment_id=assessment_id, agent=agent, message=message, log_type=log_type)
        db.add(entry)
        await db.commit()
        await self._broadcast(assessment_id, {
            "event": "activity",
            "agent": agent,
            "message": message,
            "log_type": log_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def _set_status(self, db: AsyncSession, assessment: Assessment, status: str):
        assessment.status = status
        db.add(assessment)
        await db.commit()
        await self._broadcast(assessment.id, {"event": "status", "status": status})

    async def run(self, db: AsyncSession, assessment_id: str):
        if self._active.get(assessment_id):
            return
        self._active[assessment_id] = True

        try:
            result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
            assessment = result.scalar_one_or_none()
            if not assessment or assessment.status in ("COMPLETED", "BLOCKED"):
                return

            assessment.started_at = datetime.now(timezone.utc)
            from app.schemas.policy import PolicyAction, ActionCapability, PolicyDecisionResult
            from app.schemas.tools import ToolResult, ToolExecutionState, ToolRequest
            
            # ── INIT: Initial Recon & Analysis ─────────────────────────────────
            await self._set_status(db, assessment, "RECON")
            await self._log(db, assessment_id, "ReconAgent", "🔍 Dispatching initial reconnaissance...", "info")

            initial_action = PolicyAction(
                action_id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                target=assessment.target,
                action_type="endpoint_scan",
                capability=ActionCapability.RECON,
                requested_by="AresController"
            )
            decision = await self.policy.evaluate_action(initial_action, assessment)
            if decision.decision == PolicyDecisionResult.BLOCK:
                await self._log(db, assessment_id, "PolicyAgent", f"🚫 BLOCKED [{decision.reason_code}] — {decision.reason}", "error")
                assessment.completed_at = datetime.now(timezone.utc)
                await self._set_status(db, assessment, "BLOCKED")
                return

            try:
                recon_result = await self.recon.scan(target=assessment.target, assessment_id=assessment_id, policy_decision=decision)
            except Exception as e:
                await self._log(db, assessment_id, "ReconAgent", f"💥 Recon failed: {str(e)}", "error")
                assessment.completed_at = datetime.now(timezone.utc)
                await self._set_status(db, assessment, "FAILED")
                return

            recon_data = recon_result.to_controller_dict()
            assessment.recon_data = recon_data
            db.add(assessment)

            await self._set_status(db, assessment, "ANALYSIS")
            candidate_findings = await self.analyzer.analyze(recon_result)
            # Save Attack Surfaces
            for ep in recon_data.get("endpoints", []):
                attack_surface = AttackSurface(
                    assessment_id=assessment_id,
                    origin="Recon",
                    path=ep.get("path", ""),
                    method=ep.get("method", "GET"),
                    parameters=ep.get("parameters", {}),
                    forms=ep.get("forms", {}),
                    form_fields=ep.get("form_fields", {}),
                    input_fields=ep.get("input_fields", {}),
                    authentication_required=ep.get("authentication_required", "False"),
                    authentication_state=ep.get("authentication_state", "UNAUTHENTICATED"),
                    session_context_id=ep.get("session_context_id"),
                    csrf_state=ep.get("csrf_state", {}),
                    response_status=ep.get("response_status"),
                    response_headers=ep.get("response_headers", {}),
                    response_metadata=ep.get("response_metadata", {}),
                    technologies=recon_data.get("technologies", [])
                )
                db.add(attack_surface)

            # Persist initial candidates as HYPOTHESES
            for f_data in candidate_findings:
                finding = Finding(
                    assessment_id=assessment_id,
                    title=f_data.get("title", ""),
                    category=f_data.get("category", ""),
                    severity=f_data.get("severity", "Info"),
                    confidence=f_data.get("confidence", 0.0),
                    endpoint=f_data.get("endpoint", ""),
                    description=f_data.get("description", ""),
                    reasoning=f_data.get("reasoning", ""),
                    recommendation=f_data.get("recommendation", ""),
                    status="HYPOTHESIS",
                    agent="AnalyzerAgent",
                    finding_signature=f"{assessment_id}:{f_data.get('category', '')}:{f_data.get('endpoint', '')}:{f_data.get('title', '')}"
                )
                db.add(finding)
            await db.commit()

            assessment_state = {
                "assessment_id": assessment_id,
                "target": assessment.target,
                "actions_taken": 0,
                "max_actions": getattr(settings, "MAX_VAPT_ACTIONS", 10),
                "status": "IN_PROGRESS"
            }

            # ── VAPT LOOP ───────────────────────────────────────────────────
            await self._set_status(db, assessment, "VALIDATION")
            await self._log(db, assessment_id, "Controller", "🔄 Entering Iterative VAPT Loop...", "info")

            while assessment_state["actions_taken"] < assessment_state["max_actions"]:
                await self._log(db, assessment_id, "PlannerAgent", f"🤔 Planning Action {assessment_state['actions_taken'] + 1}/{assessment_state['max_actions']}", "info")
                
                # Fetch fresh state for Planner
                surfaces_res = await db.execute(select(AttackSurface).where(AttackSurface.assessment_id == assessment_id))
                assessment_state["attack_surfaces"] = [{"path": s.path, "method": s.method, "parameters": s.parameters} for s in surfaces_res.scalars().all()]
                
                findings_res = await db.execute(select(Finding).where(Finding.assessment_id == assessment_id))
                db_findings = findings_res.scalars().all()
                assessment_state["findings"] = [{"title": f.title, "category": f.category, "status": f.status, "endpoint": f.endpoint} for f in db_findings]
                
                actions_res = await db.execute(select(PentestAction).where(PentestAction.assessment_id == assessment_id).order_by(PentestAction.created_at.desc()).limit(10))
                assessment_state["past_actions"] = [{"action_type": a.capability, "target": a.target, "endpoint": a.endpoint, "status": a.status, "objective": a.objective} for a in actions_res.scalars().all()]

                # Plan
                next_action = await self.planner.plan(assessment_state)
                
                if next_action.get("action_type", "").lower() == "stop":
                    await self._log(db, assessment_id, "PlannerAgent", "🛑 Planner chose to stop the loop.", "info")
                    break

                assessment_state["actions_taken"] += 1

                # Save PentestAction
                db_action = PentestAction(
                    assessment_id=assessment_id,
                    target=next_action.get("target", assessment.target),
                    endpoint=next_action.get("endpoint"),
                    method=next_action.get("method", "GET"),
                    capability=next_action.get("capability", "RECON"),
                    tool=next_action.get("tool"),
                    objective=next_action.get("objective", ""),
                    hypothesis=next_action.get("hypothesis", ""),
                    reason=next_action.get("reason", ""),
                    expected_observation=next_action.get("expected_observation", ""),
                    validation_goal=next_action.get("validation_goal"),
                    status="EXECUTING"
                )
                db.add(db_action)
                await db.commit()

                # Policy Check
                action_cap = next_action.get("capability", "RECON")
                
                if action_cap == "MISSING_CONTEXT":
                    await self._log(db, assessment_id, "Controller", f"⚠️ Action skipped due to MISSING_CONTEXT: {next_action.get('reason')}", "warning")
                    db_action.status = "BLOCKED"
                    db_action.result_data = {"reason": next_action.get("reason")}
                    db.add(db_action)
                    await db.commit()
                    assessment_state["recent_observations"].append(f"MISSING_CONTEXT: {next_action.get('reason')}")
                    continue

                policy_action = PolicyAction(
                    action_id=str(uuid.uuid4()),
                    assessment_id=assessment_id,
                    target=assessment.target,
                    action_type=next_action["action_type"],
                    capability=action_cap,
                    endpoint=next_action.get("endpoint"),
                    parameters=next_action.get("parameters", {}),
                    requested_by="PlannerAgent"
                )
                decision = await self.policy.evaluate_action(policy_action, assessment)
                
                if decision.decision == PolicyDecisionResult.BLOCK:
                    await self._log(db, assessment_id, "PolicyAgent", f"🚫 Action BLOCKED: {decision.reason}", "warning")
                    db_action.status = "BLOCKED"
                    db_action.result_data = {"reason": decision.reason}
                    db.add(db_action)
                    await db.commit()
                    continue

                # Execute
                await self._log(db, assessment_id, "ToolGateway", f"⚡ Executing {action_cap} on {next_action.get('endpoint', 'target')}", "info")
                tool_req = ToolRequest(
                    request_id=policy_action.action_id,
                    assessment_id=assessment_id,
                    target=assessment.target,
                    capability=action_cap,
                    parameters=policy_action.parameters,
                    session_context_id=next_action.get("session_context_id"),
                    policy_decision_id=decision.audit_id
                )
                tool_result = await self.tool_gateway.execute(tool_req, decision)

                # Save Evidence
                await EvidenceManager.extract_from_tool_result(db, assessment_id, tool_result)

                # Observe
                await self._log(db, assessment_id, "ObservationAgent", "👀 Evaluating tool result...", "info")
                observation = await self.observation.evaluate(next_action, tool_result.model_dump(mode="json"), assessment_state)
                
                db_action.status = "COMPLETED" if tool_result.status == ToolExecutionState.SUCCESS else "FAILED"
                db_action.result_data = {"analysis": observation.get("analysis", "")}
                db.add(db_action)
                await db.commit()
                
                # Update State / Attack Surface
                if observation.get("new_endpoints"):
                    for ep in observation["new_endpoints"]:
                        attack_surface = AttackSurface(
                            assessment_id=assessment_id,
                            origin="Observation",
                            path=ep.get("path", ""),
                            method=ep.get("method", "GET"),
                            parameters=ep.get("parameters", {}),
                            forms=ep.get("forms", {}),
                            form_fields=ep.get("form_fields", {}),
                            input_fields=ep.get("input_fields", {}),
                            authentication_required=ep.get("authentication_required", "False"),
                            authentication_state=ep.get("authentication_state", "UNAUTHENTICATED"),
                            session_context_id=ep.get("session_context_id"),
                            csrf_state=ep.get("csrf_state", {}),
                            response_status=ep.get("response_status"),
                            response_headers=ep.get("response_headers", {}),
                            response_metadata=ep.get("response_metadata", {}),
                            technologies=observation.get("new_technologies", [])
                        )
                        db.add(attack_surface)
                    await db.commit()

                # Update Finding Status if applicable
                goal = next_action.get("validation_goal")
                if goal:
                    # Update local state
                    for f in assessment_state["findings"]:
                        if f["title"] == goal:
                            f["status"] = observation["finding_status"]
                            break
                    # Update DB
                    res = await db.execute(select(Finding).where(Finding.assessment_id == assessment_id, Finding.title == goal))
                    db_finding = res.scalar_one_or_none()
                    if db_finding:
                        db_finding.status = observation.get("finding_status", db_finding.status)
                        db.add(db_finding)
                        db_action.finding_id = db_finding.id
                        db.add(db_action)
                        await db.commit()
                        await self._log(db, assessment_id, "ObservationAgent", f"📝 Finding '{goal}' status updated to {observation.get('finding_status')}", "success")


            # ── Final Reasoning & Reporting ─────────────────────────────────
            await self._set_status(db, assessment, "LLM_REASONING")
            
            # Fetch all findings for reasoning
            res = await db.execute(select(Finding).where(Finding.assessment_id == assessment_id))
            final_findings = res.scalars().all()
            final_findings_dict = []
            for f in final_findings:
                final_findings_dict.append({
                    "title": f.title, "category": f.category, "severity": f.severity,
                    "confidence": f.confidence, "endpoint": f.endpoint, "status": f.status
                })

            reasoning_result = await self.reasoner.reason(final_findings_dict, assessment_state)
            
            assessment.reasoning_data = {
                "risk_score": reasoning_result["risk_score"],
                "attack_chains": len(reasoning_result["attack_chains"]),
                "model": reasoning_result["model"],
            }
            db.add(assessment)
            await db.commit()

            await self._set_status(db, assessment, "REPORTING")
            await ReportingService.generate_report(db, assessment_id)

            assessment.report_json = {
                "findings": final_findings_dict,
                "reasoning": reasoning_result["reasoning_summary"],
                "attack_chains": reasoning_result["attack_chains"],
                "risk_score": reasoning_result["risk_score"]
            }

            assessment.completed_at = datetime.now(timezone.utc)
            if assessment.started_at:
                delta = assessment.completed_at - assessment.started_at
                assessment.duration_ms = int(delta.total_seconds() * 1000)
            await self._set_status(db, assessment, "COMPLETED")

            await self._log(db, assessment_id, "Controller", "🎉 Agentic VAPT Loop Complete!", "success")

        except Exception as e:
            logger.error(f"Assessment {assessment_id} encountered fatal error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            try:
                await db.rollback()
                result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
                assessment = result.scalar_one_or_none()
                if assessment:
                    assessment.completed_at = datetime.now(timezone.utc)
                    await self._set_status(db, assessment, "FAILED")
                await self._log(db, assessment_id, "Controller", f"💥 Pipeline failed: {str(e)}", "error")
            except Exception as nested_e:
                logger.error(f"Failed to mark assessment FAILED: {nested_e}")
        finally:
            self._active.pop(assessment_id, None)
