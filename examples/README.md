# WhyBroke Examples

Small buggy scripts for smoke-testing the CLI. Each is designed to fail in a
different, realistic way so you can exercise the full pipe end-to-end.

```bash
python examples/01_type_error.py 2>&1 | whybroke
python examples/02_key_error.py 2>&1 | whybroke
python examples/03_await_on_sync.py 2>&1 | whybroke
python examples/04_zero_division.py 2>&1 | whybroke
python examples/05_attribute_error.py 2>&1 | whybroke
```

Each script is self-contained — no third-party deps, no side effects.
