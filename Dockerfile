FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Create data and logs directories and set permissions
RUN mkdir -p /app/data /app/data/logs && chown -R 1000:1000 /app

# Expose the port (if needed for health checks)
EXPOSE 8080

# Set non-root user
USER 1000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "exit(0)"

# Run the bot
CMD ["python", "-u", "app/email_bot.py"]
