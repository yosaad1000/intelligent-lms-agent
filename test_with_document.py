#!/usr/bin/env python3
"""
Test RAG system with the dummy document
"""

from interactive_rag_test import SimpleRAGSystem

def test_with_dummy_doc():
    """Test RAG system with the dummy document"""
    
    print("🤖 Testing RAG System with Dummy Document")
    print("=" * 60)
    
    # Initialize RAG system
    rag = SimpleRAGSystem()
    
    # Load the test document
    print("\n📁 Loading test document...")
    try:
        with open('test_document.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        rag.upload_document("AI_ML_Guide.txt", content)
        
    except FileNotFoundError:
        print("❌ test_document.txt not found!")
        return
    
    # Test questions about the document
    test_questions = [
        "What is artificial intelligence?",
        "What are the three types of machine learning?",
        "Tell me about supervised learning",
        "What are some applications of machine learning in healthcare?",
        "What tools are mentioned for machine learning?",
        "What is overfitting?",
        "How is machine learning used in finance?",
        "What algorithms are mentioned in the document?"
    ]
    
    print(f"\n💬 Testing {len(test_questions)} questions...")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*50}")
        print(f"Question {i}: {question}")
        print('='*50)
        
        result = rag.chat(question)
        
        print(f"🤖 Answer:")
        print(f"{result['response']}")
        
        if result['citations']:
            print(f"\n📚 Sources: {', '.join(result['citations'])}")
        
        print(f"\n📊 RAG Enhanced: {'✅' if result['rag_enhanced'] else '❌'}")
        print(f"📄 Documents Used: {result['documents_used']}")
        
        # Wait for user to continue
        input("\nPress Enter to continue to next question...")
    
    print(f"\n🎉 Test Complete!")
    rag.show_status()
    
    # Interactive mode
    print(f"\n💬 Now you can ask your own questions!")
    print("Type 'quit' to exit")
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if question:
                result = rag.chat(question)
                
                print(f"\n🤖 Answer:")
                print(f"{result['response']}")
                
                if result['citations']:
                    print(f"\n📚 Sources: {', '.join(result['citations'])}")
                
                print(f"\n📊 RAG Enhanced: {'✅' if result['rag_enhanced'] else '❌'}")
            
        except KeyboardInterrupt:
            break
    
    print("\n👋 Thanks for testing the RAG system!")

if __name__ == "__main__":
    test_with_dummy_doc()