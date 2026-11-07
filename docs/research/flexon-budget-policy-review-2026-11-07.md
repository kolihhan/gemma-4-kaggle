# Flexon budget-aware agent V10 — source and mechanism review

Reviewed 2026-11-07 MYT. Research and CPU execution only. No training, model
inference, new Kaggle submission or candidate changes.

## Decision

Retain this as an external comparator. The strongest conclusion is that another
single-root 31B policy fits exactly the configuration of our scored V2 control.
The public page records 0.22 for V10. We have not reproduced that score, obtained
its task-level outcomes or isolated a beneficial policy component. Our own
verified comparator remains 0.17. Do not count the displayed 0.05 difference as
a measured improvement of any mechanism.

The paired-check prototype has not earned preference over this simpler action
space. Keep its existing candidate and matched control unchanged, and require
independent patch correctness plus actual uptake and cost measurements before
promoting it. This review does not authorize a new experiment or replace the
frozen base-evidence submission.

## Primary evidence and version identity

- [Notebook](https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2).
  The title says v2; Kaggle's version counter is **10**. The public indexed page
  [for scriptVersionId 357955943](https://www.kaggle.com/code/flexonafft/gemma-4-budget-aware-coding-agent-v2/input?scriptVersionId=357955943)
  records Public Score 0.22 and Best Score 0.22 V10. This is another account's
  public record, not an authenticated submission receipt or a repeated result
  from our account.
- Public `GetKernel`, explicitly pinned with `versionLabel=v10`, returned the
  same notebook source as the unversioned pull. Source SHA-256:
  `ec76bd9a4dedc4626bee9d31781469023e6cfe29b666afd095dff5723f717e7b`.
  [Pinned source endpoint](https://www.kaggle.com/api/v1/kernels/pull/flexonafft/gemma-4-budget-aware-coding-agent-v2?versionLabel=v10).
- The source credits matterhorn3838's SuperAgent, describes an earlier adaptation
  at 0.18, and labels the navigation candidate unscored. Those are source comments;
  their exact chronology relative to submission and scoring is unverified.
  An unscored-at-authoring comment does not establish that the code was never
  scored. Keep it separate from the public page's later score record.
- Official SDK `kernels.KernelsApiService/ListKernelSessionOutput` with owner
  `flexonafft`, the notebook slug and `versionLabel=v10` returned `submission.zip`
  plus its CPU build log. The downloaded 3,713-byte ZIP SHA-256 was
  `6ff73d104725cc31deadd18787f3f55e5ce534889cec82387e3b280637d34887`.
  The log printed the same hash. The SDK operation and version-label format were
  checked against Kaggle's SDK/CLI source. No signed download URL is retained here.

## What actually changes from our exact Budget-Fit V2

The comparison uses the archive attributed to lynnsakurai, source ZIP SHA-256
`a4b10f6b8034fd7fffa144a7ee3fbd8faf9a84503ffb1349d1522ba048b534d3`,
the same comparator that scored 0.17 in our submission 58019162.

| Component | Byte comparison | Actual implication |
| --- | --- | --- |
| `agent.yaml` | Identical | One 31B root, nine declared native tools; no adapter, subagent or executable Skill |
| `configs/sampling.yaml` | Identical | Temperature 0.2, top-p 0.95, max output 8192, thinking 4096 |
| `eval_config.yaml` | Identical | Eight minutes, 28 configured tool calls, 80 turns, timeout_seconds 240 |
| `prompts/system.md` | Different | Behavior policy is the intervention; 6,323 versus 5,342 characters, not measured tokens |

This candidate does not implement an automatic budget scheduler, a new tool, a
learned decision policy or a deterministic edit-recovery controller. Its call
plan is conveyed through instructions to the agent. A policy implemented in a
prompt can still matter; its contribution must be established through behavior
and independent outcomes rather than inferred from the title.

| Policy area | Our exact V2 | Retrieved Flexon V10 | Research interpretation |
| --- | --- | --- | --- |
| Navigation | Bounded batched text search; narrow implementation plus useful caller/test/sibling | Explicitly batch already-known identifiers, callers and test paths; about 20 matches per search, 40-line reads and up to three regions | More prescriptive batching could reduce serial calls; much of the principle is already present |
| Graph tools | One search rescue after two text failures; one neighbor call if useful | Forbid all three graph tools while keeping their declarations | A real policy difference, but no general proof that those tools are useless |
| First edit | Normally by call 10; absolutely by 12 | Read calls 1–8; edit calls 9–12; force best guess by 12 | Both already impose early editing; no new capability demonstrated |
| Edit matching failures | Reread, shorten the unique match, then guarded Python replacement after two failures | Essentially the same recovery rule | Do not count this as an absent capability in our V2 |
| Verification | Combine diff/syntax/focused execution where practical; 120-second focused test example | Search for a matching test, 150-second focused test example; at most two verification calls | Timing, batching and interpretation differ; no new ground-truth oracle |
| Ambiguous or failed search | Prefer a literal contract-consistent minimal patch | Require a best candidate edit even after unsuccessful searches | Could reduce empty patches and also increase unsupported edits; direction is unmeasured |

## Actual checks completed

1. Inspected every executable cell before execution. They define four submission
   files, validate includes/configuration and write the ZIP. No model invocation
   or submission operation occurs in these cells.
2. Executed all four cells on CPU in a Python process with output isolated to a
   research directory. The internal configuration checks and ZIP integrity
   checks passed. The resulting ZIP was byte-identical to V10's official output.
3. Compared all four ZIP members with our pinned V2, producing the table above.
   Published V10 prompt SHA-256:
   `7f8dde62578a247ffbfc1a519b712ae65849fcfae1ee70c49e0628cab74cbef6`.
   The other three hashes equal the pins in `prepare_public_budgetfit_v2.py`.
4. Compiled the extracted package using official `adk_submission==0.2.13` and
   `google-adk==1.36.1`. The registry supplied the 31B model alias with an
   inference stub that raises if called, and nine unused tool stubs. Result:
   one `LlmAgent`, nine tools, zero subagents. Compilation passed; no model ran.

**Unexecuted:** live agent compliance, navigation efficiency, edit recovery rate,
agent-selected assertion relevance, final patch grading and our own 0.22 score
reproduction. A CPU packaging success measures engineering compatibility only.

## Hypothesis → evidence → next falsification

**Local hypothesis.** Batching independent, already-known navigation requests can
preserve more of a fixed budget for useful editing and verification. The source
expresses a plausible policy. It provides no intervention-level causal result.
Our V2 already batches searches, so a comparison must isolate the additional
policy rather than credit all batching as new.

**Global hypothesis.** Useful source changes per unit solver time may matter more
than adding another information action. The exact three-file match makes the
external policy an appropriate comparator, but it does not establish that
navigation is the dominant failure class on our 31B tasks.

**Smallest discriminating model experiment, when separately authorized.** Keep
the original checkpoint, prompt and budgets except for one navigation policy
change. Use tasks locked before inference, at least two repositories, and retain
failures and missing-check tasks. Match requested information and record tool
rounds, returned context, time to first source edit, verification reached and
independent final correctness. Reduced calls without correctness improvement
falsify the competitive benefit; a higher unsupported-edit rate counts against
the mechanism. Do not copy the whole prompt and call the result an ablation.

**Decision.** Continue considering execution efficiency as a competing hypothesis.
Retain the external artifact as a comparator; do not promote it solely from the
highest displayed score or layer its whole prompt onto the paired-check action.
The paired-check candidate's existing causal test remains required to establish
that its additional observations improve decisions enough to pay their cost.


## Bottleneck reassessment after the comparator review

This supersedes treating the navigation-only experiment above as the immediate
priority. A 0.17 result from our account and another account's 0.22 are not an
observed five-point gain of our intervention. No original paired-check quality
result exists yet. The smaller displayed gap cannot diagnose a model ceiling.

**Leading hypothesis, not a demonstrated dominant cause:** after source and
feedback are available, the agent fails to produce or execute an appropriately
changed repair. Distinguish malformed execution, wrong repair generation, and
rejecting/selecting an otherwise correct candidate. Additional observations only
help if the agent can use them to change its next action.

Three existing records constrain this diagnosis:

1. In the external 31B, thinking-off 33-task series, v6.0 supplied current source
   lines on failed edits and reduced exact repeats from 14% to 10%, but still
   solved 14/33, tying v5.8. Fifteen of 33 failing scripts were followed by the
   identical script. This supports the existence of a feedback-use problem,
   without proving that it dominates our thinking-on 31B.
   [Pinned v6.0 record](https://github.com/happyc0der/gemma-swe-agent/blob/88cfbc6dc9fdce17f90117e17c2ff8c365c7eb16/experiments/2026-10-20-faithful-v60-AB/notes.md).
2. In that external thinking-off baseline's single-bullet edit-recovery screen,
   the Python fallback followed only 6 of 236 erroring edit calls, in two tasks.
   Solves were 7/33 versus baseline 9/33. These are dependent call opportunities
   and one run per variant; the result is a negative screen of compliance, not
   a general harmful-effect estimate.
   [Pinned recovery screen](https://github.com/happyc0der/gemma-swe-agent/blob/88cfbc6dc9fdce17f90117e17c2ff8c365c7eb16/experiments/2026-10-24-faithful-bf-editfb-off-AB/notes.md).
3. A different external Budget-Fit diagnostic pool reports file overlap with
   reference fixes in 52 of 69 verification-failed attempts across 19 tasks.
   This does not establish correct symbol/root-cause localization, but it rules
   out treating every failed repair as merely failing to find a file.
   [Primary report, section 10](https://pilkwangkim.github.io/posts/Gemma-4-Developer-Agent-Part-2-Measuring-an-Agent-While-Its-Evaluator-Moved/#10-what-the-agents-own-checks-do-not-establish).

**Decision.** Stop extending navigation rules or adding feedback features as the
presumed remedy. Retain the existing prototype for testing, and put correct
repair generation and feedback-driven action changes ahead of further tool
engineering in the hypothesis ranking. Requirement omissions and runtime/tool
failures remain competing explanations; our hidden 31B failure mix is unknown.
This is not evidence that fine-tuning, more agents, or more search is required.

**Next discriminating measurement, unexecuted.** At a shared 31B checkpoint where
relevant code has already been read, keep the issue, source, tools and total
remaining budget fixed. In the existing continuation/retry comparison, retain
candidate snapshots and independently grade candidate availability separately
from the final patch. Do not add inference merely to generate an oracle statistic.
If correct candidates rarely appear, prioritize repair generation. If correct
candidates appear but are discarded or replaced, prioritize selection/stop
control. If an intended edit never reaches the tree because requests are
malformed, prioritize the execution interface. Compare final correctness with
the same total cost; an oracle label is diagnostic evidence, not a deployable
selector. Choose the evaluation tasks before seeing these outcomes and retain
all failures. No model experiment, CPU patch grading, training or submission was
executed for this reassessment.
