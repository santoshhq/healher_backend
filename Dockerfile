# ============================================
# Stage 1: Build dependencies
# ============================================
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build tools needed for some pip packages (bcrypt, pymongo, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better Docker layer caching
COPY requirements.txt .

# Install all Python dependencies into a separate prefix
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ============================================
# Stage 2: Final slim runtime image
# ============================================
FROM python:3.13-slim

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY main.py db.py chatbot.py food_scanner.py pcos_prediction.py ./
COPY modules/ ./modules/
COPY authentication/ ./authentication/
COPY chatbot/ ./chatbot/
COPY core/ ./core/
COPY daily_logs/ ./daily_logs/
COPY food_scanner/ ./food_scanner/
COPY insights/ ./insights/
COPY menstrual_tracker/ ./menstrual_tracker/
COPY rules_engine/ ./rules_engine/
COPY schemas/ ./schemas/
COPY scripts/ ./scripts/
COPY yoga_poses/ ./yoga_poses/

# Expose the port uvicorn will run on
EXPOSE 8080

# Run the FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
