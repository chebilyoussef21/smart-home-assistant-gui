# Dockerfile

FROM python:3.11

# Install system dependencies for Qt
RUN apt-get update && apt-get install -y \
    #libgl1-mesa-glx \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libxcb-randr0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-render-util0 \
    libxrender1 \
    libsm6 \
    libxext6 \
    libx11-xcb1 \
    qt5-qmake \
    qtbase5-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /customHAapp

# Copy project files
COPY . /customHAapp

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# QoL env for PyQt/Qt
ENV QT_X11_NO_MITSHM=1
ENV PYTHONUNBUFFERED=1

# Run the GUI
CMD ["python", "main.py"]