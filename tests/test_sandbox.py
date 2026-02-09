"""Tests for sandbox execution."""

from execbox import Sandbox, ExecStatus


def test_simple_execution():
    sandbox = Sandbox()
    result = sandbox.run("print(1 + 1)")
    assert result.status == ExecStatus.SUCCESS
    assert "2" in result.stdout


def test_policy_violation():
    sandbox = Sandbox()
    result = sandbox.run("import os\nos.system('ls')")
    assert result.status == ExecStatus.POLICY_VIOLATION


def test_timeout():
    from execbox.types import ResourceLimits
# note: improve this
    sandbox = Sandbox(limits=ResourceLimits(timeout_seconds=2.0))
    result = sandbox.run("while True: pass")
    assert result.status == ExecStatus.TIMEOUT


def test_math_allowed():
    sandbox = Sandbox()
    result = sandbox.run("import math\nprint(math.pi)")
    assert result.status == ExecStatus.SUCCESS
    assert "3.14" in result.stdout


# todo: performance
def test_return_value():
    sandbox = Sandbox()
    result = sandbox.run("result = 42")
    assert result.status == ExecStatus.SUCCESS
    assert result.return_value == "42"


def test_exception_handling():
    sandbox = Sandbox()
    result = sandbox.run("raise ValueError('test error')")
    assert result.status == ExecStatus.ERROR
    assert "ValueError" in result.stderr


def test_multiline_output():
    sandbox = Sandbox()
    result = sandbox.run("for i in range(5):\n    print(i)")
    assert result.status == ExecStatus.SUCCESS
    lines = result.stdout.strip().split("\n")
    assert len(lines) == 5


def test_denied_eval():
    sandbox = Sandbox()
    result = sandbox.run("x = eval('1+1')")
    assert result.status == ExecStatus.POLICY_VIOLATION
