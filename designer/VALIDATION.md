# Validation record

Prepared 2026-11-16 against repository commit `3f1b864bf9a3ba8a5a06289e71fdde082b224b33`.

| Check | Result |
| --- | --- |
| Core, data and browser app JavaScript parse in V8 | Passed |
| 65 calculation, pressure-state, interlock, import, CSV and graph tests in V8 | Passed, 0 failures |
| Default process and electrical graph endpoint/type consistency | Passed |
| Browser app static DOM ID references | Passed: no missing static references or duplicate HTML IDs |
| Repeatable Node runner included | Yes; Node execution unavailable in preparation environment |
| Browser rendering and interaction QA | Not run; no execution/browser workspace available |
| Exact visual integration with existing Propellant Site | Not run; Site source unavailable |
| Existing Site source changed or deployed | No |
| Real equipment operation or physical acceptance | Not tested or implied |

Run `node designer/core.test.cjs` and the browser acceptance checklist in README before integration/publication. These tests check the standalone design module, not the existing Arduino or Python controller.
