# Backend Architecture Overview

This document explains how the ScamShield backend is structured.

## FastAPI Routes
- **/scan** → Handles text, URLs, or phone numbers for scanning.
- **/history** → Fetches the previous scan results.
- **/stats** → Provides statistics about scan results.
- **/health** → Returns 'OK' if the API is live.

## Core Modules
- **server.py** → Main FastAPI app.
- **config.py** → (To be added) handles environment variables.
- **logging_setup.py** → (To be added) central logging for all endpoints.

## Database
- MongoDB is used for storing history, blacklists, and statistics.

## Future Improvements
- Rate limiting, authentication, and AI-driven adaptive scoring.

