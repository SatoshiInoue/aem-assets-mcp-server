# Multi-stage build for Google Cloud Run
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY ./app ./app
COPY .env* ./

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8080

# Set environment variable for Cloud Run
ENV PORT=8080

# Run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
