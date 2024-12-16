# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set environment variables to prevent debconf errors
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install Chrome dependencies and Chrome
RUN apt-get update && \
    apt-get install -y \
        wget \
        curl \
        unzip \
        gnupg \
        libnss3 \
        libgconf-2-4 \
        default-jdk \
        fonts-liberation \
        libappindicator3-1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libatspi2.0-0 \
        libatomic1 \
        libgbm1 \
        libgtk-3-0 \
        libx11-xcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxi6 \
        libxrandr2 \
        libxss1 \
        libxtst6 \
        xdg-utils \
        --no-install-recommends

# Download and install the latest stable version of Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb || apt-get -fy install && \
    rm google-chrome-stable_current_amd64.deb

# Install ChromeDriver dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    chromium-driver \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry