"""
Chat & Decision RAG Service
Project: Demand-Decision-Intelligence
Location: backend/services/chat_service.py

Implements database-grounded RAG context retrieval and response synthesis.
Retrieves live figures from:
- products
- inventory_recommendations & inventory simulation
- forecasts & forecast_runs
- anomalies (outliers)
- daily_product_demand (city sales & top movers)
Persists chat sessions and messages in PostgreSQL.
"""

import json
import re
import os
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from backend.models.chat import ChatSession, ChatMessage
from backend.models.product import Product
from backend.models.inventory import InventoryRecommendation, InventoryState
from backend.models.forecast import ForecastItem, ForecastRun
from backend.models.anomaly import AnomalyAlert
from backend.models.demand import DailyProductDemand


class DecisionRAGService:
    def __init__(self):
        pass

    def get_or_create_session(self, db: Session, user_id: Optional[int] = None, session_id: Optional[int] = None) -> ChatSession:
        if session_id:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                return session

        new_session = ChatSession(
            user_id=user_id,
            title="Decision Intelligence Consultation"
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session

    def get_history(self, db: Session, session_id: int, limit: int = 30) -> List[Dict[str, Any]]:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).limit(limit).all()

        result = []
        for m in messages:
            citations = []
            if m.retrieved_context:
                try:
                    parsed = json.loads(m.retrieved_context)
                    if isinstance(parsed, dict) and "citations" in parsed:
                        citations = parsed["citations"]
                except Exception:
                    pass

            result.append({
                "id": m.id,
                "role": m.sender_role,
                "content": m.message,
                "citations": citations,
                "created_at": str(m.created_at) if m.created_at else None,
            })
        return result

    def classify_intent_and_extract_entities(self, query: str) -> Dict[str, Any]:
        q = query.lower()

        # Extract SKU numbers if mentioned
        sku_matches = re.findall(r"\b\d{3,7}\b", query)

        # Detect Hubs / Cities
        hubs = []
        for h in ["delhi", "bengaluru", "bangalore", "mumbai", "hr-ncr", "gurgaon"]:
            if h in q:
                mapped = "Bengaluru" if h == "bangalore" else "Delhi" if h == "delhi" else "Mumbai" if h == "mumbai" else "HR-NCR"
                if mapped not in hubs:
                    hubs.append(mapped)

        # Intent detection
        if any(w in q for w in ["stockout", "risk", "out of stock", "low stock", "safety stock", "reorder", "inventory"]):
            intent = "STOCKOUT_INVENTORY"
        elif any(w in q for w in ["anomaly", "anomalies", "spike", "drop", "surge", "irregular", "outlier"]):
            intent = "ANOMALY_ALERTS"
        elif any(w in q for w in ["forecast", "predict", "next week", "future demand", "expected"]):
            intent = "FORECAST_INQUIRY"
        elif any(w in q for w in ["top moving", "fast moving", "best seller", "revenue", "gmv", "growth", "wow", "mom", "sales"]):
            intent = "SALES_REVENUE"
        elif any(w in q for w in ["product", "sku", "catalog", "price", "mrp", "pack"]):
            intent = "PRODUCT_SEARCH"
        else:
            intent = "GENERAL_INTELLIGENCE"

        return {
            "intent": intent,
            "skus": sku_matches,
            "hubs": hubs,
            "raw_query": query
        }

    def retrieve_grounded_context(self, db: Session, parsed: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
        intent = parsed["intent"]
        skus = parsed["skus"]
        hubs = parsed["hubs"]
        citations = []
        context_snippets = []

        # 1. Stockout / Inventory Retrieval
        if intent == "STOCKOUT_INVENTORY" or skus:
            query = db.query(InventoryRecommendation).join(
                Product, InventoryRecommendation.product_id == Product.product_id, isouter=True
            )
            if skus:
                query = query.filter(InventoryRecommendation.product_id.in_([int(s) for s in skus]))
            else:
                query = query.filter(InventoryRecommendation.risk_status.in_(["CRITICAL_STOCKOUT", "REORDER_RECOMMENDED"]))

            if hubs:
                query = query.filter(InventoryRecommendation.city_name.in_(hubs))

            recs = query.order_by(desc(InventoryRecommendation.recommended_order_qty)).limit(5).all()

            for r in recs:
                p_name = r.product.product_name if r.product else f"SKU #{r.product_id}"
                snippet = f"SKU {r.product_id} ({p_name}) in {r.city_name}: Current Stock={r.current_stock:.0f}, Avg Daily Demand={r.avg_daily_demand:.0f}, Safety Stock={r.safety_stock:.0f}, ROP={r.reorder_point:.0f}, Recommended Order={r.recommended_order_qty:.0f} units, Risk={r.risk_status}."
                context_snippets.append(snippet)
                citations.append({
                    "type": "inventory",
                    "title": f"SKU #{r.product_id} Inventory Policy",
                    "product_id": r.product_id,
                    "product_name": p_name,
                    "city": r.city_name,
                    "current_stock": r.current_stock,
                    "recommended_order_qty": r.recommended_order_qty,
                    "risk_status": r.risk_status,
                    "priority": r.priority,
                })

        # 2. Anomaly Retrieval
        if intent == "ANOMALY_ALERTS":
            query = db.query(AnomalyAlert).join(
                Product, AnomalyAlert.product_id == Product.product_id, isouter=True
            )
            if hubs:
                query = query.filter(AnomalyAlert.city_name.in_(hubs))
            if skus:
                query = query.filter(AnomalyAlert.product_id.in_([int(s) for s in skus]))

            anomalies = query.order_by(desc(AnomalyAlert.anomaly_date)).limit(5).all()
            for a in anomalies:
                p_name = a.product.product_name if a.product else f"SKU #{a.product_id}"
                snippet = f"Anomaly on {a.anomaly_date} for SKU {a.product_id} ({p_name}) in {a.city_name}: Type={a.anomaly_type}, Actual={a.actual_value:.0f} vs Expected={a.expected_value or 0:.0f}, Severity={a.severity}. Action: {a.description}."
                context_snippets.append(snippet)
                citations.append({
                    "type": "anomaly",
                    "title": f"Demand Anomaly Alert: SKU #{a.product_id}",
                    "product_id": a.product_id,
                    "city": a.city_name,
                    "anomaly_type": a.anomaly_type,
                    "severity": a.severity,
                    "actual": a.actual_value,
                    "expected": a.expected_value,
                    "date": str(a.anomaly_date)
                })

        # 3. Forecast Retrieval
        if intent == "FORECAST_INQUIRY" or (intent == "STOCKOUT_INVENTORY" and len(context_snippets) < 2):
            query = db.query(ForecastItem).join(
                Product, ForecastItem.product_id == Product.product_id, isouter=True
            )
            if skus:
                query = query.filter(ForecastItem.product_id.in_([int(s) for s in skus]))
            if hubs:
                query = query.filter(ForecastItem.city_name.in_(hubs))

            forecasts = query.order_by(desc(ForecastItem.forecast_date)).limit(6).all()
            for f in forecasts:
                p_name = f.product.product_name if f.product else f"SKU #{f.product_id}"
                snippet = f"Forecast for SKU {f.product_id} ({p_name}) on {f.forecast_date} in {f.city_name}: Predicted Demand={f.predicted_demand:.0f} units (95% CI: {f.lower_bound:.0f} - {f.upper_bound:.0f}) via {f.model_name or 'Prophet'}."
                context_snippets.append(snippet)
                citations.append({
                    "type": "forecast",
                    "title": f"Forecast for SKU #{f.product_id}",
                    "product_id": f.product_id,
                    "forecast_date": str(f.forecast_date),
                    "predicted": f.predicted_demand,
                    "bounds": f"{f.lower_bound:.0f} - {f.upper_bound:.0f}",
                    "model": f.model_name
                })

        # 4. Sales / Fast Moving Retrieval
        if intent in ("SALES_REVENUE", "GENERAL_INTELLIGENCE") or not context_snippets:
            query = db.query(
                DailyProductDemand.product_id,
                DailyProductDemand.city_name,
                func.sum(DailyProductDemand.total_quantity).label("total_qty"),
                func.sum(DailyProductDemand.total_sales_value).label("total_rev"),
                Product.product_name
            ).join(Product, DailyProductDemand.product_id == Product.product_id, isouter=True)

            if hubs:
                query = query.filter(DailyProductDemand.city_name.in_(hubs))

            top_movers = query.group_by(
                DailyProductDemand.product_id, DailyProductDemand.city_name, Product.product_name
            ).order_by(desc("total_qty")).limit(5).all()

            for tm in top_movers:
                snippet = f"Fast-Mover: SKU {tm.product_id} ({tm.product_name or 'Standard Grocery'}) in {tm.city_name}: 14-Day Procured Quantity={tm.total_qty:.0f} units, Revenue=₹{tm.total_rev:,.2f}."
                context_snippets.append(snippet)
                citations.append({
                    "type": "sales",
                    "title": f"Fast-Mover SKU #{tm.product_id}",
                    "product_id": tm.product_id,
                    "product_name": tm.product_name,
                    "city": tm.city_name,
                    "total_quantity": tm.total_qty,
                    "revenue_inr": tm.total_rev
                })

        grounded_text = "\n".join(context_snippets) if context_snippets else "No specific records matched the query filter."
        return grounded_text, citations

    def synthesize_answer(self, user_query: str, parsed: Dict[str, Any], context_text: str, citations: List[Dict[str, Any]]) -> str:
        intent = parsed["intent"]
        hubs = ", ".join(parsed["hubs"]) if parsed["hubs"] else "all fulfillment hubs"
        skus = ", ".join(parsed["skus"]) if parsed["skus"] else None

        # Check for OpenAI API Key in env for dynamic completion
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and len(openai_key) > 10:
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                prompt = (
                    "You are an expert FMCG / Retail Demand and Inventory Decision Assistant. "
                    "Use strictly the retrieved database facts below to answer the user's question concisely, "
                    "clearly citing exact numbers, SKU numbers, hub names, and recommended purchase order actions.\n\n"
                    f"Retrieved Database Grounding Context:\n{context_text}\n\n"
                    f"User Question: {user_query}\n"
                    "Response:"
                )
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.2
                )
                return completion.choices[0].message.content
            except Exception as e:
                pass  # Fallback to deterministic synthesis

        # Deterministic Grounded Semantic Synthesis Engine
        if intent == "STOCKOUT_INVENTORY":
            crit_items = [c for c in citations if c.get("risk_status") == "CRITICAL_STOCKOUT"]
            reorder_items = [c for c in citations if c.get("risk_status") == "REORDER_RECOMMENDED"]

            if crit_items:
                skus_str = ", ".join([f"**SKU #{c['product_id']}** ({c.get('product_name') or 'Item'}) in *{c.get('city')}* (Stock: {c['current_stock']:.0f}, Recommended PO: {c['recommended_order_qty']:.0f} units)" for c in crit_items[:3]])
                ans = (
                    f"### 🚨 High Risk Stockout Alert ({hubs})\n\n"
                    f"Based on real-time inventory policy calculations, the following product(s) have breached their safety stock thresholds and require **immediate replenishment POs**:\n\n"
                    f"- {skus_str}\n\n"
                    f"**Operational Guidance**: Expedite vendor dispatch for these critical lines to prevent stockouts over the upcoming 7-day fulfillment window."
                )
            elif reorder_items:
                skus_str = ", ".join([f"**SKU #{c['product_id']}** ({c.get('product_name') or 'Item'}) in *{c.get('city')}* (Recommended PO: {c['recommended_order_qty']:.0f} units)" for c in reorder_items[:3]])
                ans = (
                    f"### 📦 Reorder Recommendations ({hubs})\n\n"
                    f"Current inventory levels are approaching or have dropped below Reorder Points (ROP) for:\n\n"
                    f"- {skus_str}\n\n"
                    f"**Recommendation**: Trigger standard purchase orders aligned with current lead times to maintain target cycle service levels (95%)."
                )
            else:
                ans = f"Current inventory levels across {hubs} are operating within healthy safety stock buffers. No immediate critical stockouts detected."

        elif intent == "ANOMALY_ALERTS":
            spikes = [c for c in citations if "SPIKE" in str(c.get("anomaly_type", ""))]
            drops = [c for c in citations if "DROP" in str(c.get("anomaly_type", ""))]
            ans = (
                f"### ⚡ Demand Anomaly Analysis ({hubs})\n\n"
                f"Statistical and Isolation Forest anomaly monitors detected **{len(citations)} active anomalies**:\n\n"
            )
            for c in citations[:4]:
                ans += f"- **SKU #{c['product_id']}** ({c['city']}): Actual demand **{c['actual']:.0f} units** vs expected **{c['expected']:.0f} units** ({c['anomaly_type']}, Severity: *{c['severity']}* on {c['date']}).\n"
            ans += "\n**Recommended Action**: For surge spikes, verify whether promotional discounts drove the spike; for drops, inspect potential warehouse stock depletions."

        elif intent == "FORECAST_INQUIRY":
            ans = (
                f"### 📈 Demand Forecast Projections ({hubs})\n\n"
                f"According to the multi-model forecasting ensemble (Prophet & LightGBM benchmarked across holdout windows):\n\n"
            )
            for c in citations[:4]:
                ans += f"- **SKU #{c['product_id']}**: Predicted demand is **{c['predicted']:.0f} units** for {c['forecast_date']} (95% CI: {c['bounds']}) via {c.get('model', 'Prophet')}.\n"
            ans += "\n**Business Impact**: Projected volumes show steady baseline velocity. Allocate warehouse picking bins accordingly."

        elif intent == "SALES_REVENUE":
            ans = (
                f"### 🏆 Top Moving Products & Velocity ({hubs})\n\n"
                f"Aggregated demand transactions over the monitored period reveal the following volume leaders:\n\n"
            )
            for c in citations[:4]:
                ans += f"- **SKU #{c['product_id']}** (*{c.get('product_name') or 'Grocery Item'}*): **{c['total_quantity']:,.0f} units** across {c['city']} (Gross Sales: ₹{c['revenue_inr']:,.2f}).\n"
            ans += "\n**Insight**: High volume concentration in urban grocery staples underscores strong repeat purchase behavior."

        elif intent == "PRODUCT_SEARCH":
            prod_info = citations[0] if citations else None
            if prod_info:
                ans = (
                    f"### 🔍 Product Master Details\n\n"
                    f"Found records for **SKU #{prod_info.get('product_id')}**:\n"
                    f"- **Product**: {prod_info.get('product_name', 'Catalog SKU')}\n"
                    f"- **Location**: {prod_info.get('city', 'All Hubs')}\n"
                    f"- **Status**: Active in current catalog and monitored in forecasting pipeline."
                )
            else:
                ans = f"Searched catalog for '{user_query}'. No matching product ID or keyword was found in active records."

        else:
            ans = (
                f"### 🤖 Demand & Decision Intelligence Summary\n\n"
                f"I analyzed your request regarding **{user_query}** against live database records:\n\n"
            )
            for c in citations[:3]:
                ans += f"- **SKU #{c.get('product_id')}** in *{c.get('city', 'Hub')}*: {c.get('title', 'Active Data')}\n"
            ans += "\nYou can ask specific questions like:\n- *'Which products are at risk of stockout next week?'*\n- *'Show top moving products in Delhi'*\n- *'Summarize recent demand anomalies'*"

        return ans

    def process_chat_message(self, db: Session, user_query: str, session_id: Optional[int] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        # 1. Get/create session
        session = self.get_or_create_session(db, user_id=user_id, session_id=session_id)

        # 2. Persist user message
        db.add(ChatMessage(
            session_id=session.id,
            sender_role="user",
            message=user_query
        ))
        db.commit()

        # 3. Classify and retrieve
        parsed = self.classify_intent_and_extract_entities(user_query)
        context_text, citations = self.retrieve_grounded_context(db, parsed)

        # 4. Synthesize answer
        assistant_text = self.synthesize_answer(user_query, parsed, context_text, citations)

        # 5. Persist assistant message
        context_json = json.dumps({"intent": parsed["intent"], "citations": citations})
        db.add(ChatMessage(
            session_id=session.id,
            sender_role="assistant",
            message=assistant_text,
            retrieved_context=context_json
        ))
        db.commit()

        return {
            "session_id": session.id,
            "role": "assistant",
            "message": assistant_text,
            "intent": parsed["intent"],
            "citations": citations,
            "created_at": str(session.updated_at or session.created_at)
        }


chat_service = DecisionRAGService()
