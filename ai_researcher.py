"""
AI Automated Researcher
This script demonstrates how to use the OpenRouter client for AI research tasks.
"""

import os
import sys
from openrouter_client import OpenRouterClient


def main():
    """
    Main function demonstrating AI research capabilities
    """
    print("🤖 AI Automated Researcher")
    print("=" * 50)
    
    try:
        # Initialize the OpenRouter client
        print("Initializing AI client...")
        client = OpenRouterClient()
        print("✅ Client initialized successfully!\n")
        
        # Example 1: Image Analysis
        print("📸 Example 1: Image Analysis")
        print("-" * 30)
        image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
        
        print(f"Analyzing image: {image_url}")
        print("Analysis Result:")
        print("-" * 30)
        
        # Stream the image analysis response
        stream = client.analyze_image_stream(
            image_url=image_url,
            prompt="Describe this image in detail. What do you see? What is the setting and atmosphere?"
        )
        for chunk in stream:
            print(chunk, end='', flush=True)
        print("\n")
        
        # Display cost information
        if hasattr(stream, 'cost_info'):
            cost_info = stream.cost_info
            print(f"💰 Cost: ${cost_info['cost']:.4f} | Model: {cost_info['model']}")
            if cost_info['usage']:
                usage = cost_info['usage']
                print(f"📊 Tokens: {usage.get('total_tokens', 'N/A')} (Input: {usage.get('prompt_tokens', 'N/A')}, Output: {usage.get('completion_tokens', 'N/A')})")
        print()
        
        # Example 2: Research Query
        print("🔬 Example 2: Research Query")
        print("-" * 30)
        research_query = """
        What are the current trends and challenges in artificial intelligence research? 
        Please provide a comprehensive overview including:
        1. Recent breakthroughs
        2. Current limitations
        3. Future directions
        4. Ethical considerations
        """
        
        print("Researching AI trends...")
        print("Research Result:")
        print("-" * 30)
        
        # Stream the research response
        stream = client.research_query_stream(research_query)
        for chunk in stream:
            print(chunk, end='', flush=True)
        print("\n")
        
        # Display cost information
        if hasattr(stream, 'cost_info'):
            cost_info = stream.cost_info
            print(f"💰 Cost: ${cost_info['cost']:.4f} | Model: {cost_info['model']}")
            if cost_info['usage']:
                usage = cost_info['usage']
                print(f"📊 Tokens: {usage.get('total_tokens', 'N/A')} (Input: {usage.get('prompt_tokens', 'N/A')}, Output: {usage.get('completion_tokens', 'N/A')})")
        print()
        
        # Example 3: Custom Chat Completion
        print("💬 Example 3: Custom Chat Completion")
        print("-" * 30)
        messages = [
            {
                "role": "system",
                "content": "You are an expert AI researcher with deep knowledge of machine learning, neural networks, and AI ethics."
            },
            {
                "role": "user",
                "content": "Explain the concept of transfer learning in AI and provide examples of how it's used in practice."
            }
        ]
        
        print("Processing custom chat completion...")
        print("Chat Result:")
        print("-" * 30)
        
        # Stream the chat completion response
        stream = client.chat_completion_stream(messages)
        for chunk in stream:
            print(chunk, end='', flush=True)
        print("\n")
        
        # Display cost information
        if hasattr(stream, 'cost_info'):
            cost_info = stream.cost_info
            print(f"💰 Cost: ${cost_info['cost']:.4f} | Model: {cost_info['model']}")
            if cost_info['usage']:
                usage = cost_info['usage']
                print(f"📊 Tokens: {usage.get('total_tokens', 'N/A')} (Input: {usage.get('prompt_tokens', 'N/A')}, Output: {usage.get('completion_tokens', 'N/A')})")
        print()
        
        print("🎉 All examples completed successfully!")
        
        # Display total cost summary
        cost_summary = client.get_cost_summary()
        print("\n" + "=" * 50)
        print("📊 COST SUMMARY")
        print("=" * 50)
        print(f"💰 Total Cost: ${cost_summary['total_cost']:.4f}")
        print(f"📈 Total Requests: {cost_summary['request_count']}")
        print(f"📊 Average Cost per Request: ${cost_summary['average_cost_per_request']:.4f}")
        print("=" * 50)
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nTo fix this:")
        print("1. Set your OPENROUTER_API_KEY environment variable")
        print("2. You can set it by running: export OPENROUTER_API_KEY='your_api_key_here'")
        print("3. Or create a .env file with: OPENROUTER_API_KEY=your_api_key_here")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("Please check your internet connection and API key validity.")


def interactive_mode():
    """
    Interactive mode for continuous research queries
    """
    print("🔍 Interactive AI Research Mode")
    print("Type 'quit' or 'exit' to stop")
    print("=" * 50)
    
    try:
        client = OpenRouterClient()
        
        while True:
            query = input("\n📝 Enter your research query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not query:
                print("Please enter a valid query.")
                continue
            
            print("\n🤔 Thinking...")
            print("💡 Research Result:")
            print("-" * 40)
            try:
                # Stream the research response
                stream = client.research_query_stream(query)
                for chunk in stream:
                    print(chunk, end='', flush=True)
                print("\n")
                
                # Display cost information
                if hasattr(stream, 'cost_info'):
                    cost_info = stream.cost_info
                    print(f"💰 Cost: ${cost_info['cost']:.4f} | Model: {cost_info['model']}")
                    if cost_info['usage']:
                        usage = cost_info['usage']
                        print(f"📊 Tokens: {usage.get('total_tokens', 'N/A')} (Input: {usage.get('prompt_tokens', 'N/A')}, Output: {usage.get('completion_tokens', 'N/A')})")
                
                # Show running total
                cost_summary = client.get_cost_summary()
                print(f"💳 Running Total: ${cost_summary['total_cost']:.4f} ({cost_summary['request_count']} requests)")
                print()
                
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please set your OPENROUTER_API_KEY environment variable first.")
    
    finally:
        # Display final cost summary when exiting interactive mode
        try:
            cost_summary = client.get_cost_summary()
            if cost_summary['request_count'] > 0:
                print("\n" + "=" * 50)
                print("📊 FINAL COST SUMMARY")
                print("=" * 50)
                print(f"💰 Total Cost: ${cost_summary['total_cost']:.4f}")
                print(f"📈 Total Requests: {cost_summary['request_count']}")
                print(f"📊 Average Cost per Request: ${cost_summary['average_cost_per_request']:.4f}")
                print("=" * 50)
        except:
            pass  # Ignore errors when client wasn't initialized


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()
