from src.fintech_ingest import PaymentEvent, risk_action, chunk_text


def test_large_payment_requires_review_and_chunks_are_stable():
    event = PaymentEvent("p-1", "a-1", 10000, "USD", "settlement")
    assert risk_action(event) == "review"
    assert chunk_text("one two three", size=2) == ["one two", "three"]
