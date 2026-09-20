import os
import re
import json
import pandas as pd
from typing import List, Dict, Any, Tuple
import requests
from sqlalchemy.orm import Session
from backend.models.demand import DailyProductDemand

class ChatAssistantService:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.inventory_path = "reports/inventory_decision_sample.csv"
        self.anomalies_path = "reports/demand_anomalies.csv"

    def determine_intent(self, message: str) -> str:
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["stock", "inventory", "reorder", "risk", "stockout"]):
            return "inventory"
        if any(w in msg_lower for w in ["anomaly", "spike", "drop", "unusual", "alert", "why did"]):
            return "anomaly"
        if any(w in msg_lower for w in ["forecast", "predict", "future", "next week"]):
            return "forecast"
        return "demand"

    def retrieve_context(self, intent: str, message: str, db: Session) -> Tuple[str, List[str]]:
        context = []
        citations = []
        
        # Simple extraction of numbers as product IDs
        product_ids = re.findall(r'\b\d{4,}\b', message)
        
        try:
            if intent == "inventory" and os.path.exists(self.inventory_path):
                df = pd.read_csv(self.inventory_path)
                if product_ids:
                    df = df[df['product_id'].astype(str).isin(product_ids)]
                else:
                    df = df[df['risk_status'] == 'CRITICAL_STOCKOUT'].head(5)
                if not df.empty:
                    context.append("Inventory Data:\n" + df.to_string(index=False))
                    citations.append("inventory_decision_sample.csv")
            
            elif intent == "anomaly" and os.path.exists(self.anomalies_path):
                df = pd.read_csv(self.anomalies_path)
                if product_ids:
                    df = df[df['product_id'].astype(str).isin(product_ids)]
                else:
                    df = df.head(5)
                if not df.empty:
                    context.append("Anomaly Data:\n" + df.to_string(index=False))
                    citations.append("demand_anomalies.csv")
            
            elif intent == "demand" or intent == "forecast":
                # For forecast we just use recent demand if forecast isn't explicitly in CSV
                if product_ids:
                    pid = int(product_ids[0])
                    results = db.query(DailyProductDemand).filter(DailyProductDemand.product_id == pid).order_by(DailyProductDemand.date_.desc()).limit(5).all()
                    if results:
                        demands = "\n".join([f"Date: {r.date_}, Qty: {r.total_quantity}, City: {r.city_name}" for r in results])
                        context.append("Recent Demand Data:\n" + demands)
                        citations.append("daily_product_demand (DB)")
        except Exception as e:
            print(f"Error retrieving context: {e}")

        if not context:
            return "No specific data found for your query in the available records.", citations
        
        return "\n\n".join(context), citations

    def get_suggestions(self) -> List[str]:
        return [
            "Which products have critical stockout risk in Delhi?",
            "What is the forecasted demand for SKU 19512 next week?",
            "Why did product 391306 trigger an anomaly alert?",
            "Show me recent sales trends for top products"
        ]

    def call_gemini(self, prompt: str) -> str:
        if not self.gemini_api_key:
            return None
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return None

    def process_message(self, message: str, history: List[Dict], db: Session) -> Dict:
        intent = self.determine_intent(message)
        context_str, citations = self.retrieve_context(intent, message, db)
        
        system_prompt = (
            "You are an AI Decision Assistant for a Demand & Decision Intelligence project. "
            "Answer the user's question based ONLY on the following retrieved project data. "
            "If the data doesn't contain the answer, say 'I don't have enough data to answer that'. "
            "Do not invent forecasts, stock levels, or metrics.\n\n"
            f"Retrieved Data:\n{context_str}\n\n"
            f"User Question: {message}"
        )
        
        reply = self.call_gemini(system_prompt)
        
        if not reply:
            # Fallback mode
            reply = (
                f"**Fallback Mode (LLM API unavailable)**\n\n"
                f"I detected your intent as '{intent}'. Here is the relevant raw data I found:\n\n"
                f"```text\n{context_str}\n```\n\n"
                f"*Please configure GEMINI_API_KEY for natural language insights.*"
            )

        return {
            "reply": reply,
            "citations": citations
        }
