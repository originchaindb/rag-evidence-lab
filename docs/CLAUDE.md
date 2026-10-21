# Optional Claude capture

The default workflow uses recorded outputs. To capture one real response, put your Claude API key and an available structured-output model ID into the ignored `.env` file as `ANTHROPIC_API_KEY` and `AI_MODEL`. API access is separate from a chat subscription. Set a provider-side budget appropriate for your account before running paid requests.

```sh
python claude_capture.py --live examples/model-request.json
```

This explicit command sends the system prompt, prompt and schema in that file to Anthropic. Review their contents first. It makes one request, allows at most 1000 output tokens, caps the request at 12000 bytes, refuses redirects, and never retries automatically. A local allowance counts up to three attempts **before** network access, including failed requests. This is a request count, not a dollar cap or an account-wide limit. Deleting `.local` resets local state; do not use it as a production billing guard.

The result is saved to `.local/claude-output.json`, including provider-reported usage. It is not committed. Copy output.answer, output.abstained and output.citations into the corresponding evaluation case. Keep documents and expected_terms human-authored.

Then run `python app.py run YOUR_INPUT.json`. The capture helper is a small adapter, not an autonomous agent. Structured output ensures shape at the provider boundary; it does not establish factual correctness. A refusal or truncated response is rejected. No Cloud write or external action follows automatically.

Tests use synthetic provider responses. See VERIFICATION.md for whether live Claude requests were performed in this release.

References: [Messages API](https://platform.claude.com/docs/en/api/messages/create), [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).
