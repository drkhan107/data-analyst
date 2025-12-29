import os
import uuid
from langchain.agents import create_agent
 # Using OpenAI Tools agent
from langchain_core.prompts import PromptTemplate
from python_interpreter.PythonCodeTool import PythonCodeInterpreter
from langchain_core.tools import Tool
from pydantic import BaseModel, Field

from config import SOURCE_PATH

class ResponseStructure(BaseModel):
    """Response Structure."""
    response: str = Field(description="The final response for the query")
    files: list = Field(description="list of all files generated during the execution")
    run_id: str = Field(description="Run id for this execution. This will be returned by the code executor tool")

TEMPLATE= '''

    You are a powerful data analysis assistant.
    You have access to a sandboxed Python execution environment via the 'sandboxed_python_repl' tool.
    All input files needed for analysis are available at "/app/data/input_files/" directory.
    An new file you create or generate should be stored at the "{output_path}" directory.
    When asked to analyze or manipulate the DataFrame, or to generate plots, you MUST use the 'sandboxed_python_repl' tool.
    Construct the Python code needed to answer the user's request and pass it to the tool.
    To do data analysis and crunching, run code but do not generate plots, return chart and graph data instead.
    The output should be text response along with tables and data for plots.
    If the ask or need is to generate charts, do not generate charts, but provide chart data instead and be creative in choosing chart type.
    Always use the provided tool.

    # You are also given a plan pepared by an expert to help you in your analysis.
    # Plan:  {plan}

    Provide detailed answers to the following questions as best you can. You have access to the following tools:

    {tools}

    Final Answer Format:  

    {{
        "response": "This analysis presents trends across categories and groups.",
        "attachments": ["path/to/attachment1.png", "path/to/attachment2.docx"],
        "charts": [
            {{
            "title": "Example Chart 1",
            "type": "bar",
            "description": "Brief description and insights from the chart",
            "data": [
                {{ "Type": "A", "Score": 0.6 }},
                {{ "Type": "B", "Score": 0.3 }}
            ]
            }},
            {{
            "title": "Trend Over Time",
            "type": "line",
            "description": "Brief description aand insights from the chart",
            "data": [
                {{ "Month": "Jan", "Metric": 100 }},
                {{ "Month": "Feb", "Metric": 120 }},
                {{ "Month": "Mar", "Metric": 90 }}
            ]
            }},
            {{
            "title": "Proportion by Group",
            "type": "pie",
            "description": "Brief description and insights from the chart",
            "data": [
                {{ "Group": "Group A", "Proportion": 0.5 }},
                {{ "Group": "Group B", "Proportion": 0.3 }},
                {{ "Group": "Group C", "Proportion": 0.2 }}
            ]
            }},
            {{
            "title": "Correlation Between Features",
            "type": "scatter",
            "description": "Brief description and insights from the chart",
            "data": [
                {{ "Feature X": 10, "Feature Y": 20 }},
                {{ "Feature X": 15, "Feature Y": 30 }},
                {{ "Feature X": 20, "Feature Y": 35 }}
            ]
            }}
        ]
    }}


    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    Thought:{agent_scratchpad}'''


prompt1=f""" 

    You are a powerful data analysis assistant.
    You have access to a sandboxed Python execution environment via the 'sandboxed_python_repl' tool.
    All input files needed for analysis are available at "/data/" directory.
    An new file you create or generate should be stored at the "/tmp" directory.
    When asked to analyze or manipulate the DataFrame, or to generate plots, you MUST use the 'sandboxed_python_repl' tool.
    Construct the Python code needed to answer the user's request and pass it to the tool.

    Use only these libaries as you cannot install anything else:
    - pandas
    - numpy
    - matplotlib
    - seaborn
    - openpyxl

    Strictly follow the following output json format:
    Output example:

    {{
        "Final Answer": "Your final answer to the original input question",
        "generated_files: ["file1", "file2"],
        "run id": "run_id returned by the code executor tool"
    }}
    
"""

