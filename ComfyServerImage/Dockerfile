# Stage 1: Base image with common dependencies
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# Prevents prompts from packages asking for user input during installation
ENV DEBIAN_FRONTEND=noninteractive
# Prefer binary wheels over source distributions for faster pip installations
ENV PIP_PREFER_BINARY=1
# Ensures output from python is printed immediately to the terminal without buffering
ENV PYTHONUNBUFFERED=1 
# Speed up some cmake builds
ENV CMAKE_BUILD_PARALLEL_LEVEL=8

# Install Python, git and other necessary tools
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    libsm6 \
    libgl1 \
    libglib2.0-0 \
    libxext6 \
    libxrender1 \
    libgl1-mesa-glx\
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*


# Python Evn
RUN pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121


WORKDIR /runpod-volume
RUN git clone https://github.com/comfyanonymous/ComfyUI.git
RUN pip3 install -r /runpod-volume/ComfyUI/requirements.txt

## install custom nodes
WORKDIR /runpod-volume/ComfyUI/custom_nodes
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git



# Change working directory to ComfyUI
WORKDIR /runpod-volume/ComfyUI
# Install runpod
RUN pip install runpod requests

# Go back to the root
WORKDIR /



# Start container
EXPOSE 8848
CMD ["python3", "-u", "/runpod-volume/ComfyUI/main.py","--highvram","--disable-smart-memory", "--listen", "0.0.0.0", "--port", "8848"]