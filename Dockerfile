FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and templates
COPY config/ /app/config/
COPY src/ /app/src/
COPY templates/ /app/templates/

# Ensure output directories exist
RUN mkdir -p /app/out /app/data

# Expose API port
EXPOSE 8000

# Run FastAPI server via Uvicorn
CMD ["uvicorn", "src.killchain.api:app", "--host", "0.0.0.0", "--port", "8000"]
