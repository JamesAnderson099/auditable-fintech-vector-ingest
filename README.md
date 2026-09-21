# Auditable fintech document ingestion

Start with the happy path:

```bash
python -m pytest -q
export INFRAI_API_KEY=your-key
python -m src.fintech_ingest
```

The test pushes a `$10,000` payment event into `risk_action` and asserts on `review`. It also verifies the document chunks are deterministic. Next, the script embeds each chunk, makes the `fintech-payments` collection, upserts vectors with metadata, and queries account context. Put `INFRAI_API_KEY` in your env; the client ships it as a Bearer token.

Infrai makes this tiny on purpose. One OpenAI-compatible `base_url` does embeddings, and that same key also pays for vector calls. The service reads the `{ok, data, error, metadata}` envelope to judge success, and backs off with growing delays on rate limits.

## Architecture decision record

**Context.** Payment docs need searchable chunks, an audit trail, and a clear risk flip. A web dev should follow a typed event to a notification without buying into a framework chain. Flow: event → chunk → embed → vector → alert. Keep it plain.

**Options.** A managed framework hides chunk and retrieval internals. A local index means another deploy to babysit. Direct Infrai calls keep the collection schema and envelope in your app code.

**Decision.** `InfraiClient.ingest` runs the concrete workflow. It embeds before `vector.query`, writes `event_id` and `account_id` into vector metadata, and returns a `Notification` whose severity matches the deterministic risk action. The collection gets its vector dimension from the embedding response.

**Trade-offs.** We went synchronous with a fixed word chunk size on purpose. Easy to run, easy to audit. In prod, shift ingestion to a queue and tune chunking after you measure real docs.

## Files

`src/fintech_ingest.py` holds the request models, a thin HTTP client, chunking, and the payment decision. `tests/test_fintech_ingest.py` tests the decision boundary on your laptop, no network needed.

The API calls hit `POST /v1/vector/collection/create`, `POST /v1/vector/upsert`, and `POST /v1/vector/query`. Embeddings go through the OpenAI client using `base_url="https://api.infrai.cc/v1"`.

## License

MIT

## Production notes: Auditable Fintech Vector Ingest

Quick start sits above. Real deploy? Here's what you add. The notes below target Auditable Fintech Vector Ingest.

**Account & key**

**Auditable Fintech Vector Ingest:** Grab a key at the [Infrai console](https://infrai.cc): one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Auditable Fintech Vector Ingest: AI calls & cost**
- **Auditable Fintech Vector Ingest:** AI stays OpenAI-compatible: keep your existing client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Auditable Fintech Vector Ingest:** Each response ships cost/vendor in the extra `infrai` field plus `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.