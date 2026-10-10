FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./

# Keep wheel dependencies on PyPI; the PyTorch index has returned mismatched
# hashes for transitive packages such as mpmath.
RUN pip install --no-cache-dir --default-timeout=1000 --retries 10 \
        --index-url https://download.pytorch.org/whl/cpu \
        --no-deps torch==2.14.1+cpu && \
    pip install --no-cache-dir --default-timeout=1000 --retries 10 \
        --index-url https://pypi.org/simple \
        -r requirements.txt

COPY api/ ./api/
COPY models/ ./models/
COPY utils/ ./utils/
COPY saved_models/ ./saved_models/

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
