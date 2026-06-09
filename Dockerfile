# Use lightweight official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# Install system dependencies (required for some ML packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir streamlit google-generativeai python-dotenv requests

# Copy the rest of the application code
COPY . .

# Run database setup to package prepopulated mock registry inside the container
RUN python utils/database_setup.py

# Expose Streamlit default Cloud Run port
EXPOSE 8080

# Run multi-service orchestrator
CMD ["python", "start.py"]
