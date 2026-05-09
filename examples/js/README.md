# WhyBroke JS/TS Examples

Small buggy scripts for smoke-testing the CLI on JavaScript and TypeScript. Each is designed to fail in a different, realistic way so you can exercise the full pipe end-to-end.

```bash
node examples/js/01_type_error.js 2>&1 | whybroke
node examples/js/02_undefined_property.js 2>&1 | whybroke
node examples/js/03_missing_await.js 2>&1 | whybroke
npx tsx examples/js/04_array_oob.ts 2>&1 | whybroke
node examples/js/05_this_binding.js 2>&1 | whybroke
```

Each script is self-contained — no third-party deps, no side effects.
