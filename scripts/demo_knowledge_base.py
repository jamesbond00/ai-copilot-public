from src.knowledge.knowledge_base import KnowledgeBase
import shutil
import os

def main():
    # Clean up previous DB run if exists for a fresh start in demo
    if os.path.exists("./chroma_db_demo"):
        shutil.rmtree("./chroma_db_demo")

    print("Initializing Knowledge Base...")
    kb = KnowledgeBase(path="./chroma_db_demo", collection_name="demo_knowledge")

    print("Adding documents...")
    
    # 1. Wiki Document
    kb.add_document(
        content="The payment gateway API requires an API key in the header 'X-API-Key'. The endpoint is https://api.payments.com/v1.",
        metadata={"source": "wiki", "title": "Payment Gateway Integration"},
        doc_id="wiki-1"
    )
    
    # 2. Jira Ticket
    kb.add_document(
        content="Ticket JIRA-123: Users align reporting 500 errors on checkout. Root cause was identified as a timeout in the inventory service.",
        metadata={"source": "jira", "id": "JIRA-123", "status": "closed"},
        doc_id="jira-123"
    )

    # 3. Code Repo Readme
    kb.add_document(
        content="To run the local dev environment, use 'docker-compose up'. Ensure .env file keeps the correct database credentials.",
        metadata={"source": "repo", "file": "README.md"},
        doc_id="repo-readme"
    )

    print(f"Total documents: {kb.count()}")

    # Query
    query = "How do I fix checkout errors?"
    print(f"\nQuerying: '{query}'")
    results = kb.query(query, n_results=2)

    print("\nResults:")
    for i in range(len(results['documents'][0])):
        doc = results['documents'][0][i]
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i]
        print(f"[{i+1}] (Score: {dist:.4f}) {doc}")
        print(f"    Metadata: {meta}")

    # Query 2
    query2 = "What header is needed for payments?"
    print(f"\nQuerying: '{query2}'")
    results2 = kb.query(query2, n_results=1)
    print(f"Result: {results2['documents'][0][0]}")

if __name__ == "__main__":
    main()
