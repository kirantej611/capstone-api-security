FROM python:3.11-slim

WORKDIR /app

# System dependencies for scientific packages if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Assuming requirements.txt is provided, we copy and install it
# If it doesn't exist, we fallback to creating one or just installing directly.
COPY requirements.txt* /app/

RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --default-timeout=1000 --retries 10 -r requirements.txt

# Copy all project code
COPY . /app/

# Set Python path to include the current directory
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8001

# Command to run
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
