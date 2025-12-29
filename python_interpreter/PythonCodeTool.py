
import docker
import requests
import time
import uuid
import os
import logging # Import the logging module
from dotenv import load_dotenv

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field # For defining tool input schema

from config import MOUNT_PATH
from .run import run_code_in_docker
# Configs
IMAGE_NAME = "secure-python-sandbox"



def setup_logger(path,session_id):
    logfile_path=os.path.join(path,f"output_files/{session_id}/logs")
    os.makedirs(logfile_path, exist_ok=True)
    log_file = os.path.join(logfile_path, f"{session_id}.log")
    logger = logging.getLogger(session_id)
    logger.setLevel(logging.INFO)

    # Create file handler which logs even debug messages
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add the handlers to the logger
    # Ensure handlers are not duplicated if setup_logger is called multiple times for the same session_id
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger
# --- End Logging Configuration ---


class PythonCodeInterpreter():
    name: str = "sandboxed_python_repl"
    description: str = (
        "Executes Python code in a sandboxed environment. "
        "Use this for data analysis, manipulation, and generating data based on the DataFrame. "
        "The tool will return standard output, standard error, and paths to any generated files."
    )
    payload:dict={"user_id": "adam", "project_id": "peace","session_id": "run-001","storage":"local"}
    logger:logging

    def __init__(self, payload, docker=False):
        super().__init__()
        self.payload = payload
        self.payload.setdefault('user_id', 'adam')
        self.payload.setdefault('project_id', 'peace')
        self.payload.setdefault('storage', 'local')
        self.payload.setdefault('session_id', "run-"+str(uuid.uuid4()))
        self.payload.setdefault('source_path', "/home/asif-iqbal-khan/data/proj-001")
        
        self.payload['docker_image']=IMAGE_NAME
        self.use_docker=docker
        self.payload['session_id']=f"run-{str(uuid.uuid4())}"
        self.logger = setup_logger(self.payload["source_path"], self.payload['session_id']) # Initialize logger for the instance


    def run(self, code: str) -> str:
        """Execute Python code in the sandbox."""
        self.logger.info(f"Attempting to run code for session: {self.payload['session_id']}")
        self.logger.debug(f"Code to execute: {code}")

        run_id=self.payload['session_id'] #f"run-{str(uuid.uuid4())}"
        output_path=f"{self.payload['source_path']}/output_files/{run_id}"
        os.makedirs(output_path, exist_ok=True) # Ensure output directory exists
        self.logger.info(f"Output files will be stored in: {output_path}")

        self.payload['output_path']=output_path
        self.payload['run_id']=run_id
        self.payload['code']=code

        # print(self.payload)
        if self.use_docker:
            result= run_code_in_docker(self.payload)   
        else:
            result= self.run_code()
        

        if isinstance(result, str):
            self.logger.error(f"send_code_execution returned an error: {result}")
            return result
        result_json=result
        # try:
        #     result_json = result.json()
        # except requests.exceptions.JSONDecodeError as e:
        #     self.logger.error(f"Failed to decode JSON response: {e}. Response text: {result.text}")
        #     return f"Error: Could not decode response from sandbox. {e}"

        stdout = result_json.get("stdout", "")
        stderr = result_json.get("stderr", "")
        generated_files_container_paths = result_json.get("generated_files", [])
        
        

        files=[]
        # Corrected logic to check for generated files on the host
        for filename in os.listdir(output_path):
            file_path = os.path.join(output_path, filename)
            if os.path.isfile(file_path):
                files.append(file_path)
        self.logger.info(f"Files generated on host: {files}")

        file_messages = []
        if generated_files_container_paths:
            file_messages.append("Generated files:")
            for container_path in generated_files_container_paths:
                if container_path.startswith("/tmp"):
                    relative_path = container_path[len("/tmp/"):].lstrip('/')
                    host_file_path = os.path.join(output_path, relative_path) # Changed to use output_path
                    file_messages.append(f"- Accessible at: {host_file_path}")
                    self.logger.info(f"Generated file found: {host_file_path}")
                else:
                    file_messages.append(f"- Generated (path unknown on host): {container_path}")
                    self.logger.warning(f"Unexpected container path for generated file: {container_path}")

        final_output_parts = []
        if stdout:
            final_output_parts.append(f"Stdout:\n```\n{stdout.strip()}\n```")
            self.logger.info(f"Stdout received: {stdout.strip()}")
        if stderr:
            final_output_parts.append(f"Stderr:\n```\n{stderr.strip()}\n```")
            self.logger.warning(f"Stderr received: {stderr.strip()}")
        if file_messages:
            final_output_parts.append("\n".join(file_messages))

        if not final_output_parts:
            self.logger.info("Code executed. No output, standard error, or generated files.")
            return "Code executed. No output or standard error. No files generated."
        final_output_parts.append("\nRun ID: "+run_id)
        return "\n\n".join(final_output_parts)