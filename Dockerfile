# Multi-stage production container for Freight Audit Engine & Web Platform
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and documentation
COPY . .

# Generate baseline seed data
RUN python scripts/run_all.py --scale full --no-repro

# Expose Streamlit (8501) and FastAPI (8000)
EXPOSE 8501
EXPOSE 8000

# Default entrypoint runs Streamlit dashboard
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

