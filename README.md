# Databricks Genie Chatbot

A Streamlit chatbot that uses Semantic Kernel with GPT-4 to interact with Databricks Genie APIs. Ask natural language questions about your Databricks environment, Unity Catalog, tables, schemas, and data.

## Setup

### 1. Install Dependencies

```bash
pipenv install
pipenv shell
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Databricks Configuration
DATABRICKS_TOKEN=your_databricks_personal_access_token
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
GENIE_SPACE_ID=your_genie_space_id

# Optional: Enable debug mode
DEBUG_MODE=false
```

**Required Variables:**
- `OPENAI_API_KEY` - Your OpenAI API key for GPT-4 access
- `DATABRICKS_TOKEN` - Databricks personal access token (PAT)
- `DATABRICKS_HOST` - Your Databricks workspace URL
- `GENIE_SPACE_ID` - The ID of your Databricks Genie space

### 3. Run the App

```bash
streamlit run app.py
```

The chatbot will open at `http://localhost:8501`

## How It Works

1. User asks a question in natural language
2. GPT-4 determines if it needs Databricks information
3. If yes, the question is passed directly to Genie APIs
4. Genie processes the question, generates SQL, and retrieves data
5. GPT-4 formats and presents the results to the user

## Example Questions

- "What tables are in my catalog?"
- "Show me the schema of table X"
- "What are the recent jobs that ran?"
- "Query the latest data from table Y"

