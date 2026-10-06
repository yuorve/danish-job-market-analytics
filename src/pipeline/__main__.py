"""
CLI entry point for running the pipeline: `python -m src.pipeline`
"""

import json
from src.pipeline.orchestrator import PipelineOrchestrator

def main():
    orchestrator = PipelineOrchestrator()
    results = orchestrator.run()
    print("\n--- Pipeline Execution Summary ---")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
