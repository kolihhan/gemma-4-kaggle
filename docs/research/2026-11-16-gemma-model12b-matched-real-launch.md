# Gemma 4 new axis: 12B versus already frozen matched 31B

Date 2026-11-16. **Scientific change: model size, not another optional Skill or another prompt-only round.** Kaggle staff official clarification [12B/E4B/E2B model support](https://www.kaggle.com/competitions/gemma-4-developer-agent/discussion/748287). The 12B model is required to launch vLLM using `--hf-overrides '{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}'`. Do not mix different models inside one final competition submission; this experiment runs only 12B.

## Actual frozen comparison, non-independent public-development source

- [Preregistered model-size hypothesis and gate](../../experiments/solver-v3/pro-12b-vs-frozen31b-20261116.json). Against exact **PREVIOUS** 31B V2 control, 1/3 resolved, 62 calls, 604.94 seconds on three previously selected FastAPI/Rich/Requests tasks. The old matched 31B base and V3R were run once in [Action #43689217134](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43689217134). Their *test IDs and outcomes are already known*; this is a cost-efficient retrospective matched **hypothesis probe**, not independent confirmation.
- Reuse exact SHA-salted selection from original frozen V3R manifest, with the same exclusions. Identical per-task **5min / 28 max tool calls / 80 turns**, same root native tools, prompt and sampling; change only root model 31B→12B (plus the architecture-required vLLM override in **private test harness**, not a new competition tool).
- Source exact hash `a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`, original reference Apache-2.0 attribution. We reused our own historical Kaggle private CPU immutable source `kolihhan/gemma4-budgetfit-v2-reference-42008171687/1`, validated as byte-identical.
- [CPU pinned source and syntax gate #43780901445](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43780901445) **SUCCESS**: exact three-task protocol, no source drift, legal 12B reference and `HF_OVERRIDE` rendered, generated runtime SHA256 `d66590030f045a67a32e335f572ffc5e9423a573edbf23e68619469d288ea43f`.
- [Single REAL private 12B Kaggle launch #43781086310](https://github.com/kolihhan/gemma-4-kaggle/actions/runs/43781086310) passed quota check, source render and Kernel push. Private Kernel `kolihhan/gemma4-model12b-v2-matched-20261116`, 3 official `swegemma` public-dev grader tasks on real Gemma 4 12B model. **IN PROGRESS** at report-writing, no real 12B resolved-task outcome yet. This is not official Kaggle competition submission and does not claim to improve best scored 0.18.

## Promotion / falsifier

- Primary same-task rescues/regressions in official grader versus exact frozen 31B V2. Secondary time, tool calls, patch and errors.
- **12B ≥2/3**, zero errors would warrant a **fresh disjoint blinded paired cohort**; it is not enough on its own for claiming hidden score gain.
- If 12B ≤1/3 or fails to load, no model-size benefit is proven; retire the simple "smaller is automatically better" claim rather than fitting prompts on the same issues. A wheelhouse or architecture failure is infrastructure evidence, not a negative repair skill result.
- Do not repeat this already-launched kernel; when it reaches COMPLETE, read its actual 3-task paired scorer status, not merely GitHub job success.

## Operational correction (no science impact)

Two earlier CPU passes failed because our workflow's templated secret reference accidentally retained a leading backslash, sending malformed credentials to Kaggle; **not** because Kaggle token was expired. Corrected exact GitHub Actions secret expansion and verified authenticated CPU #43780901445 SUCCESS. This correction did not change agent source, model or task results and did not launch duplicate GPU.

No new model training, no second 31B GPU run and no new official competition submission.
