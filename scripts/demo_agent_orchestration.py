"""
Demo script to verify the Agentic Orchestration Layer.
"""
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')

def main():
    print("Initializing Agent Orchestrator...")
    orchestrator = AgentOrchestrator(model="qwen2:1.5b")
    
    user_query = "Can you diagnose why the checkout service is throwing errors?"
    print(f"\nUser Query: {user_query}")
    print("-" * 50)
    
    response = orchestrator.run(user_query)
    
    print("-" * 50)
    print("\nFinal Response:")
    print(response)

if __name__ == "__main__":
    main()
