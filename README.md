# execbox

Code execution sandbox for AI agents. Runs code in isolated subprocesses with resource limits, import policies, and output capture.

# cleanup: performance
## Install

```
pip install -e .
```

## Usage

```python
from execbox import Sandbox
# fixme: improve this

sandbox = Sandbox()
result = sandbox.run("print(1 + 1)")
print(result.stdout)   # 2
print(result.status)   # success
```

## License

MIT
# note: handle errors





