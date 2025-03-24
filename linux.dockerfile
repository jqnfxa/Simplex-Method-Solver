FROM python:3.10-slim-buster AS builder

# Install build dependencies, including Qt5 and X11.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-dev \
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    libxkbcommon-x11-0 \
    qtbase5-dev \
    qtchooser \
    qt5-qmake \
    qtbase5-dev-tools \
    libx11-xcb-dev \
    libxcb-xinerama0-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 
WORKDIR /app

COPY requirements.txt .
COPY src/ /app/src/

# Create a virtual environment and install dependencies.
RUN python -m venv .venv
RUN . .venv/bin/activate && .venv/bin/pip install --no-cache-dir -r requirements.txt

# Build the executable using pyinstaller.
RUN . .venv/bin/activate && \
    pyinstaller --onefile --noconsole --name simplex \
    --add-data "src:src" \
    --hidden-import PyQt5.sip \
    src/main.py

# Copy the executable directly to /usr/local/bin.
RUN cp dist/simplex /usr/local/bin/

# --- Second stage: Minimal runtime image ---
FROM debian:buster-slim

# Install a MORE COMPREHENSIVE set of runtime dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxcb1 \
    libx11-xcb1 \
    libgl1 \
    libxext6 libxrender1 libxi6 libxrandr2 \
    && rm -rf /var/lib/apt/lists/*


# Copy the executable from the builder stage.
COPY --from=builder /usr/local/bin/simplex /usr/local/bin/simplex

# Make the executable runnable.
RUN chmod +x /usr/local/bin/simplex

# Set the entrypoint.
ENTRYPOINT ["simplex"]
