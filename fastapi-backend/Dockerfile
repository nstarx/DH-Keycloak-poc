# Use stable Python base
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Copy dependencies first
COPY requirements.txt .

# Install Python dependencies (no apt-get)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
