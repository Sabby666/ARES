import html
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload
from app.models.models import Assessment, Finding, Evidence, ActivityLog, Report
from app.core.config import settings

class ReportingService:
    """Generates professional, traceable HTML security reports."""
    
    @staticmethod
    async def generate_report(db: AsyncSession, assessment_id: str) -> str:
        # Load assessment
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()
        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found.")

        # Load findings with evidence eagerly
        result = await db.execute(
            select(Finding)
            .options(joinedload(Finding.evidence))
            .where(Finding.assessment_id == assessment_id)
            .order_by(desc(Finding.created_at))
        )
        findings = result.unique().scalars().all()
        
        # Load activity log
        result = await db.execute(
            select(ActivityLog)
            .where(ActivityLog.assessment_id == assessment_id)
            .order_by(ActivityLog.timestamp)
        )
        activities = result.scalars().all()

        # Organize findings
        proven_findings = [f for f in findings if f.status == "PROVEN"]
        candidate_findings = [f for f in findings if f.status in ("CANDIDATE", "HYPOTHESIS", "VALIDATING", "NEEDS_REVIEW")]
        not_proven_findings = [f for f in findings if f.status == "NOT_PROVEN"]
        rejected_findings = [f for f in findings if f.status in ("REJECTED", "INCONCLUSIVE")]
        
        # Build Report
        report_html = ReportingService._render_html(assessment, findings, proven_findings, candidate_findings, not_proven_findings, rejected_findings, activities)
        
        # Persist report
        report = Report(
            assessment_id=assessment_id,
            report_type="html",
            content=report_html,
            findings_count=len(proven_findings)
        )
        db.add(report)
        assessment.report_html = report_html
        await db.commit()
        
        return report_html

    @staticmethod
    def _render_html(assessment: Assessment, all_findings: list[Finding], proven_findings: list[Finding], candidate_findings: list[Finding], not_proven_findings: list[Finding], rejected_findings: list[Finding], activities: list[ActivityLog]) -> str:
        execution_mode = "SIMULATED / MOCK" if settings.TOOL_PROVIDER == "mock" else "REAL / HEXSTRIKE"
        generation_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        # Basic Statistics
        total_findings = len(all_findings)
        prov_count = len(proven_findings)
        cand_count = len(candidate_findings)
        not_prov_count = len(not_proven_findings)
        rej_count = len(rejected_findings)
        duration = f"{assessment.duration_ms} ms" if assessment.duration_ms else "Unknown"
        
        # Escape helpers
        esc = html.escape

        # Severity colors
        sev_colors = {
            "Critical": "#ff4757",
            "High": "#ff6b35",
            "Medium": "#ffa502",
            "Low": "#2ed573",
            "Info": "#70a1ff"
        }

        # Findings Summary Table
        def render_summary_table(finding_list):
            if not finding_list:
                return "<p style='color:#888;'>No findings in this category.</p>"
            
            # Sort by severity (Critical -> Info), then confidence
            sev_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
            sorted_f = sorted(finding_list, key=lambda x: (sev_order.get(x.severity, 5), -x.confidence))
            
            rows = ""
            for f in sorted_f:
                color = sev_colors.get(f.severity, "#70a1ff")
                rows += f"""
                <tr>
                    <td style='border-bottom:1px solid #333;padding:8px;'>{esc(f.title)}</td>
                    <td style='border-bottom:1px solid #333;padding:8px;'>{esc(f.category)}</td>
                    <td style='border-bottom:1px solid #333;padding:8px;color:{color};font-weight:bold;'>{esc(f.severity)}</td>
                    <td style='border-bottom:1px solid #333;padding:8px;'>{f.confidence:.0%}</td>
                    <td style='border-bottom:1px solid #333;padding:8px;'><code>{esc(f.endpoint)}</code></td>
                    <td style='border-bottom:1px solid #333;padding:8px;'>{len(f.evidence)}</td>
                </tr>
                """
            return f"""
            <table style='width:100%;border-collapse:collapse;text-align:left;font-size:14px;margin-bottom:24px;'>
                <thead>
                    <tr style='background:#1a1a2e;color:#aaa;'>
                        <th style='padding:12px 8px;border-bottom:2px solid #333;'>Title</th>
                        <th style='padding:12px 8px;border-bottom:2px solid #333;'>Category</th>
                        <th style='padding:12px 8px;border-bottom:2px solid #333;'>Severity</th>
                        <th style='padding:12px 8px;border-bottom:2px solid #333;'>Confidence</th>
                        <th style='padding:12px 8px;border-bottom:2px solid #333;'>Endpoint</th>
                        <th style='padding:12px 8px;border-bottom:2px solid #333;'>Evidence</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            """

        # Finding Details Section
        def render_finding_details(finding_list):
            if not finding_list:
                return ""
            
            details = ""
            for f in finding_list:
                color = sev_colors.get(f.severity, "#70a1ff")
                
                evidence_html = ""
                if f.evidence:
                    for ev in f.evidence:
                        simulated_badge = "<span style='background:#4b4b4b;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;margin-left:8px;border:1px dashed #888;'>SIMULATED EVIDENCE</span>" if ev.source_type == "MOCK" else ""
                        evidence_html += f"""
                        <div style='background:#2a2a3e;padding:12px;border-radius:6px;margin:8px 0;border:1px solid #444;'>
                            <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                                <div>
                                    <strong style='font-size:12px;color:#aaa;'>Source: {esc(ev.source)}</strong>
                                    {simulated_badge}
                                </div>
                                <span style='font-size:12px;color:#888;'>{ev.timestamp.strftime("%Y-%m-%d %H:%M:%S") if ev.timestamp else ""}</span>
                            </div>
                            <pre style='margin:0;font-size:12px;color:#ccc;overflow-x:auto;max-height:300px;'>{esc(ev.content)}</pre>
                        </div>
                        """
                else:
                    evidence_html = "<p style='color:#888;font-size:12px;'>No evidence attached.</p>"

                details += f"""
                <div style='background:#1a1a2e;border-left:4px solid {color};padding:20px;margin:16px 0;border-radius:8px;'>
                    <h3 style='margin:0 0 12px 0;color:#e0e0e0;'>{esc(f.title)}</h3>
                    
                    <div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;'>
                        <div><strong style='color:#888;font-size:12px;'>Severity:</strong> <span style='color:{color};font-weight:600;'>{esc(f.severity)}</span></div>
                        <div><strong style='color:#888;font-size:12px;'>Confidence:</strong> {f.confidence:.0%}</div>
                        <div><strong style='color:#888;font-size:12px;'>Category:</strong> {esc(f.category)}</div>
                        <div><strong style='color:#888;font-size:12px;'>Status:</strong> {esc(f.status)}</div>
                        <div><strong style='color:#888;font-size:12px;'>Resource:</strong> <code>{esc(f.endpoint)}</code></div>
                        <div><strong style='color:#888;font-size:12px;'>Source Agent:</strong> {esc(f.agent)}</div>
                    </div>
                    
                    <h4 style='color:#70a1ff;margin:16px 0 8px 0;font-size:14px;'>Description</h4>
                    <p style='margin:0 0 16px 0;line-height:1.5;color:#ccc;'>{esc(f.description)}</p>
                    
                    <h4 style='color:#70a1ff;margin:16px 0 8px 0;font-size:14px;'>Reasoning</h4>
                    <p style='margin:0 0 16px 0;line-height:1.5;color:#ccc;'>{esc(f.reasoning)}</p>
                    
                    <h4 style='color:#70a1ff;margin:16px 0 8px 0;font-size:14px;'>Recommendation</h4>
                    <p style='margin:0 0 16px 0;line-height:1.5;color:#ccc;'>{esc(f.recommendation)}</p>
                    
                    <h4 style='color:#70a1ff;margin:16px 0 8px 0;font-size:14px;'>Evidence</h4>
                    {evidence_html}
                </div>
                """
            return details

        # Timeline
        timeline_html = ""
        for act in activities:
            timeline_html += f"""
            <div style='margin-bottom:8px;font-size:13px;'>
                <span style='color:#888;width:150px;display:inline-block;'>{act.timestamp.strftime("%Y-%m-%d %H:%M:%S") if act.timestamp else ""}</span>
                <strong style='color:#70a1ff;width:120px;display:inline-block;'>{esc(act.agent)}</strong>
                <span style='color:#ccc;'>{esc(act.message)}</span>
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ARES Security Report — {esc(assessment.name)}</title>
<style>
  body {{ font-family: 'Inter', 'Segoe UI', sans-serif; background: #0d0d1a; color: #e0e0e0; padding: 40px; margin: 0; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 12px; }}
  h2 {{ color: #70a1ff; margin-top: 40px; border-bottom: 1px solid #333; padding-bottom: 8px; }}
  .meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 24px 0; }}
  .meta-item {{ background: #1a1a2e; padding: 16px; border-radius: 8px; border: 1px solid #333; }}
  .meta-label {{ color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 8px; }}
  .meta-value {{ color: #e0e0e0; font-size: 16px; font-weight: 600; }}
  code {{ background: #2a2a3e; padding: 2px 6px; border-radius: 4px; font-size: 13px; }}
  .footer {{ margin-top: 60px; padding-top: 20px; border-top: 1px solid #333; color: #666; font-size: 12px; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <h1>🛡️ ARES Penetration Testing Report</h1>
  
  <div class="meta">
    <div class="meta-item"><div class="meta-label">Assessment</div><div class="meta-value">{esc(assessment.name)}</div></div>
    <div class="meta-item"><div class="meta-label">Target Scope</div><div class="meta-value">{esc(assessment.target)}</div></div>
    <div class="meta-item"><div class="meta-label">Execution Mode</div><div class="meta-value">{execution_mode}</div></div>
    <div class="meta-item"><div class="meta-label">Duration</div><div class="meta-value">{duration}</div></div>
  </div>

  <h2>📋 Executive Summary</h2>
  <div style="background:#1a1a2e;padding:20px;border-radius:8px;border:1px solid #333;line-height:1.6;">
    <p style="margin-top:0;">
      During the penetration test of <strong>{esc(assessment.target)}</strong>, ARES reasoned over discovered attack surfaces and formed <strong>{total_findings}</strong> hypotheses/findings.
    </p>
    <p>
      Pentest Actions Executed: <strong>{len([a for a in activities if "Executing" in a.message])}</strong><br>
      { "<span style='color:#ff4757;'>Required application context unavailable. No specific actions executed.</span>" if len([a for a in activities if "Executing" in a.message]) == 0 else "" }
    </p>
    <p>
      Of the findings, <strong>{prov_count}</strong> were PROVEN via authorized controlled testing, and <strong>{cand_count}</strong> remain as CANDIDATES. 
      <strong>{not_prov_count}</strong> findings were explicitly NOT PROVEN, and <strong>{rej_count}</strong> were rejected or inconclusive.
    </p>
  </div>

  <h2>📊 Proven Findings Summary</h2>
  {render_summary_table(proven_findings)}

  <h2>⚠️ Candidate Findings Summary</h2>
  {render_summary_table(candidate_findings)}

  <h2>🔍 Proven Finding Details</h2>
  {render_finding_details(proven_findings)}
  
  <h2>⏳ Candidate Finding Details (Needs Review)</h2>
  {render_finding_details(candidate_findings)}

  <h2>⏱️ Assessment Timeline</h2>
  <div style="background:#1a1a2e;padding:20px;border-radius:8px;border:1px solid #333;">
    {timeline_html}
  </div>
  
  <h2>🛑 Limitations & Methodology</h2>
  <div style="background:#1a1a2e;padding:20px;border-radius:8px;border:1px solid #333;line-height:1.6;color:#ccc;">
    <p style="margin-top:0;"><strong>Workflow:</strong> Scope &rarr; Policy &rarr; Agent Execution &rarr; Tool Execution &rarr; Evidence &rarr; Finding &rarr; Validation &rarr; Report.</p>
    <p><strong>Limitations:</strong></p>
    <ul style="margin:0;padding-left:20px;">
        <li>This report reflects the output of an automated agentic security pipeline.</li>
        <li>Mock / simulated tool results may be present. If the execution mode is SIMULATED, evidence is explicitly mocked and does not represent a real penetration test against an external target.</li>
        <li>Full autonomous exploitation and live HexStrike integration are outside the scope of this particular execution unless stated otherwise.</li>
        <li>Candidate findings require human review to verify their legitimacy.</li>
    </ul>
  </div>

  <div class="footer">
    Generated by ARES Security Prototype — Academic Use Only — {generation_time}
  </div>
</div>
</body>
</html>"""
