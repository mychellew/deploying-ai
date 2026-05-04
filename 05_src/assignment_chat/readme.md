# Travel Buddy: Agentic Canadian Travel Assistant

## Project Overview
Travel Buddy is an AI-powered conversational agent built to assist users with Canadian travel logistics. The system uses a Router-Service architecture to provide real-time weather updates, curated travel information via semantic search (RAG), and customized day-by-day itineraries. 

The agent maintains a consistent "Friendly Canadian" persona, ensuring all technical data is transformed into engaging, helpful dialogue.

## Features and Services

### 1. Real-time Weather Service (REST API)
* **Back-end:** Integrates with the Open-Meteo API.
* **Transformation:** Instead of returning raw JSON, the service passes data through a personality layer. A secondary LLM call rephrases the coordinates and temperatures into a warm, conversational response to ensure the output is never provided verbatim.

### 2. Semantic Travel Guide (RAG)
* **Vector Database:** Uses ChromaDB with file persistence.
* **Embedding Process:** Documents were processed using OpenAI's `text-embedding-3-small` model. Text was split using a `RecursiveCharacterTextSplitter` with a chunk size of 300 and an overlap of 50 to maintain contextual continuity.
* **Hybrid Knowledge:** The RAG prompt is engineered to use internal LLM knowledge for historical climate data or deep history if the local `travel_guides.txt` does not contain the specific answer.

### 3. Orchestration and Function Calling
* **The Router:** A central LLM acts as the system's brain. It analyzes user intent and returns a structured JSON object to decide which service (Weather, RAG, or Planner) to invoke.
* **Itinerary Planning:** A specialized service handles complex multi-day scheduling requests, ensuring responses adhere to the system's personality and topic restrictions.

## Security and Guardrails
* **Topic Restrictions:** Hard-coded filters and system instructions prevent the model from discussing restricted topics, specifically: cats, dogs, horoscopes, zodiac signs, and Taylor Swift.
* **Prompt Protection:** Includes logic to block attempts to reveal or modify system instructions or internal configurations.
* **Context Management:** The system maintains conversation state through Gradio’s history mechanism, passing the previous bot message back into the router to resolve ambiguous follow-up questions.

## Implementation Decisions
* **Keyword Fallback:** To ensure reliability, the function calling router includes a Python-based fallback logic. If the LLM fails to return valid JSON, the system uses keyword matching to ensure the user still receives an answer.
* **Historical Weather Handling:** Since the Weather API is strictly for current conditions, I have configured the system to lean on the RAG and internal knowledge base for queries regarding typical or historical weather patterns.
* **Environment Configuration:** The project uses a `.secrets` file and `dotenv` to manage API keys and gateway headers securely across different modules.

## Setup
1. Ensure the `.secrets` file contains a valid `API_GATEWAY_KEY`.
2. The vector database is pre-persisted in the `chroma_db` folder to avoid the need for re-indexing during assessment.
3. Run the application from the main project file to launch the Gradio interface.