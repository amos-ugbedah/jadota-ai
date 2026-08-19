# Use Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY backend/requirements/base.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY backend/ /app/

# Expose the port
EXPOSE 7860

# Run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
