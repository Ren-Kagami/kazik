# 🎰 Slot Machine - Probability Theory Explorer

A FastAPI-based web application that implements a slot machine game for exploring probability theory and statistical concepts.

## Features

- Interactive slot machine game
- Real-time probability calculations
- Statistical analysis and simulations
- Session tracking and game statistics
- Modern web interface with animations

## Installation

1. Clone or create this project structure
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the FastAPI server:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. Open your browser and visit:
   - Game interface: http://localhost:8000/static/index.html
   - API documentation: http://localhost:8000/docs

## Project Structure

- `app/`: Main application code
- `app/core/`: Core configuration and probability calculations
- `app/api/`: API routes and endpoints
- `app/models/`: Pydantic data models
- `app/static/`: Frontend files (HTML, CSS, JavaScript)
- `tests/`: Unit tests

## API Endpoints

- `POST /api/v1/session` - Create new game session
- `GET /api/v1/session/{session_id}` - Get session info
- `POST /api/v1/spin/{session_id}` - Spin the slot machine
- `GET /api/v1/probability` - Get probability analysis
- `POST /api/v1/simulate` - Run game simulations

## Development

To run tests:
```bash
pytest tests/ --cov=app
```

## License

MIT License
