# Financial System

A financial management system built with Python.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python src/main.py
```

## Project Structure

- `config/`: Configuration files
- `src/`: Source code
  - `core/`: Core business logic
  - `database/`: Database models and connection
  - `interfaces/`: User interfaces
  - `services/`: Business services
  - `utils/`: Utility functions
- `tests/`: Test files
- `data/`: Data files