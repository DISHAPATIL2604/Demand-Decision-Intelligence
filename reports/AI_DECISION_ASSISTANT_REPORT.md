# Stage 8 — AI Decision Assistant Report

## Objective
Build an AI Decision Assistant that answers natural-language questions using project data (sales, forecasts, anomalies, and inventory decisions) from Stage 7.

## Architecture
- **Backend Service**: `chat_assistant.py` added to handle query routing, data retrieval, and LLM communication.
- **Backend API**: `chat.py` added to expose `/api/chat/message` and `/api/chat/suggestions` endpoints.
- **Frontend**: A new `AssistantPage.jsx` integrated into the existing router, replacing the `/assistant` placeholder.

## Data Sources Used
- `reports/inventory_decision_sample.csv` (for stockout risk queries)
- `reports/demand_anomalies.csv` (for anomaly queries)
- Database table `daily_product_demand` via SQLAlchemy (for demand queries)

## Query Routing/Retrieval Logic
- Regex-based intent classification mapped to "inventory", "anomaly", "forecast", or "demand".
- Retrieves relevant records via `pandas` (for CSVs) and SQLAlchemy (for DB). 
- Filters by product ID if detected in the query.

## LLM Integration
- Uses `requests` module to call the Gemini API (`gemini-1.5-flash`), eliminating the need to add external SDK dependencies.
- Sends the retrieved data context alongside a strict system prompt to avoid hallucinations.

## Fallback Mode
- If `GEMINI_API_KEY` is unavailable or the API call fails, the assistant returns a clear structured fallback message containing the raw data and indicating the LLM is unavailable.

## API Endpoints
1. `POST /api/chat/message`: Process user query with history, returning a reply and citations.
2. `GET /api/chat/suggestions`: Return quick start queries.

## Frontend Implementation
- Matched the dark-theme UI and utilized existing CSS variables.
- Utilized Lucide icons for the Assistant bot, User, and UI components.
- Added message history, error states, and a typing indicator.

## Authentication Handling
- `get_current_user` injected directly into the API routes.
- The frontend uses the existing `api.js` Axios wrapper that retrieves the bearer token, ensuring seamless integration with existing auth.

## Example Queries
- "Which products have critical stockout risk in Delhi?"
- "What is the forecasted demand for SKU 19512 next week?"
- "Why did product 391306 trigger an anomaly alert?"

## Testing Performed
1. Tested Python imports and verified syntax fixes.
2. Backend API routes successfully registered.
3. Fallback mode functional (tested logically without injecting an API key).

## Limitations
- Intent routing is regex-based (can be improved with LLM routing).
- Relies on CSV exports for some data (inventory/anomalies) rather than DB reads, as specified by instructions.

## Files Changed/Created
- `backend/services/chat_assistant.py` [NEW]
- `backend/api/chat.py` [NEW]
- `backend/main.py` [MODIFIED]
- `frontend/src/services/api.js` [MODIFIED]
- `frontend/src/pages/assistant/AssistantPage.jsx` [NEW]
- `frontend/src/App.jsx` [MODIFIED]
- `backend/api/analytics.py` [MODIFIED] (fixed existing merge conflict)
- `reports/AI_DECISION_ASSISTANT_REPORT.md` [NEW]
