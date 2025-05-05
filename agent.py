from langchain.agents import AgentType, initialize_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
import requests
import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class PhotoReminderAgent:
    """Agent that generates photo reminders based on location context."""
    
    def __init__(self, verbose: bool = True):
        """Initialize the Photo Reminder Agent with LangChain components."""
        # Check for API keys
        if not os.getenv("GOOGLE_API_KEY"):
            logger.error("GOOGLE_API_KEY environment variable is not set")
            raise EnvironmentError("GOOGLE_API_KEY environment variable is not set")
        if not os.getenv("PLACES_API_KEY"):
            logger.error("PLACES_API_KEY environment variable is not set")
            raise EnvironmentError("PLACES_API_KEY environment variable is not set")
        
        try:
            # Initialize the Google Gemini model
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
            logger.info("Successfully initialized Google Gemini model")
        except Exception as e:
            logger.error(f"Failed to initialize Google Gemini model: {str(e)}")
            raise
        
        try:
            # Initialize the LangChain agent with our tools
            self.agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                verbose=verbose,
                handle_parsing_errors=True
            )
            logger.info("Successfully initialized LangChain agent")
        except Exception as e:
            logger.error(f"Failed to initialize LangChain agent: {str(e)}")
            raise
    
    @property
    def tools(self) -> List:
        """Return the list of tools available to the agent."""
        return [
            self.get_place_details_tool(),
            self.generate_reminder_tool()
        ]
    
    def get_place_details_tool(self):
        """Create a tool to fetch location details from Google Places API."""
        @tool
        def get_place_details(latitude: float, longitude: float) -> Dict[str, Any]:
            """Fetch detailed information about current location using Google Places API."""
            logger.info(f"Fetching place details for coordinates: {latitude}, {longitude}")
            try:
                response = requests.get(
                    "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                    params={
                        "location": f"{latitude},{longitude}",
                        "radius": 50,  # Search within 50 meters of location
                        "key": os.getenv("PLACES_API_KEY")
                    },
                    timeout=5
                )
                response.raise_for_status()
                
                data = response.json()
                logger.debug(f"Places API response status: {data.get('status')}")
                
                results = data.get('results', [{}])
                best_result = results[0] if results else {}
                
                # Extract relevant place information
                place_info = {
                    "type": best_result.get('types', ['unknown'])[0],
                    "name": best_result.get('name', 'current location'),
                    "address": best_result.get('vicinity', 'unknown location'),
                    "rating": best_result.get('rating', 0),
                    "is_popular": best_result.get('user_ratings_total', 0) > 100
                }
                
                logger.info(f"Successfully retrieved place info: {place_info['name']}")
                return place_info
            except requests.exceptions.RequestException as e:
                error_msg = f"API request failed: {str(e)}"
                logger.error(error_msg)
                return {"error": error_msg}
            except Exception as e:
                error_msg = f"Failed to get place details: {str(e)}"
                logger.error(error_msg)
                return {"error": error_msg}
        
        return get_place_details
    
    def generate_reminder_tool(self):
        """Create a tool to generate photo reminders based on place information."""
        @tool
        def generate_photo_reminder(place_info: Dict[str, Any], preferences: List[str]) -> str:
            """Generate a photo reminder message considering place details and user preferences."""
            logger.info(f"Generating photo reminder for place: {place_info.get('name', 'unknown')}")
            
            # Check if there was an error getting place info
            if "error" in place_info:
                logger.warning(f"Using fallback reminder due to place info error: {place_info['error']}")
                return "📸 Don't forget to capture this moment!"
            
            prompt = f"""
            Create a friendly photo reminder for this location:
            
            Name: {place_info.get('name')}
            Type: {place_info.get('type')}
            Address: {place_info.get('address')}
            Rating: {place_info.get('rating')}
            Is Popular: {place_info.get('is_popular', False)}
            User Preferences: {', '.join(preferences)}
            
            Requirements:
            - Include 1-2 relevant emojis that match the place type
            - Max 15 words
            - Friendly and encouraging tone
            - Consider place type and user preferences
            - If it's a highly-rated place, emphasize its quality
            
            Examples:
            - "🌳 Don't miss the beautiful scenery at this park!"
            - "🏛️ Capture this impressive museum architecture!"
            - "☕ This coffee shop has perfect lighting for your food photos!"
            """
            
            try:
                response = self.llm.invoke(prompt).content
                logger.info(f"Successfully generated reminder: {response}")
                return response
            except Exception as e:
                # Fallback reminder if LLM call fails
                error_msg = f"Failed to generate reminder: {str(e)}"
                logger.error(error_msg)
                fallback = f"📸 Don't miss taking a photo at {place_info.get('name', 'this place')}!"
                logger.info(f"Using fallback reminder: {fallback}")
                return fallback
        
        return generate_photo_reminder
    
    def process_location(self, lat: float, lng: float, preferences: List[str]) -> Dict[str, Any]:
        """Process a location to determine if a photo reminder should be generated."""
        logger.info(f"Processing location: {lat}, {lng} with preferences: {preferences}")
        try:
            # Structure the input for the agent
            agent_input = (
                f"I am at coordinates {lat},{lng}. "
                f"First, get details about this location. "
                f"Then, decide if it's worth taking a photo here based on the location type and my preferences: {preferences}. "
                f"If it is, generate a suitable photo reminder message."
            )
            
            # Run the agent
            logger.info("Running agent with location input")
            response = self.agent.run(input=agent_input)
            logger.info(f"Agent response: {response}")
            
            # Process the response
            if "not worth" in response.lower() or "wouldn't recommend" in response.lower():
                logger.info("Agent determined location is not photo-worthy")
                return {
                    "reminder": False,
                    "message": response
                }
            
            logger.info("Photo reminder generated successfully")
            return {
                "reminder": True,
                "message": response,
                "location": {"lat": lat, "lng": lng}
            }
        except Exception as e:
            error_msg = f"Error processing location: {str(e)}"
            logger.error(error_msg)
            return {
                "reminder": False,
                "error": error_msg,
                "location": {"lat": lat, "lng": lng}
            }