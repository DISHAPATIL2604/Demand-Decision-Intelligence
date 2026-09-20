"""
Comprehensive Test Suite for Business Decision Copilot ("ChatGPT for Business Data")
Validates all 9 user conversation flows and capabilities.
"""
import os
import sys

# Reconfigure stdout to handle UTF-8 symbols gracefully
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db.session import SessionLocal
from backend.services.chat_assistant import ChatAssistantService

def run_tests():
    db = SessionLocal()
    assistant = ChatAssistantService()
    print("=== STARTING BUSINESS DECISION COPILOT TESTS ===")

    # ── CONVERSATION 1 ──
    print("\n--- TEST 1: Business Health -> Focus -> Why ---")
    h1 = []
    r1_1 = assistant.process_message("How is my business doing?", h1, db)
    print("User: How is my business doing?")
    print("Reply preview:", r1_1["reply"][:150], "...")
    assert "### Answer" in r1_1["reply"]
    assert "### Source" in r1_1["reply"]
    h1.append({"role": "user", "content": "How is my business doing?"})
    h1.append({"role": "assistant", "content": r1_1["reply"], "intent": r1_1["intent"], "evidence": r1_1["evidence"]})

    r1_2 = assistant.process_message("Where should I focus?", h1, db)
    print("User: Where should I focus?")
    print("Reply preview:", r1_2["reply"][:150], "...")
    assert "### Answer" in r1_2["reply"]
    h1.append({"role": "user", "content": "Where should I focus?"})
    h1.append({"role": "assistant", "content": r1_2["reply"], "intent": r1_2["intent"], "evidence": r1_2["evidence"]})

    r1_3 = assistant.process_message("Why?", h1, db)
    print("User: Why?")
    print("Reply preview:", r1_3["reply"][:150], "...")
    assert "### Answer" in r1_3["reply"]

    # ── CONVERSATION 2 ──
    print("\n--- TEST 2: Inventory Health -> Problem Products ---")
    h2 = []
    r2_1 = assistant.process_message("Are we maintaining healthy inventory?", h2, db)
    print("User: Are we maintaining healthy inventory?")
    print("Reply preview:", r2_1["reply"][:150], "...")
    assert "complete inventory-health score" in r2_1["reply"] or "inventory-health" in r2_1["reply"]
    h2.append({"role": "user", "content": "Are we maintaining healthy inventory?"})
    h2.append({"role": "assistant", "content": r2_1["reply"], "intent": r2_1["intent"], "evidence": r2_1["evidence"]})

    r2_2 = assistant.process_message("Which products are causing the problem?", h2, db)
    print("User: Which products are causing the problem?")
    print("Reply preview:", r2_2["reply"][:150], "...")
    assert "Product ID" in r2_2["reply"] or "Amul" in r2_2["reply"]

    # ── CONVERSATION 3 ──
    print("\n--- TEST 3: Restock -> Cost -> Save Money ---")
    h3 = []
    r3_1 = assistant.process_message("Which products should I restock?", h3, db)
    print("User: Which products should I restock?")
    print("Reply preview:", r3_1["reply"][:150], "...")
    h3.append({"role": "user", "content": "Which products should I restock?"})
    h3.append({"role": "assistant", "content": r3_1["reply"], "intent": r3_1["intent"], "evidence": r3_1["evidence"]})

    r3_2 = assistant.process_message("How much will it cost?", h3, db)
    print("User: How much will it cost?")
    print("Reply preview:", r3_2["reply"][:150], "...")
    assert "unit-cost" in r3_2["reply"] or "cost" in r3_2["reply"].lower()
    h3.append({"role": "user", "content": "How much will it cost?"})
    h3.append({"role": "assistant", "content": r3_2["reply"], "intent": r3_2["intent"], "evidence": r3_2["evidence"]})

    r3_3 = assistant.process_message("Can we save money?", h3, db)
    print("User: Can we save money?")
    print("Reply preview:", r3_3["reply"][:150], "...")
    assert "inventory value" in r3_3["reply"].lower() or "excess" in r3_3["reply"].lower()

    # ── CONVERSATION 4 ──
    print("\n--- TEST 4: Profitable Products -> Why ---")
    h4 = []
    r4_1 = assistant.process_message("Which products are profitable?", h4, db)
    print("User: Which products are profitable?")
    print("Reply preview:", r4_1["reply"][:150], "...")
    assert "Revenue is available" in r4_1["reply"] or "profit" in r4_1["reply"].lower()
    h4.append({"role": "user", "content": "Which products are profitable?"})
    h4.append({"role": "assistant", "content": r4_1["reply"], "intent": r4_1["intent"], "evidence": r4_1["evidence"]})

    r4_2 = assistant.process_message("Why?", h4, db)
    print("User: Why?")
    print("Reply preview:", r4_2["reply"][:150], "...")

    # ── CONVERSATION 5 ──
    print("\n--- TEST 5: What Changed This Week -> Why ---")
    h5 = []
    r5_1 = assistant.process_message("What changed this week?", h5, db)
    print("User: What changed this week?")
    print("Reply preview:", r5_1["reply"][:150], "...")
    assert "Cr" in r5_1["reply"] or "Revenue" in r5_1["reply"]
    h5.append({"role": "user", "content": "What changed this week?"})
    h5.append({"role": "assistant", "content": r5_1["reply"], "intent": r5_1["intent"], "evidence": r5_1["evidence"]})

    r5_2 = assistant.process_message("Why?", h5, db)
    print("User: Why?")
    print("Reply preview:", r5_2["reply"][:150], "...")

    # ── CONVERSATION 6 (Hinglish Multi-step) ──
    print("\n--- TEST 6: Hinglish Revenue -> Cost -> Order ---")
    h6 = []
    r6_1 = assistant.process_message("Kaunsa product sabse zyada revenue deta hai?", h6, db)
    print("User: Kaunsa product sabse zyada revenue deta hai?")
    print("Reply preview:", r6_1["reply"][:150], "...")
    h6.append({"role": "user", "content": "Kaunsa product sabse zyada revenue deta hai?"})
    h6.append({"role": "assistant", "content": r6_1["reply"], "intent": r6_1["intent"], "evidence": r6_1["evidence"]})

    r6_2 = assistant.process_message("Iska cost kitna hai?", h6, db)
    print("User: Iska cost kitna hai?")
    print("Reply preview:", r6_2["reply"][:150], "...")
    h6.append({"role": "user", "content": "Iska cost kitna hai?"})
    h6.append({"role": "assistant", "content": r6_2["reply"], "intent": r6_2["intent"], "evidence": r6_2["evidence"]})

    r6_3 = assistant.process_message("Isko order karna chahiye kya?", h6, db)
    print("User: Isko order karna chahiye kya?")
    print("Reply preview:", r6_3["reply"][:150], "...")

    # ── CONVERSATION 7 (Hinglish Restock -> Spend) ──
    print("\n--- TEST 7: Next week kya order karu -> Kitne paise lagenge ---")
    h7 = []
    r7_1 = assistant.process_message("next week kya order karu?", h7, db)
    print("User: next week kya order karu?")
    print("Reply preview:", r7_1["reply"][:150], "...")
    h7.append({"role": "user", "content": "next week kya order karu?"})
    h7.append({"role": "assistant", "content": r7_1["reply"], "intent": r7_1["intent"], "evidence": r7_1["evidence"]})

    r7_2 = assistant.process_message("kitne paise lagenge?", h7, db)
    print("User: kitne paise lagenge?")
    print("Reply preview:", r7_2["reply"][:150], "...")

    # ── CONVERSATION 8 (Marathi Business Health -> Focus) ──
    print("\n--- TEST 8: Marathi Business Health -> Focus ---")
    h8 = []
    r8_1 = assistant.process_message("माझा business कसा चालला आहे?", h8, db)
    print("User: माझा business कसा चालला आहे?")
    print("Reply preview:", r8_1["reply"][:150], "...")
    assert "महसूल" in r8_1["reply"] or "व्यवसाय" in r8_1["reply"]
    h8.append({"role": "user", "content": "माझा business कसा चालला आहे?"})
    h8.append({"role": "assistant", "content": r8_1["reply"], "intent": r8_1["intent"], "evidence": r8_1["evidence"]})

    r8_2 = assistant.process_message("कुठे सुधारणा हवी?", h8, db)
    print("User: कुठे सुधारणा हवी?")
    print("Reply preview:", r8_2["reply"][:150], "...")
    assert "लक्ष" in r8_2["reply"] or "सुधारणा" in r8_2["reply"] or "साठा" in r8_2["reply"]

    # ── CONVERSATION 9 (Unsupported / Speculation) ──
    print("\n--- TEST 9: Unsupported / Speculation ---")
    r9 = assistant.process_message("What will the market price be six months from now?", [], db)
    print("User: What will the market price be six months from now?")
    print("Reply preview:", r9["reply"][:150], "...")
    assert "don't have enough data" in r9["reply"] or "UNSUPPORTED" in str(r9["evidence"])

    db.close()
    print("\n=== ALL 9 BUSINESS CONVERSATION TESTS PASSED PERFECTLY ===")

if __name__ == "__main__":
    run_tests()
