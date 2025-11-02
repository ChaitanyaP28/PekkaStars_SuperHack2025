"""
AiAgent: Triggered by Orchestrator on Critical Failure.
Creates backup of service code, sends code and logs to LLM
Generates a fix.
Runs fix in sandbox and determines if fix is correct.
Updates knowledge base with both backup and fixed code
"""

import os
import re
import json
from google import genai
from dotenv import load_dotenv
from datetime import datetime

# ============================================================
#  Load environment variables
# ============================================================
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Resolve paths relative to this script so all files can live in the same directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KB_PATH = os.path.join(SCRIPT_DIR, os.getenv("KB_PATH", "knowledge_base.json"))
LOG_FILE = os.path.join(SCRIPT_DIR, os.getenv("LOG_FILE", "log.txt"))

# ============================================================
#  Initialize Gemini client
# ============================================================
if not API_KEY:
    print("GEMINI_API_KEY not set. Please set the GEMINI_API_KEY environment variable.")
    # Do not exit here to allow parts of the script that don't need the client to run in tests.

client = None
try:
    client = genai.Client(api_key=API_KEY) if API_KEY else None
except Exception as e:
    print(f"Failed to initialize Gemini client: {e}")

# ============================================================
#  Knowledge Base Helpers
# ============================================================
def init_kb():
    """Ensure knowledge base file exists and is valid JSON."""
    if not os.path.exists(KB_PATH):
        with open(KB_PATH, "w") as f:
            json.dump({"entries": []}, f, indent=2)
    else:
        try:
            with open(KB_PATH, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "entries" not in data:
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            # Reset corrupted KB
            with open(KB_PATH, "w") as f:
                json.dump({"entries": []}, f, indent=2)

def add_to_kb(faulty_code, fixed_code):
    """Add an entry to the knowledge base safely."""
    init_kb()
    entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "faulty_code": faulty_code,
        "fixed_code": fixed_code,
        "timestamp": datetime.now().isoformat()
    }

    try:
        with open(KB_PATH, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = {"entries": []}

    data["entries"].append(entry)

    with open(KB_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print("\nAdded to Knowledge Base!\n")

# ============================================================
#  Log Reader
# ============================================================
def read_logs() -> str:
    """Read logs from the log file."""
    log_path = LOG_FILE
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                logs = f.read().strip()
            return logs if logs else "No logs available."
        except Exception as e:
            return f"Error reading logs: {e}"
    return "Log file not found."


def extract_filename_from_logs(logs: str) -> str:
    """Try to extract the most recent application filename from logs.

    Looks for lines like 'Application: 2.py' or occurrences like '[2.py]'.
    Returns the filename (e.g. '2.py') or an empty string if nothing found.
    """
    if not logs:
        return ""

    # Try 'Application: <name>' pattern first
    app_matches = re.findall(r"Application:\s*([\w\-\.]+\.py)", logs)
    if app_matches:
        return app_matches[-1]

    # Fallback: look for bracketed references like '[2.py]'
    bracket_matches = re.findall(r"\[([^\]]+\.py)\]", logs)
    if bracket_matches:
        return bracket_matches[-1]

    return ""

# ============================================================
#  Code Fixer
# ============================================================
def clean_llm_output(text: str) -> str:
    """Remove markdown fences, stray backticks, or labels."""
    # Remove ```python or ``` etc.
    text = re.sub(r"^```(?:python)?", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"```$", "", text, flags=re.MULTILINE)
    text = text.strip().strip("`").strip()
    # Remove language prefix lines like 'python\n'
    if text.lower().startswith("python\n"):
        text = text[7:].strip()
    return text

def fix_code(faulty_code: str, logs: str = "") -> str:
    """Ask Gemini to fix Python code and return clean result."""
    log_context = ""
    if logs:
        log_context = f"\n\nApplication Logs:\n{logs}\n\n"
    
    prompt = (
        "You are a Python expert.\n"
        "Fix syntax or logic errors in the following Python code.\n"
        f"LOG:{log_context}"
        "Return only valid Python code — no markdown, no explanations, no comments.\n\n"
        f"Code:\n{faulty_code}"
        f"Make sure to make the CODE DOESNT CRASH or THROW ANY ERROR, even if there is an error and handle it carefully as put it as info and NOT as an ERROR"
    )

    if client is None:
        print("Gemini client not available; returning original faulty code.")
        return faulty_code

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return faulty_code

    # Extract LLM text safely
    text = getattr(response, "text", "") or ""
    text = text.strip()
    if not text:
        try:
            text = response.output[0].content[0].text.strip()
        except Exception:
            text = ""

    cleaned = clean_llm_output(text)
    return cleaned

# ============================================================
#  Run Code Safely
# ============================================================
def run_code(code: str):
    """Safely execute Python code."""
    print("\n--- Running Fixed Code ---")
    try:
        # Use a restricted globals dict but allow builtins
        safe_globals = {"__builtins__": __builtins__}
        exec(code, safe_globals, {})
    except Exception as e:
        print(f"Error while running fixed code: {e}")

# ============================================================
#  Main Execution
# ============================================================
if __name__ == "__main__":
    # Read logs first to determine which application/file caused the error
    logs = read_logs()
    print("\n=== Reading Application Logs ===")
    print(logs[:500] + "..." if len(logs) > 500 else logs)

    detected = extract_filename_from_logs(logs)

    # All files are expected to be in the same directory as this script
    script_dir = SCRIPT_DIR
    local_fallback = os.path.join(script_dir, "faulty.py")

    faulty_path = local_fallback

    if detected:
        candidate = os.path.join(script_dir, detected)
        if os.path.exists(candidate):
            faulty_path = candidate
        else:
            print(f"Detected filename '{detected}' in logs but file not found at {candidate}. Falling back to {local_fallback}.")
    else:
        print("Could not detect application filename from logs; using fallback 'faulty.py'.")

    if not os.path.exists(faulty_path):
        print(f"Faulty file not found at '{faulty_path}'. Please create it first.")
        exit(1)

    with open(faulty_path, "r", encoding="utf-8") as f:
        faulty_code = f.read().strip()

    print(f"=== Faulty Code Read from {faulty_path} ===")
    print(faulty_code)
    print("\n=== Sending to Gemini for Fix ===\n")

    fixed_code = fix_code(faulty_code, logs)

    print("--- Fixed Code ---")
    print(fixed_code or "Gemini returned empty response")

    run_code(fixed_code)
    add_to_kb(faulty_code, fixed_code)

    fixed_output_path = os.path.join(script_dir, "fixed_output.py")
    try:
        with open(fixed_output_path, "w", encoding="utf-8") as f:
            f.write(fixed_code)
        print(f"Fixed code saved to {fixed_output_path}\n")
    except Exception as e:
        print(f"Could not save fixed output: {e}")
