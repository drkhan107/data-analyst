import functools
import logging
import multiprocessing
import re
# import sys
import contextlib
from io import StringIO
from typing import Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 1. Pre-compile regex patterns at module level to avoid recompilation on every call
_REMOVE_PYTHON_PREFIX = re.compile(r"^(\s|`)*(?i:python)?\s*")
_REMOVE_TRAILING_CHARS = re.compile(r"(\s|`)*$")

@functools.lru_cache(maxsize=1)  # maxsize=1 is sufficient for a parameter-less function
def warn_once() -> None:
    """Warn once about the dangers of PythonREPL."""
    logger.warning("Python REPL can execute arbitrary code. Use with caution.")


class PythonExecutor(BaseModel):
    """Simulates a standalone Python REPL."""

    globals: Optional[Dict] = Field(default_factory=dict, alias="_globals")
    locals: Optional[Dict] = Field(default_factory=dict, alias="_locals")

    @staticmethod
    def sanitize_input(query: str) -> str:
        # Use pre-compiled patterns
        query = _REMOVE_PYTHON_PREFIX.sub("", query)
        query = _REMOVE_TRAILING_CHARS.sub("", query)
        return query

    @classmethod
    def worker(
        cls,
        command: str,
        globals: Optional[Dict],
        locals: Optional[Dict],
        queue: Optional[multiprocessing.Queue] = None,
    ) -> str:
        """
        Executes code and captures stdout. 
        Returns string directly if queue is None, otherwise puts in Queue.
        """
        output = StringIO()
        try:
            cleaned_command = cls.sanitize_input(command)
            # 3. Use contextlib for faster/safer stdout redirection
            with contextlib.redirect_stdout(output):
                exec(cleaned_command, globals, locals)
            result = output.getvalue()
        except Exception as e:
            result = repr(e)
        
        if queue:
            queue.put(result)
            return "" # Return value ignored in async process
        return result

    def run(self, command: str, timeout: Optional[int] = None) -> str:
        # warn_once()

        # 2. Optimization: Avoid multiprocessing overhead if timeout is not required
        if timeout is None:
            # Run directly in the main process
            # No pickling, no process spawn time, no Queue IPC overhead
            return self.worker(command, self.globals, self.locals)

        # Timeout path: Must use multiprocessing
        queue: multiprocessing.Queue = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=self.worker, 
            args=(command, self.globals, self.locals, queue)
        )
        p.start()
        p.join(timeout)

        if p.is_alive():
            p.terminate()
            p.join() # Ensure resources are cleaned up
            return "Execution timed out"
        
        return queue.get()