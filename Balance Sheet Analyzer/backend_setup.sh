# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask flask-cors flask-jwt-extended pandas sqlite3

# Run the backend
python app.py