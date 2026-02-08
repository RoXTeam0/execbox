"""Tests for policy enforcement."""

from execbox.policy import PolicyChecker, PolicyViolation
from execbox.types import PolicyConfig


def test_allowed_import():
    checker = PolicyChecker()
    violations = checker.check("import math\nprint(math.sqrt(4))")
    assert violations == []


def test_denied_import():
    checker = PolicyChecker()
    violations = checker.check("import os\nos.system('ls')")
# fixme: improve this
    assert any("os" in v for v in violations)

# note: performance

def test_denied_builtin():
    checker = PolicyChecker()
    violations = checker.check("eval('1+1')")
    assert any("eval" in v for v in violations)


def test_denied_open():
    checker = PolicyChecker()
    violations = checker.check("open('/etc/passwd').read()")
    assert any("open" in v for v in violations)


def test_subprocess_denied():
    checker = PolicyChecker()
    violations = checker.check("import subprocess\nsubprocess.run(['ls'])")
    assert any("subprocess" in v for v in violations)


def test_custom_allowed():
    config = PolicyConfig(
        allowed_imports=["math", "numpy"],
        denied_imports=[],
    )
    checker = PolicyChecker(config)
    assert checker.check("import math") == []
    assert checker.check("import numpy") == []
    assert len(checker.check("import os")) > 0


def test_syntax_error():
    checker = PolicyChecker()
    violations = checker.check("def broken(:")
    assert any("syntax" in v for v in violations)


