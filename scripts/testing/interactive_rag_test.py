#!/usr/bin/env python3
"""
Interactive RAG Test - Simple command-line interface to test RAG functionality
"""

import json
import uuid
from datetime import datetime

class SimpleRAGSystem:
    """Simple RAG system for testing"""
    
    def __init__(self):
        self.documents = []
        self.conversations = []
        
    def upload_document(self, filename, content):
        """Upload and process a document"""
        
        print(f"\n📁 Processing document: {filename}")
        
        # Create chunks
        chunks = self.create_chunks(content)
        
        # Store document
        doc_id = str(uuid.uuid4())[:8]
        document = {
            'id': doc_id,
            'filename': filename,
            'content': content,
            'chunks': chunks,
            'uploaded_at': datetime.now().isoformat()
        }
        
        self.documents.append(document)
        
        print(f"✅ Document uploaded successfully!")
        print(f"   📄 File: {filename}")
        print(f"   🔢 Chunks: {len(chunks)}")
        print(f"   📊 Size: {len(content)} characters")
        
        return doc_id
    
    def create_chunks(self, text, chunk_size=300):
        """Create text chunks"""
        
        # Split by sentences for better chunks
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def search_documents(self, query, top_k=3):
        """Search for relevant document chunks"""
        
        query_words = set(query.lower().split())
        results = []
        
        for doc in self.documents:
            for i, chunk in enumerate(doc['chunks']):
                chunk_words = set(chunk.lower().split())
                
                # Calculate relevance score (simple word overlap)
                overlap = len(query_words.intersection(chunk_words))
                if overlap > 0:
                    score = overlap / len(query_words)
                    results.append({
                        'document': doc['filename'],
                        'chunk_index': i,
                        'chunk': chunk,
                        'score': score
                    })
        
        # Sort by relevance and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def chat(self, message):
        """Process a chat message with RAG"""
        
        print(f"\n💬 Processing: {message}")
        
        # Search for relevant documents
        relevant_chunks = self.search_documents(message)
        
        if relevant_chunks:
            print(f"🔍 Found {len(relevant_chunks)} relevant document chunks")
            
            # Create response based on relevant chunks
            response = self.generate_response(message, relevant_chunks)
            
            # Create citations
            citations = []
            for chunk in relevant_chunks:
                citation = f"{chunk['document']} (chunk {chunk['chunk_index'] + 1})"
                if citation not in citations:
                    citations.append(citation)
            
            result = {
                'response': response,
                'citations': citations,
                'rag_enhanced': True,
                'documents_used': len(relevant_chunks)
            }
        else:
            print("🔍 No relevant documents found")
            result = {
                'response': "I don't have any relevant information in your uploaded documents to answer that question. Please upload some documents first.",
                'citations': [],
                'rag_enhanced': False,
                'documents_used': 0
            }
        
        # Store conversation
        self.conversations.append({
            'message': message,
            'response': result['response'],
            'timestamp': datetime.now().isoformat(),
            'rag_enhanced': result['rag_enhanced']
        })
        
        return result
    
    def generate_response(self, question, relevant_chunks):
        """Generate a response based on relevant chunks"""
        
        # Combine relevant text
        context = "\n\n".join([chunk['chunk'] for chunk in relevant_chunks])
        
        # Simple response generation based on question type
        question_lower = question.lower()
        
        if "what is" in question_lower:
            # Look for definitions
            for chunk in relevant_chunks:
                text = chunk['chunk'].lower()
                if "is a" in text or "is the" in text:
                    return f"Based on your documents: {chunk['chunk']}"
        
        elif "types" in question_lower or "kinds" in question_lower:
            # Look for lists or categories
            response = "According to your documents, here are the types mentioned:\n\n"
            for chunk in relevant_chunks:
                if any(word in chunk['chunk'].lower() for word in ['types', 'kinds', '1.', '2.', '3.']):
                    response += f"• {chunk['chunk']}\n\n"
            return response.strip()
        
        elif "how" in question_lower or "explain" in question_lower:
            # Provide detailed explanation
            return f"Based on your uploaded documents:\n\n{context[:500]}..."
        
        elif "applications" in question_lower or "uses" in question_lower or "used for" in question_lower:
            # Look for applications/uses
            for chunk in relevant_chunks:
                if any(word in chunk['chunk'].lower() for word in ['applications', 'used', 'uses', 'including']):
                    return f"According to your documents: {chunk['chunk']}"
        
        # Default response with most relevant chunk
        return f"Based on your documents: {relevant_chunks[0]['chunk']}"
    
    def show_status(self):
        """Show system status"""
        
        print(f"\n📊 RAG System Status:")
        print(f"   📄 Documents: {len(self.documents)}")
        print(f"   💬 Conversations: {len(self.conversations)}")
        
        if self.documents:
            total_chunks = sum(len(doc['chunks']) for doc in self.documents)
            print(f"   🔢 Total chunks: {total_chunks}")
            print(f"   📁 Files:")
            for doc in self.documents:
                print(f"      • {doc['filename']} ({len(doc['chunks'])} chunks)")

