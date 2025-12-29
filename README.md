

# Data Analyst AI Agent

An **AI-powered data analysis agent** that uses a Large Language Model (LLM) and a **sandboxed Python code interpreter** to perform dynamic data analysis tasks. The agent maintains conversational context, executes Python code securely (via Docker), and produces structured analytical responses.

---

## ✨ Key Capabilities

* 🧠 LLM-driven reasoning for data analysis
* 🐍 Secure Python code execution using a sandboxed interpreter
* 💬 Conversation memory across queries
* 📁 Automatic session-based output management
* 🔌 Tool-based agent architecture
* 🧩 Easily extensible for new tools and workflows
* 💬 Supports Visualizations through matplotlib and seaborne graphs and charts.

---

## 🧱 Architecture Overview

The core component is the `DataAnalysisAgent` class, which:

1. Accepts an LLM and project/session metadata
2. Creates a sandboxed Python execution tool
3. Registers the tool with an AI agent
4. Maintains conversation history
5. Executes user queries and returns structured responses

---

## 📁 Project Structure

```
data-analyst/
├── analysis_agent.py       # DataAnalysisAgent implementation
├── config.py               # Paths, constants, and configuration
├── utils.py                # Helper utilities
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project metadata
├── LICENSE
└── README.md
```

---

## 🧠 Core Class: `DataAnalysisAgent`

### Initialization

* Build docker image "secure-python-sandbox" (one-time)

```python
DataAnalysisAgent(llm, project_info)
```

**Parameters**

* `llm` – Large Language Model instance (Currently supports Gemini -  provide GOOGLE_API_KEY in .env file)
* `project_info` – Dictionary containing:

  * `project_id`
  * `session_id`
  * other project metadata


### What Happens Internally

* Initializes conversation memory
* Sets up a **Docker-based PythonCodeInterpreter**
* Registers the interpreter as a tool named `code_interpreter`
* Creates an AI agent with:

  * system prompt
  * tool support
  * structured response formatting
  * debug mode enabled

---

## 🛠️ Tooling

### Python Code Interpreter Tool

The agent is equipped with a tool defined as:

* **Name:** `code_interpreter`
* **Purpose:** Execute Python code safely
* **Execution:** Docker sandbox
* **Usage:** Automatically invoked by the agent when code execution is required

```text
"A Python shell. Use this to execute python commands. Input should be a valid python command."
```

---

## ▶️ Running a Query

### Method

```python
run(query)
```

### What It Does

1. Creates a session-based output directory
2. Updates source and output paths
3. Combines recent conversation context with the new query
4. Invokes the agent
5. Stores both user query and assistant response
6. Returns the full agent response object

---

## 📂 Output Management

* Outputs are stored per session:
* Set SOURCE_PATH in config.py

```
/{SOURCE_PATH}/{project_id}/output_files/{session_id}/
```

* Ensures isolation between runs
* Supports reproducibility and auditing

---

## 💬 Conversation Memory

* Maintains a rolling conversation history
* Uses the **most recent messages** to preserve context
* Enables multi-step analytical reasoning

---

## 🔍 Example Usage

```python
agent = DataAnalysisAgent(llm=llm, project_info={'project_id':'proj-001', 'session_id':'s1'})

response = agent.run(
    query="Load the dataset and show summary statistics"
)

print(response)
```

---

## 🔒 Security

* Python execution is sandboxed using Docker
* Prevents unsafe system access
* Isolated file system per session

---

## 📦 Dependencies

Install dependencies using:

```bash
pip install -r requirements.txt
```

(Exact dependencies are listed in `requirements.txt`.)

---

## 📄 License

This project is licensed under the **MIT License**.
See the `LICENSE` file for more details.

