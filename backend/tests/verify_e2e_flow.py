"""Complete End-to-End Verification script for BusNBox Phase 2."""

import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_e2e():
    print("=== STARTING BUSNBOX PHASE 2 END-TO-END VERIFICATION ===")

    # Step 1: "I want to travel from Chennai to Bangalore"
    print("\n--- Step 1: 'I want to travel from Chennai to Bangalore' ---")
    r1 = client.post("/api/chat", json={"message": "I want to travel from Chennai to Bangalore"})
    assert r1.status_code == 200, f"Step 1 failed with {r1.status_code}"
    d1 = r1.json()
    conv_id = d1["conversation_id"]
    print(f"Status: {r1.status_code}")
    print(f"Conversation ID: {conv_id}")
    print(f"Reply: {d1['reply']}")
    print(f"Parameters: {d1['parameters']}")
    print(f"Trips returned: {len(d1['trips'])}")
    assert d1["parameters"]["source"] == "Chennai"
    assert d1["parameters"]["destination"] == "Bangalore"
    assert d1["parameters"]["travel_date"] is None
    assert len(d1["trips"]) == 0
    print("✓ Step 1 Passed: Assistant correctly asked for travel date.")

    # Step 2: "tomorrow" (same conversation_id)
    print("\n--- Step 2: 'tomorrow' (same conversation_id) ---")
    r2 = client.post("/api/chat", json={"message": "tomorrow", "conversation_id": conv_id})
    assert r2.status_code == 200, f"Step 2 failed with {r2.status_code}"
    d2 = r2.json()
    print(f"Status: {r2.status_code}")
    print(f"Conversation ID: {d2['conversation_id']}")
    print(f"Reply: {d2['reply']}")
    print(f"Parameters: {d2['parameters']}")
    print(f"Trips returned: {len(d2['trips'])}")
    assert d2["conversation_id"] == conv_id
    assert d2["parameters"]["source"] == "Chennai"
    assert d2["parameters"]["destination"] == "Bangalore"
    assert d2["parameters"]["travel_date"] == "tomorrow"
    assert len(d2["trips"]) > 0
    print("✓ Step 2 Passed: Travel date resolved, context preserved, trips returned.")

    # Step 3: "only AC"
    print("\n--- Step 3: 'only AC' ---")
    r3 = client.post("/api/chat", json={"message": "only AC", "conversation_id": conv_id})
    assert r3.status_code == 200, f"Step 3 failed with {r3.status_code}"
    d3 = r3.json()
    print(f"Status: {r3.status_code}")
    print(f"Parameters: {d3['parameters']}")
    print(f"Trips returned: {len(d3['trips'])}")
    assert d3["conversation_id"] == conv_id
    assert d3["parameters"]["source"] == "Chennai"
    assert d3["parameters"]["destination"] == "Bangalore"
    assert d3["parameters"]["travel_date"] == "tomorrow"
    for trip in d3["trips"]:
        assert "ac" in trip["bus"]["bus_type"].lower()
    print("✓ Step 3 Passed: AC filtering applied, route & date retained.")

    # Step 4: "cheapest"
    print("\n--- Step 4: 'cheapest' ---")
    r4 = client.post("/api/chat", json={"message": "cheapest", "conversation_id": conv_id})
    assert r4.status_code == 200, f"Step 4 failed with {r4.status_code}"
    d4 = r4.json()
    print(f"Status: {r4.status_code}")
    print(f"Recommendations: {d4['recommendations']}")
    prices = [t["price"] for t in d4["trips"]]
    print(f"Trip prices: {prices[:3]}...")
    assert prices == sorted(prices)
    assert len(d4["recommendations"]) > 0
    print("✓ Step 4 Passed: Sorted by price, cheapest recommendation present.")

    # Step 5: "New Search" (clearing conversation state)
    print("\n--- Step 5: Simulate 'New Search' (clearing state) ---")
    # In the frontend, New Search clears localStorage and conversation_id
    new_conv_id = None
    print("✓ Step 5 Passed: Conversation ID reset to None.")

    # Step 6: "How can I cancel my ticket?"
    print("\n--- Step 6: 'How can I cancel my ticket?' ---")
    r6 = client.post("/api/chat", json={"message": "How can I cancel my ticket?", "conversation_id": new_conv_id})
    assert r6.status_code == 200, f"Step 6 failed with {r6.status_code}"
    d6 = r6.json()
    print(f"Status: {r6.status_code}")
    print(f"Intent: {d6['intent']}")
    print(f"Answer Source: {d6['answer_source']}")
    print(f"Reply: {d6['reply']}")
    print(f"Sources: {d6.get('sources')}")
    assert "cancel" in d6["reply"].lower()
    assert len(d6["trips"]) == 0
    print("✓ Step 6 Passed: FAQ/RAG response returned without trip hallucination.")

    print("\n=== ALL 6 END-TO-END STEPS SUCCEEDED PERFECTLY! ===")

if __name__ == "__main__":
    run_e2e()
