from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Optional
import os
import json
import logging
from pathlib import Path
from agent import PhotoReminderAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Photo Reminder App")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the PhotoReminderAgent
try:
    photo_agent = PhotoReminderAgent(verbose=False)
    logger.info("PhotoReminderAgent initialized successfully")
except EnvironmentError as e:
    logger.error(f"Failed to initialize PhotoReminderAgent: {e}")
    photo_agent = None
except Exception as e:
    logger.error(f"Unexpected error initializing PhotoReminderAgent: {e}")
    photo_agent = None

# In-memory storage for active reminders (will be lost on restart)
active_reminders = []

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "reminders": active_reminders}
    )

missing_keys = []
if not os.getenv("GOOGLE_API_KEY"):
    missing_keys.append("GOOGLE_API_KEY")
if not os.getenv("PLACES_API_KEY"):
    missing_keys.append("PLACES_API_KEY")

if missing_keys:
    logger.error(f"Missing required API keys: {', '.join(missing_keys)}")
    logger.error("Please set these environment variables or add them to a .env file")
    photo_agent = None
    initialization_error = f"Missing required API keys: {', '.join(missing_keys)}"
else:
    try:
        photo_agent = PhotoReminderAgent(verbose=False)
        logger.info("PhotoReminderAgent initialized successfully")
        initialization_error = None
    except Exception as e:
        logger.error(f"Failed to initialize PhotoReminderAgent: {e}")
        photo_agent = None
        initialization_error = str(e)
@app.post("/process-location")
async def process_location(
    latitude: float = Form(...),
    longitude: float = Form(...),
    preferences: str = Form(...)
):
    """Process a location and generate a photo reminder if appropriate."""
    if not photo_agent:
        logger.error("Photo agent not initialized. Check API keys.")
        raise HTTPException(status_code=500, detail="Photo agent not initialized. Check API keys.")
    
    try:
        # Parse preferences from comma-separated string
        preference_list = [p.strip() for p in preferences.split(",") if p.strip()]
        
        logger.info(f"Processing location: {latitude}, {longitude} with preferences: {preference_list}")
        
        # Process location with the agent
        result = photo_agent.process_location(latitude, longitude, preference_list)
        
        if result.get("reminder", False):
            # Add to active reminders if it's a valid reminder
            reminder_id = len(active_reminders)
            reminder = {
                "id": reminder_id,
                "message": result["message"],
                "latitude": latitude,
                "longitude": longitude,
                "preferences": preference_list
            }
            active_reminders.append(reminder)
            
            try:
                # Try to render the notification template
                html_content = templates.get_template("components/notification.html").render(
                    reminder=reminder,
                    request=None  # You might need to add this if your template requires it
                )
                
                return {
                    "success": True,
                    "reminder": reminder,
                    "html": html_content
                }
            except Exception as template_error:
                logger.error(f"Template rendering error: {template_error}")
                return {
                    "success": True,
                    "reminder": reminder,
                    "html": f"<div>New reminder: {reminder['message']}</div>"  # Fallback HTML
                }
        else:
            # Return the error or message explaining why no reminder was generated
            return {
                "success": False,
                "message": result.get("message", result.get("error", "Unknown error"))
            }
    except Exception as e:
        logger.error(f"Error processing location: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )

@app.post("/dismiss-reminder/{reminder_id}")
async def dismiss_reminder(reminder_id: int):
    """Dismiss a reminder by ID."""
    global active_reminders
    
    try:
        # Find the reminder by ID
        reminder = next((r for r in active_reminders if r["id"] == reminder_id), None)
        if reminder:
            # Remove the reminder
            active_reminders = [r for r in active_reminders if r["id"] != reminder_id]
            return {"success": True}
        else:
            return {"success": False, "message": "Reminder not found"}
    except Exception as e:
        logger.error(f"Error dismissing reminder: {e}")
        return {"success": False, "message": str(e)}

@app.get("/test-reminder")
async def test_reminder():
    """Generate a test reminder (for development purposes)."""
    try:
        test_reminder = {
            "id": len(active_reminders),
            "message": "📸 Test reminder! This is how notifications will look.",
            "latitude": 40.7812,
            "longitude": -73.9665,
            "preferences": ["testing"]
        }
        active_reminders.append(test_reminder)
        
        try:
            html_content = templates.get_template("components/notification.html").render(
                reminder=test_reminder,
                request=None  # You might need to add this if your template requires it
            )
        except Exception as template_error:
            logger.error(f"Template rendering error: {template_error}")
            html_content = f"<div>Test reminder: {test_reminder['message']}</div>"  # Fallback HTML
        
        return {
            "success": True,
            "reminder": test_reminder,
            "html": html_content
        }
    except Exception as e:
        logger.error(f"Error creating test reminder: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Server error: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)