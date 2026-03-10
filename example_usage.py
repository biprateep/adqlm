from adqlm.client import ADQLMAssistant

def main():
    # Initialize the assistant
    # Ensure GOOGLE_API_KEY is set in your environment
    assistant = ADQLMAssistant()
    
    # Ingest documentation (this happens once per session, but could be persisted)
    print("Ingesting documentation...")
    assistant.ingest_docs()
    
    print("\n--- ADQLM Assistant CLI ---")
    print("Type 'exit' to quit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        print("Assistant: Processing...")
        result = assistant.process_query(user_input)
        
        print(f"\n[Generated SQL]\n{result['sql']}")
        print(f"\n[Explanation]\n{result['explanation']}")
        
        if result['data'] is not None:
            print(f"\n[Data Preview]\n{result['data']}")
        
        print("\n" + "-"*30 + "\n")

if __name__ == "__main__":
    main()
