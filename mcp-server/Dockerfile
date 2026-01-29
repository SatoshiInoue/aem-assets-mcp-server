# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy shared modules
COPY shared/ /app/shared/

# Copy MCP server code
COPY mcp-server/requirements.txt /app/
COPY mcp-server/app/ /app/app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run the MCP server directly with Python (FastMCP has built-in server)
# This follows the official Cloud Run MCP server pattern
CMD ["python", "-m", "app.main"]
