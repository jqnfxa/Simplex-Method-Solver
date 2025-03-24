FROM python:3.10-windowsservercore-ltsc2022 AS builder

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

WORKDIR /app

COPY requirements.txt .
COPY src/ /app/src/

RUN python -m venv .venv ; `
    . .venv/Scripts/activate ; `
    pip install --no-cache-dir -r requirements.txt ; `
    pip install pyinstaller

# Build the executable.  MAJOR improvements here.
RUN . .venv/Scripts/activate ; `
    $pyi_args = @(  `
        '--onefile',  `
        '--noconsole',  `
        '--name', 'simplex',  `
        '--add-data', 'src;src',  `
        'src/main.py'  `
    ) ; `
    pyinstaller $pyi_args

# --- Second stage: Minimal runtime image ---
FROM mcr.microsoft.com/windows/servercore:ltsc2022-amd64

COPY --from=builder /app/dist/simplex.exe /simplex.exe

ENTRYPOINT ["powershell", "/simplex.exe"]
