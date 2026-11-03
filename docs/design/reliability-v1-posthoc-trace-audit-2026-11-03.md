# Reliability-v1 post-hoc trace mechanics audit

## Intent

Explain why Reliability-v1 became smaller/faster without improving the 17-task development resolved count, using already-completed traces only.

This is a read-only mechanism audit. It must not mutate the frozen Reliability-v1 submission, rerun the 17-task diagnostic, consume Kaggle GPU, inspect hidden/blind evidence, or promote a new candidate.

## Question

On the same inspected 17-task development denominator, did Reliability-v1 change the sequence of evidence gathering, editing, verification, repair, and submission in a way that can explain `1/17 -> 1/17` despite smaller patches and lower runtime?

## Inputs

Existing completed Kaggle kernels only:

- topology single-root: `kolihhan/gemma4-topology-single-41458804862`
- Reliability-v1 diagnostic: `kolihhan/gemma4-reliability-v1-diag-41485671952`

Both use the same frozen 17-task manifest.

## Measurement

For root-agent traces (`author=swe_e4b_coder`), reduce raw traces to mechanics only:

- tool category sequence, never raw message text;
- edit/mutation count;
- targeted vs broad verification count;
- whether a targeted behavioral check occurs before the first source mutation;
- whether a failed targeted check after mutation is followed by another mutation;
- whether that repair is followed by a targeted retest;
- whether final targeted evidence passes;
- whether submission occurs after failing targeted evidence;
- localization-tool counts.

Source mutation is conservatively detected from explicit edit tools plus narrow script-edit signatures. Ambiguous command-side mutations remain unclassified rather than guessed.

## Output boundary

Persist only compact JSON summaries and A/B aggregate comparison. Do not upload raw traces, problem statements, assistant messages, tool arguments, source snippets, patches, or reference fields.

## Interpretation contract

- A lack of pre-edit targeted evidence strengthens the evidence-first/reproduction hypothesis but does not prove F2.
- A failed post-edit targeted check followed by no repair strengthens an F5 repair-convergence hypothesis.
- A repair followed by another failing targeted check shows attempted convergence but cannot alone distinguish F2 from F3.
- F2 vs F3 remains unresolved unless evidence directly separates wrong semantic hypothesis from wrong implementation.
- The audit may reorder hypotheses; it may not select/promote a candidate.

## Resource rule

Use a cheap GitHub Action to download the two existing private Kaggle kernel outputs and analyze them. No Kaggle kernel push, no accelerator, no competition submission.
