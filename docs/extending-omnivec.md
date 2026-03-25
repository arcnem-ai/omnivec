# Extending Omnivec

Omnivec already has a useful shape for future work.

The pipeline from ZIP upload through extraction, classification, duplicate grouping, similarity search, and clustering is deterministic. That work produces saved artifacts, and the final report is generated from those artifacts.

That separation is a useful base to build on. The most natural next steps are the ones that keep the current analysis pipeline intact while doing more with the saved results.

The sections below are a few good places to start if you want to build on the codebase.

## 1. Save a structured curation plan alongside the report

Today the final output is mostly prose. A natural next step is to also save a machine-readable plan with concrete suggestions.

Examples:

- which file in a duplicate group should be treated as canonical
- which filenames should be normalized
- which assets belong in a better folder
- which assets look safe to archive or ignore

Start with:
`src/omnivec/reporting.py`, `src/omnivec/schemas.py`, `src/omnivec/storage.py`, and `src/omnivec/api.py`

## 2. Support follow-up curation against saved analysis

Right now each run ends with a final report. Another useful extension would let people continue working from the saved analysis and saved plan.

Examples:

- "Which document cluster looks safest to merge?"
- "What should I check manually before deleting duplicates?"
- "Suggest better names for the files in this cluster."
- "Which groups look related but not identical?"

Start with:
`src/omnivec/api.py`, `src/omnivec/jobs.py`, `src/omnivec/storage.py`, and a new service for post-run questions

## 3. Add approval-based execution for proposed actions

Once the system can produce structured plans and support follow-up review, the next step is to let it carry out approved actions.

A sensible progression would be:

1. generate proposed actions
2. show them to the user
3. apply only approved actions
4. save the executed plan as an artifact

Good approval tiers:

- low risk: metadata or labels
- medium risk: renames and moves
- high risk: deletes or destructive merges

Start with:
`src/omnivec/api.py`, `src/omnivec/jobs.py`, `src/omnivec/storage.py`, and a new execution layer for approved actions
