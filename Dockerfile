
# Stage 1: Builder
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies for OCR and Image Processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Copy system libraries from builder (simplified for example) or re-install
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy python env
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy Application Code
COPY backend /app/backend
COPY server /app/server
COPY api.py /app/api.py

# Expose API Port
EXPOSE 5000

# Run with Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "api:app"]