def main():
    """Interactive RAG test"""
    
    print("🤖 Interactive RAG Test System")
    print("=" * 50)
    print("Commands:")
    print("  upload - Upload a document")
    print("  chat - Ask a question")
    print("  status - Show system status")
    print("  demo - Load demo document")
    print("  quit - Exit")
    print("=" * 50)
    
    rag_system = SimpleRAGSystem()
    
    while True:
        try:
            command = input("\n> ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                print("👋 Goodbye!")
                break
            
            elif command == 'upload':
                print("\n📁 Document Upload")
                filename = input("Enter filename: ").strip()
                if not filename:
                    filename = "document.txt"
                
                print("Enter document content (press Enter twice when done):")
                lines = []
                while True:
                    line = input()
                    if line == "" and lines and lines[-1] == "":
                        break
                    lines.append(line)
                
                content = "\n".join(lines).strip()
                if content:
                    rag_system.upload_document(filename, content)
                else:
                    print("❌ No content provided")
            
            elif command == 'chat':
                if not rag_system.documents:
                    print("⚠️  No documents uploaded yet. Use 'upload' or 'demo' first.")
                    continue
                
                question = input("\n💬 Ask a question: ").strip()
                if question:
                    result = rag_system.chat(question)
                    
                    print(f"\n🤖 Response:")
                    print(f"   {result['response']}")
                    
                    if result['citations']:
                        print(f"\n📚 Sources:")
                        for citation in result['citations']:
                            print(f"   • {citation}")
                    
                    print(f"\n📊 RAG Enhanced: {result['rag_enhanced']}")
                    print(f"📄 Documents Used: {result['documents_used']}")
                else:
                    print("❌ No question provided")
            
            elif command == 'status':
                rag_system.show_status()
            
            elif command == 'demo':
                demo_content = """
Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence (AI) that enables computers to learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.

Types of Machine Learning:

Supervised Learning uses labeled training data to learn a mapping function from input variables to output variables. Examples include classification and regression problems.

Unsupervised Learning finds hidden patterns in data without labeled examples. Common techniques include clustering and dimensionality reduction.

Reinforcement Learning involves an agent that learns to make decisions by taking actions in an environment to maximize cumulative reward.

Key Concepts:
Training Data is the dataset used to teach the machine learning algorithm. Features are individual measurable properties of observed phenomena. A Model is the mathematical representation of a real-world process. An Algorithm is the method used to build the model.

Applications:
Machine learning is used in various fields including image recognition, natural language processing, recommendation systems, autonomous vehicles, medical diagnosis, and financial fraud detection.
                """
                
                rag_system.upload_document("ml-fundamentals.txt", demo_content.strip())
                print("\n💡 Try asking:")
                print("   • What is machine learning?")
                print("   • What are the types of machine learning?")
                print("   • What are some applications of machine learning?")
            
            elif command == 'help':
                print("\nCommands:")
                print("  upload - Upload a document")
                print("  chat - Ask a question")
                print("  status - Show system status")
                print("  demo - Load demo document")
                print("  quit - Exit")
            
            else:
                print(f"❌ Unknown command: {command}")
                print("Type 'help' for available commands")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()