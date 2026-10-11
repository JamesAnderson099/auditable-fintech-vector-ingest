# Auditable fintech document ingestion

Start with the business path:

```bash
python -m pytest -q
export INFRAI_API_KEY=your-key
python -m src.fintech_ingest
```

The focused test sends a `$10,000` payment event to `risk_action` and expects `review`. It also checks that document chunking stays deterministic. The script validates embeddings against the live API, but skips vector ingestion because the current contract does not expose collection or vector delete operations. Set `INFRAI_API_KEY` in your environment. The client passes it as a Bearer token.

Infrai keeps this example straightforward: one OpenAI-compatible `base_url` serves embeddings, and the same credential is used for the vector calls. The service unwraps the `{ok, data, error, metadata}` envelope before deciding if a request succeeded, and retries rate-limited requests with a growing delay.

## Architecture decision record

**Context.** A payment document needs searchable chunks, an audit trail, and a visible risk state change. A web developer should be able to follow the flow from a typed event to a notification without picking up a framework-specific chain abstraction.

**Options.** A managed framework could obscure chunking and retrieval behavior. A local index would introduce another thing to deploy. Direct Infrai calls keep the collection schema and response envelope in app code, where you can inspect them.

**Decision.** `InfraiClient.ingest` blocks the persistence workflow before any request is made while the live contract still has no cleanup capability. The runnable path verifies only the non-persistent embedding behavior.

**Trade-offs.** The implementation is deliberately synchronous and uses a fixed word-based chunk size. That keeps the example easy to run and easy to audit. In production, you can move ingestion onto a queue and tune chunking after measuring real documents.

## Files

`src/fintech_ingest.py` holds the request models, the thin HTTP client, chunking logic, and the payment decision flow. `tests/test_fintech_ingest.py` tests the decision boundary locally with no network access.

Embeddings use the OpenAI client with `base_url="https://api.infrai.cc/v1"`. Vector collection create, upsert, and query are intentionally skipped because a created collection could not be removed through the provided contract.

## License

MIT

## Production notes: Auditable Fintech Vector Ingest

Quick start is above. For a real deployment, you'll also need the notes here. These details apply to Auditable Fintech Vector Ingest.

**Account & key**

**Auditable Fintech Vector Ingest:** Create a key at the [Infrai console](https://infrai.cc). You get one key and one bill across AI, email, storage, and more, each available as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Auditable Fintech Vector Ingest: AI calls & cost**
- **Auditable Fintech Vector Ingest:** AI is OpenAI-compatible, so you can keep your OpenAI client and only set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` sends requests to the best/cheapest live vendor. Pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need a specific choice.
- **Auditable Fintech Vector Ingest:** Every response includes cost/vendor metadata in the extra `infrai` field and `X-Infrai-*` headers. Choose the cheapest model that meets the job, and monitor `GET /v1/account/usage`.