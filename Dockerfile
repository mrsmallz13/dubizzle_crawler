# Use the official Python image as base
FROM mcr.microsoft.com/playwright/python:v1.51.0-jammy

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the required browsers (already handled by base image, but safe to ensure)
RUN playwright install --with-deps chromium

# Default command
CMD ["python", "dubizzle_crawler_all_emirates.py"]