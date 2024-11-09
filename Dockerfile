FROM python:3.9-slim-bullseye

# Set working directory
WORKDIR /app

# Copy the content of the current directory into the container's /app directory
COPY . /app

# Add Aliyun mirror, update apt packages, and install necessary dependencies
RUN echo "deb http://mirrors.aliyun.com/debian/ bullseye main contrib non-free" > /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y \
       libgl1-mesa-glx \
       libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*  # Clean up after apt to reduce image size

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Expose port 5000 for Flask
EXPOSE 5000

# Set Flask environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Run Flask app
CMD ["flask", "run", "--host", "0.0.0.0"]
