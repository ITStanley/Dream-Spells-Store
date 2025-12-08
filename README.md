🧿 Dream Spells E-commerce AI Chatbot (Mini Project)

This project implements an AI-powered customer support agent named Aura for a fictional e-commerce store, Dream Spells. The system is built using Streamlit for the frontend and integrates the Google Gemini API to handle contextual queries and execute actions based on natural language input.

This project addresses Scenario 03: Customer Support Chatbot for an E-commerce Platform of the Mini Project requirement.

✨ Features

The application provides a full e-commerce simulation with core AI functionality:

    * Contextual Chatbot (Aura): An AI assistant that is aware of the product catalog, user's current shopping cart, and past order history.
    * AI Agent Action: The AI can receive a natural language buying request (e.g., "I want 2 of those") and translate it into a structured JSON command (`{"action": "add_to_cart", ...}`) which is then executed by the Python backend to update the user's cart automatically.
    * Product Catalog: Displays products loaded from `products.json`, categorized and filterable.
    * Order History: Tracks previous orders, prices, dates, and status (Processing, Shipped, Delivered) loaded from `purchase_history.json`.
    * Data Visualization: Includes a dedicated "Stats" tab showing total spending and spending trends using Pandas.

💻 Installation and Setup

    1. Prerequisites

        * Python 3.8+
        * The project files (`app.py`, `products.json`, `purchase_history.json`, `requirements.txt`).
        * Crucial: Placeholder folders for images are required: `images/products/` and `images/logo/`.

    2. Set Up Environment

        1.  Clone the Repository (or create the project folder):
            ```bash
            git clone [your_repo_link]
            cd dream_spells_store
            ```

        2.  Create and Activate a Virtual Environment (Recommended):

            * Windows:
                ```bash
                python -m venv .venv
                .\.venv\Scripts\activate
                ```
            * macOS/Linux:
                ```bash
                python3 -m venv .venv
                source .venv/bin/activate
                ```

        3.  Install Dependencies:
            All required libraries are listed in `requirements.txt`.
            ```bash
            pip install -r requirements.txt
            ```

    3. API Key Configuration

        The application requires a Gemini API Key to run the AI features.

            1.  Get your API Key from Google AI Studio.
            2.  Open `app.py` and replace the placeholder key in the following line:

                ```python
                GEMINI_API_KEY = "AIzaSyD1JUcqPm6JNYde2zO4Ljx0JfFwzt1RSfQ"  # <--- PASTE KEY HERE
                ```

🚀 Running the Application

With the environment activated and the API key configured, run the application using Streamlit:

```bash
streamlit run app.py
