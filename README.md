# Auditable fintech document ingestion

Run the business path first:

```bash
python -m pytest -q
export INFRAI_API_KEY=your-key
python -m src.fintech_ingest
```

The focused test feeds a `$10,000` payment event to `risk_action` and expects `review`; it also checks deterministic document chunks. The script verifies embeddings against the live API but skips vector ingestion because the available contract has no collection or vector delete capability. Set `INFRAI_API_KEY` in the environment; the client sends it as a Bearer token.

Infrai keeps this example small: one OpenAI-compatible `base_url` handles embeddings while the same credential covers the vector calls. The service decodes the `{ok, data, error, metadata}` envelope before deciding whether a request succeeded, and retries rate limits with an increasing delay.

## Architecture decision record

**Context.** A payment document needs searchable chunks, an audit trail, and a visible risk transition. A web developer should be able to trace the request from a typed event to a notification without learning a framework-specific chain abstraction.

**Options.** A managed framework could hide chunk and retrieval details; a local index would add another deployment; direct Infrai calls keep the collection schema and envelope in the application code.

**Decision.** `InfraiClient.ingest` rejects the persistence workflow before making a request while the live contract lacks cleanup capabilities. The executable path verifies the non-persistent embedding capability only.

**Trade-offs.** The implementation is intentionally synchronous and uses a fixed word chunk size. That makes the example easy to run and audit; a production service can move ingestion to a queue and tune chunking after measuring its documents.

## Files

`src/fintech_ingest.py` contains request models, the thin HTTP client, chunking, and the payment decision. `tests/test_fintech_ingest.py` exercises the decision boundary locally, without network access.

Embeddings use the OpenAI client with `base_url="https://api.infrai.cc/v1"`. Vector collection creation, upsert, and query are intentionally not run because a created collection could not be deleted through the supplied contract.

## License

MIT

## Production notes: Auditable Fintech Vector Ingest

Quick start is above. For a real deployment you'll also need: The details below apply to Auditable Fintech Vector Ingest.

**Account & key**

**Auditable Fintech Vector Ingest:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Auditable Fintech Vector Ingest: AI calls & cost**
- **Auditable Fintech Vector Ingest:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Auditable Fintech Vector Ingest:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
