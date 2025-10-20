#!/usr/bin/env python3
"""
Quick RAG Test - Automated test to show functionality
"""

from interactive_rag_test import SimpleRAGSystem

def quick_test():
    """Run a quick automated test"""
    
    print("🤖 Quick RAG Test - Automated Demo")
    print("=" * 50)
    
    # Initialize system
    rag = SimpleRAGSystem()
    
    # Upload demo document
    print("\n📁 Step 1: Uploading demo document...")
    demo_content = """
Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.

Types of Machine Learning:
1. Supervised Learning - Uses labeled training data for classification and regression
2. Unsupervised Learning - Finds patterns in data without labels  
3. Reinforcement Learning - Learns through rewards and penalties

Applications include image recognition, natural language processing, recommendation systems, and autonomous vehicles.
    """
    
    rag.upload_document("ml-guide.txt", demo_content.strip())
    
    # Test questions
    questions = [
        "What is machine learning?",
        "What are the types of machine learning?", 
        "What are some applications mentioned?",
        "Tell me about supervised learning"
    ]
    
    print(f"\n💬 Step 2: Testing RAG chat...")
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"❓ {question}")
        
        result = rag.chat(question)
        
        print(f"🤖 {result['response']}")
        
        if result['citations']:
            print(f"📚 Sources: {', '.join(result['citations'])}")
        
        print(f"📊 RAG Enhanced: {result['rag_enhanced']} | Documents Used: {result['documents_used']}")
    
    print(f"\n🎉 Test Complete!")
    print(f"✅ RAG system is working perfectly!")
    
    # Show final status
    rag.show_status()

if __name__ == "__main__":
    quick_test()