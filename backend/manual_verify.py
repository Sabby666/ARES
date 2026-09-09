import uuid
from app.policy.gateway import PolicyGateway
from app.schemas.policy import PolicyAction, ActionCapability
from app.models.models import Assessment


def run_manual_verification():
    gateway = PolicyGateway()
    assessment = Assessment(
        id=str(uuid.uuid4()),
        name="Manual Test",
        target="http://localhost",
        status="RECON"
    )

    print("========================================")
    print("MANUAL VERIFICATION RESULTS")
    print("========================================")

    # TEST A - Allowed Target
    action_a = PolicyAction(
        action_id=str(uuid.uuid4()), assessment_id=assessment.id,
        target="http://localhost", action_type="scan", capability=ActionCapability.RECON, requested_by="me"
    )
    dec_a = gateway.evaluate(action_a, assessment)
    print(f"TEST A (Allowed Target 'http://localhost') -> {dec_a.decision.value} ({dec_a.reason_code})")

    # TEST B - Unauthorized Target
    action_b = PolicyAction(
        action_id=str(uuid.uuid4()), assessment_id=assessment.id,
        target="https://example.com", action_type="scan", capability=ActionCapability.RECON, requested_by="me"
    )
    dec_b = gateway.evaluate(action_b, assessment)
    print(f"TEST B (Unauthorized Target 'https://example.com') -> {dec_b.decision.value} ({dec_b.reason_code})")

    # TEST C - Invalid Capability
    action_c = PolicyAction(
        action_id=str(uuid.uuid4()), assessment_id=assessment.id,
        target="http://localhost", action_type="scan", capability="ARBITRARY_EXECUTION", requested_by="me"
    )
    dec_c = gateway.evaluate(action_c, assessment)
    print(f"TEST C (Invalid Capability 'ARBITRARY_EXECUTION') -> {dec_c.decision.value} ({dec_c.reason_code})")

    # TEST D - Inactive Assessment
    inactive_assessment = Assessment(
        id=str(uuid.uuid4()), name="Manual Test", target="http://localhost", status="COMPLETED"
    )
    action_d = PolicyAction(
        action_id=str(uuid.uuid4()), assessment_id=inactive_assessment.id,
        target="http://localhost", action_type="scan", capability=ActionCapability.RECON, requested_by="me"
    )
    dec_d = gateway.evaluate(action_d, inactive_assessment)
    print(f"TEST D (Inactive Assessment 'COMPLETED') -> {dec_d.decision.value} ({dec_d.reason_code})")

    # TEST E - Allowed Action
    dec_e = gateway.evaluate(action_a, assessment)
    print(f"TEST E (Allowed Action) -> {dec_e.decision.value} ({dec_e.reason_code})")


if __name__ == "__main__":
    run_manual_verification()
