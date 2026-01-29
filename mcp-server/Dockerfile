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

# Expose port for SSE transport
EXPOSE 8080

# Set environment variable for port
ENV PORT=8080

# Run the MCP server
CMD ["python", "-m", "app.main"]
