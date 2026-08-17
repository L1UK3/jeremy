import sys
from pathlib import Path

# Add src/agent directory to sys.path so internal flat imports work seamlessly
agent_dir = Path(__file__).resolve().parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent import agent

__all__ = ["agent"]
