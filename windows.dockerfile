FROM python:3.10-windowsservercore-ltsc2022 as builder

WORKDIR /app

COPY requirements.txt ./
COPY src/ ./

# Install pyinstaller and dependencies (no venv needed on Windows in this case).
RUN pip install --no-cache-dir -r requirements.txt

# Build the executable.
RUN pyinstaller --onefile --noconsole --name simplex \
    --add-data "src;src" \
    --hidden-import PyQt5.sip \
    src/main.py

# Create an output directory
RUN mkdir C:\\output

# Copy the executable to the output directory.
RUN copy dist\\simplex.exe C:\\output\\simplex.exe

# --- Second stage: Minimal runtime image ---

FROM mcr.microsoft.com/windows/nanoserver:ltsc2022

# Copy the executable.
COPY --from=builder C:\\output\\simplex.exe C:\\simplex.exe

# Set the entry point for direct execution
ENTRYPOINT ["C:\\simplex.exe"]
