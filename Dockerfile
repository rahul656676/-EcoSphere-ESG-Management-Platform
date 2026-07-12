# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the application port
EXPOSE 5000

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Run with Gunicorn instead of Flask dev server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--chdir", "backend", "app:app"]
