FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Set Python path
ENV PYTHONPATH=/app

#REMAPED IN DOCKER COMPOSE FOR DEV
EXPOSE 8003 
# DO NOT CHANGE THE PORT THIS IS NOT YOUR ISSUE

# Run the application
CMD ["python", "-m", "src.main"]
