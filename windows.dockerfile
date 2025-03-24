FROM python:3.10-windowsservercore-ltsc2022 AS builder

# Set shell to PowerShell
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

# Install Python dependencies (may need tweaking based on your requirements.txt)
WORKDIR /app

COPY requirements.txt .
COPY src/ /app/src/

# Create a virtual environment and install dependencies
RUN python -m venv .venv ; \
    . .venv/Scripts/activate ; \
    pip install --no-cache-dir -r requirements.txt

# Install pyinstaller
RUN . .venv/Scripts/activate; pip install pyinstaller

# Build the executable.
RUN . .venv/Scripts/activate ; \
    pyinstaller --onefile --noconsole --name simplex `
        --add-data "src;src" `
        --hidden-import PyQt5.sip `
        src/main.py

# --- Second stage: Minimal runtime image ---
FROM mcr.microsoft.com/windows/servercore:ltsc2022-amd64

# Copy the executable from the builder stage.
COPY --from=builder /app/dist/simplex.exe /simplex.exe

# Set entry point to use PowerShell
ENTRYPOINT ["powershell", "/simplex.exe"]
