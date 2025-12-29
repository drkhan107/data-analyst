import os
import sys
import json
import re
from io import StringIO
from code_execution import PythonExecutor

# --- 1. Avoid heavy imports at top-level ---
# Only import light, standard libraries here

def main():
    # --- 2. Faster Config Loading (Direct Env Access) ---
    print("Executing Code!")
    
    code = os.environ.get("CODE", "")
    df_csv = os.environ.get("DF_CSV")
    session_id = os.environ.get("SESSION_ID", "default")
    
    # Pre-setup output path (Using /tmp for speed if possible)
    local_output_dir = "/tmp"
    
    os.makedirs(local_output_dir, exist_ok=True)
    
    # --- 3. Lazy Import Strategy ---
    # We only import these when main() starts to save container init time
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    # from langchain_experimental.utilities import PythonREPL

    local_namespace = {
        "pd": pd, "plt": plt, "np": np, "os": os
    }

    if df_csv:
        try:
            local_namespace['df'] = pd.read_csv(StringIO(df_csv))
        except Exception as e:
            print(json.dumps({"error": f"CSV Load Error: {str(e)}", "session_id": session_id}))
            return

    # --- 4. Streamlined Execution ---
    # Use standard list/dict instead of Pydantic models for the internal logic
    old_stdout, old_stderr = sys.stdout, sys.stderr
    redirected_stdout, redirected_stderr = StringIO(), StringIO()
    sys.stdout, sys.stderr = redirected_stdout, redirected_stderr
    
    error_message = None
    try:
        # Pass the pre-imported libs directly into the REPL
        repl = PythonExecutor(_globals=local_namespace)
        res = repl.run(code)

        exception_names = [
                "Exception",
                "SyntaxError",
                "IndentationError",
                "NameError",
                "TypeError",
                "ValueError",
                "ZeroDivisionError",
                "ModuleNotFoundError",
                "AttributeError",
                "KeyError",
                "IndexError",
                "FileNotFoundError",
                "Ruksa Hey",
            ]

        # Create a regex pattern to find either a traceback or a known exception at the start of a line.
        # The `re.MULTILINE` flag allows `^` to match the start of each line.
        error_pattern = re.compile(
            r"Traceback \(most recent call last\)|^\s*\b(" + "|".join(exception_names) + r")\b",
            re.MULTILINE
        )

            # Search for the pattern in the result string
        error_match = error_pattern.search(res)

            
        error= None

        if error_match or re.search(r"Traceback|Error:", res):
            print(f"Error Detected: {res}")  # The result is an error message
            error_message=f"Error Detected: {res}"
        
        else:
            print(res)

    except Exception as e:
        print("Error:", str(e)) 
        import traceback
        error_message = traceback.format_exc()
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr

    # --- 5. Efficient File Gathering ---
    generated_files = [
        os.path.join(local_output_dir, f) 
        for f in os.listdir(local_output_dir) 
        if os.path.isfile(os.path.join(local_output_dir, f))
    ]
    
    # Final JSON Output
    print(json.dumps({
        "stdout": redirected_stdout.getvalue(),
        "stderr": redirected_stderr.getvalue(),
        "generated_files": generated_files,
        "session_id": session_id,
        "error": error_message
    }))

if __name__ == "__main__":
    main()