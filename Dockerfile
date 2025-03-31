FROM ubuntu:22.04

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ffmpeg \
        gir1.2-gstreamer-1.0 \
        gir1.2-gst-plugins-base-1.0 \
        libgstreamer1.0-0 \
        gstreamer1.0-libav \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-tools \
        python3 \
        python3-gi \
        python3-pip \
 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /voctomix
WORKDIR /voctomix
RUN uv pip install --system --requirements pyproject.toml
ENTRYPOINT ["python3", "-m", "voctocore"]
