# Input contract

The complete executable contract is [examples/input.json](../examples/input.json), with a result at [examples/expected.json](../examples/expected.json). Input is one UTF-8 JSON object, at most 1 MiB. IDs must be unique within the input. Invalid structural fields fail the run; domain check failures appear in the report.

`documents` maps citation IDs to source text. Each case includes `id`, `answer`, boolean `answerable` and `abstained`, nonempty `expected_terms` for answerable cases, and `citations` containing `document_id` and exact `quote`. Terms are case-insensitive substrings; quotes are case-sensitive substrings. Abstention is supplied explicitly and requires manual validation against the actual answer.

Commands: `run INPUT` reports without network; `gate INPUT` exits 2 for a failed report; `save INPUT` persists; `cloud-smoke INPUT` persists and checks a fresh client; `get ID` reads; `list` retrieves up to 20 newest IDs. Success is exit 0; malformed input/configuration/network failure is exit 1.
