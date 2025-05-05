from langchain_google_genai import ChatGoogleGenerativeAI
import os
import logging
from dotenv import load_dotenv
from duckduckgo_search import DDGS  

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables from .env file
load_dotenv()

class SnapPhotoThemeAgent:
    """Agent that recommends Snapchat photo themes for memorable places."""
    
    def __init__(self):
        """Initialize the Snapchat Photo Theme Agent with Google Gemini."""
        # Check for API key
        if not os.getenv("GOOGLE_API_KEY"):
            logger.error("GOOGLE_API_KEY environment variable is not set")
            raise EnvironmentError("GOOGLE_API_KEY environment variable is not set")
        
        try:
            # Initialize the Google Gemini model
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
            logger.info("Successfully initialized Google Gemini model")
            
            # Initialize DuckDuckGo search
            self.search_engine = DDGS()
            logger.info("Successfully initialized DuckDuckGo search")
        except Exception as e:
            logger.error(f"Failed to initialize: {str(e)}")
            raise
    
    def search_place_info(self, place_name: str) -> str:
        """Search for information about the place using DuckDuckGo."""
        logger.info(f"Searching for information about: {place_name}")
        
        try:
            # Search for the place with keywords that will help determine what kind of place it is
            search_query = f"{place_name} location type tourist information"
            search_results = list(self.search_engine.text(search_query, max_results=5))
            
            if not search_results:
                return "No information found about this place."
            
            # Combine the top search results
            combined_info = "\n".join([
                f"Title: {result['title']}\nDescription: {result['body']}"
                for result in search_results
            ])
            
            logger.info(f"Found information about {place_name}")
            return combined_info
        except Exception as e:
            error_msg = f"Error searching for place information: {str(e)}"
            logger.error(error_msg)
            return f"Failed to search for information about this place: {str(e)}"
    
    def evaluate_photo_worthiness(self, place_name: str) -> str:
        """Evaluate if a place is photo-worthy and suggest Snapchat themes."""
        logger.info(f"Evaluating photo worthiness for: {place_name}")
        
        # First, search for information about the place
        place_info = self.search_place_info(place_name)
        logger.info("Retrieved place information from search")
        
        prompt = f"""
        I need to evaluate if "{place_name}" is photo-worthy for Snapchat, focusing ONLY on entertainment, self-enjoyment, or creating memories.
        
        Here's information I found about this place:
        {place_info}
        
        Based on this information, follow these steps:
        1. Identify what type of place this is (beach, museum, restaurant, landmark, etc.).
        2. Determine if this place is likely a good spot for photos that are fun, entertaining, or memory-worthy.
        3. If it IS photo-worthy, suggest:
           - 3 specific Snapchat themes or filters that would work well there based on the type of place
           - What specific elements to focus on in photos
           - Best type of shots (selfies, panoramas, close-ups, etc.)
           - Creative caption ideas for sharing
        4. If it is NOT photo-worthy for entertainment/enjoyment/memories/, explain briefly why in a single sentence.
        Important guidelines:
        - Focus ONLY on entertainment value, fun factor, and memory creation
        - Keep your response concise and enthusiastic (use emojis!)
        - Be specific to this exact location and its characteristics, not generic
        - Prioritize uniqueness and "shareability" on social media
        """
        
        try:
            response = self.llm.invoke(prompt).content
            logger.info(f"Successfully generated recommendations for {place_name}")
            return response
        except Exception as e:
            error_msg = f"Error generating recommendations: {str(e)}"
            logger.error(error_msg)
            return f"Sorry, I couldn't evaluate this place right now due to an error. Please try again later."


def main():
    """Main function to run the CLI application."""
    try:
        # Initialize the agent
        agent = SnapPhotoThemeAgent()
        
        print("\n🌟 SNAPCHAT PHOTO SPOT EVALUATOR 🌟")
        print("=" * 60)
        print("Tell me a place, and I'll tell you if it's Snapchat-worthy!")
        print("I'll search for information about the place and suggest themes, filters, and creative ideas for your snaps.")
        print("=" * 60)
        
        while True:
            # Get place input from user
            place_name = input("\n📍 Enter a place name (or 'exit' to quit): ")
            
            if place_name.lower() in ['exit', 'quit', 'q']:
                print("\nThanks for using the Snapchat Photo Spot Evaluator! Happy snapping! 📸✨")
                break
            
            if not place_name.strip():
                print("Please enter a valid place name.")
                continue
            
            # Show processing message
            print(f"\n🔍 Searching for information about {place_name}...")
            print(f"🔍 Evaluating {place_name} as a Snapchat photo spot...")
            
            # Get evaluation and recommendations
            result = agent.evaluate_photo_worthiness(place_name)
            
            # Print the recommendations
            print("\n📱 SNAPCHAT SPOT EVALUATION 📱")
            print("=" * 60)
            print(result)
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        print("Make sure you have set the GOOGLE_API_KEY environment variable in your .env file.")
        print("You also need to install the duckduckgo-search library: pip install duckduckgo-search")


if __name__ == "__main__":
    main()