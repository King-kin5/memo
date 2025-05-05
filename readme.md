# PhotoRemind App

A smart photo reminder application that helps users capture memorable moments based on location and preferences.

## Overview

This application consists of two main AI agents:

1. **PhotoReminderAgent** ([agent.py](agent.py)): Location-based photo reminder generator
2. **SnapPhotoThemeAgent** ([photo.py](photo.py)): Snapchat-focused photo spot evaluator this is terminal based 

### Key Differences

#### PhotoReminderAgent (agent.py)
- **Purpose**: Generates real-time photo reminders based on user's current location
- **Features**:
  - Integrates with Google Places API for accurate location data
  - Uses LangChain for structured agent interactions
  - Works with the web application to provide location-based notifications
  - Focuses on identifying photo opportunities in real-time
  - Part of the main web application flow

#### SnapPhotoThemeAgent (photo.py)
- **Purpose**: Evaluates specific locations for their "Snapchat-worthiness"
- **Features**:
  - Uses DuckDuckGo search for location research
  - Standalone CLI application
  - Provides detailed Snapchat-specific recommendations:
    - Filter suggestions
    - Shot types
    - Creative caption ideas
  - More focused on social media sharing and entertainment value

## Setup

1. Create a `.env` file based on [.env.example](.env.example):
```
GOOGLE_API_KEY=your_google_gemini_api_key_here
PLACES_API_KEY=your_google_places_api_key_here
```

2. Install dependencies:
```sh
pip install -r requirements.txt
```

## Usage

### Web Application
Run the main web application:
```sh
python main.py
```

### Snapchat Theme Evaluator
Run the standalone Snapchat spot evaluator:
```sh
python photo.py
```

## Dependencies

- FastAPI for web server
- LangChain for AI agent operations
- Google Gemini API for AI processing
- Google Places API for location data
- DuckDuckGo Search API for location research

## Project Structure

```
├── agent.py          # Main photo reminder agent
├── photo.py          # Snapchat theme evaluator
├── main.py           # Web application server
├── templates/        # HTML templates
├── static/          # Static assets
└── requirements.txt  # Project dependencies
```