prompt = """
        You are working with a pandas dataframe in Python. All input files you need are under path '/data'
        You are an experiencied data scientist
        Lets think step by step of why the next action has sense and if there is something to take in account
        
        At the first steps:
            1. Import libraries that you are going to use for data as pandas, numpy and seaborn
            2. Check which file you need and read it from the path /data. 
            3. Do any preprocessing if neded. 
            4. Drop duplicate rows
            
        For intermediate steps during all iterations, use de following procedure:
            (1) First identify the possible solutions and possible blocks of the thought
            (2) If theres is Empty DataFrame, review your previous observation and see if you fail and where
            (3) If you are making new columns or operations, make sure the values you are going to use exists before using it
            
        Then check the following advices:
            1. Find the corresponding metrics, not necessarily the names is exactly equal as the human requested
            2. Check if is necessary to change format of table with pivot, groupby, melt, or other function over the table. When making this changes
            make sure the table is well processed
            3. When generating a new dataset return it to be observed, if necessary, print it
            
        For plots take the following instructions in consideration:
            1. If you are plotting graphs, save the corresponding images in the following path: /tmp
            2. Prefer using seaborn library.


        Answer the following questions as best you can. You have access to the following tools:
        {tools}

        Use the following format:

        Question: the input question you must answer
        you should always think about what to do in as possible paths
        Thought1: thinks this as the first possibility path
        Thought2: thinks this as the second possibility path
        Thought: which is the best thougth to take action
        Action: code_interpreter
        Action Input: the input to the action
        Observation: the result of the action
        Remember to maintain the format specifically think about Thougth1 and Thought2
        ... (this Thought1/Thought2/Action/Action Input/Observation can repeat N times)
        Final Thought: I now know the final answer and processed the data correctly.

        Final Answer: the final answer to the original input question. 

        Begin!

        Previous conversation history:
        {history}

        Question: {input}
        {agent_scratchpad}
        """
from langchain.agents.structured_output import ProviderStrategy

class DataAnalysisAgent:
    def __init__(self, llm, p_info):
        self.llm = llm
        self.info=p_info

        self.info['session_id']=p_info['session_id'] or None
        self.conversation=[]

        # self.prompt = PromptTemplate.from_template(TEMPLATE, partial_variables={"output_path": "output_path"})
        # Create the agent
        sandboxed_tool = PythonCodeInterpreter(self.info, docker=True)
        #self.tools = [sandboxed_tool]
        # print("***********",sandboxed_tool.payload)
        self.tools=[Tool(
            name="code_interpreter",
            description="A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the output of a value, you should print it out with `print(...)`.",
            func=sandboxed_tool.run,
        )]

        self.agent=create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=prompt,
            response_format=ProviderStrategy(ResponseStructure),
            debug=True
        )

        
    def run(self, query, plan=""):
        
        source_mount_path=f"{SOURCE_PATH}/{self.info['project_id']}"
        
        # session_id = "run-"+str(uuid.uuid4()) # Unique ID for this execution run
        output_path=f"/app/data/output_files/{self.info['session_id']}" #f"{source_mount_path}/output_files/{session_id}"
        os.makedirs(f"{source_mount_path}/output_files/{self.info['session_id']}", exist_ok=True) #os.makedirs(source_mount_path, exist_ok=True)
        #os.makedirs(output_path, exist_ok=True)

        print("output path", output_path)

        self.info['source_path']=source_mount_path
        # self.info["session_id"]=session_id

        
        messages = self.conversation[::-6] + [{"role": "user", "content": query}]
    
        # --- Example Queries ---
        print("--- Query 1: DataFrame Info ---")
        response = self.agent.invoke({"messages": messages},)
        #print(f"Agent Response:\n{response1['output']}\n")
        self.conversation.append({"role": "user", "content": query})
        self.conversation.append({"role": "assistant", "content": response['messages'][-1].content[0]['text']})
        
        return response