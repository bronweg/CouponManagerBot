# Use Python Alpine for minimal size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create resources directory if it doesn't exist
RUN mkdir -p resources

# Set environment variables with defaults
ENV TELEGRAM_BOT_TOKEN=""
ENV ALLOWED_USER_IDS=""
ENV COUPON_REPO_TYPE="sqlite"
ENV COUPON_REPO_CONFIG='{"db_path":"resources/coupon_management.db","table_name":"coupons"}'

ARG USERNAME=appuser
ARG UID=1001
ARG GROUPNAME=appgroup
ARG GID=$UID

# Create a non-root user for security (important for Kubernetes)
RUN groupadd --gid $GID $GROUPNAME && \
    useradd --uid $UID --gid $GID $USERNAME

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup /app

# Set python path
ENV PYTHONPATH="/app"

# Switch to non-root user
USER appuser

# Health check (optional, useful for Kubernetes)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the application
CMD ["python", "start_bot.py"]
