FROM python:3.11-slim

# تثبيت الاعتمادات المكتبيّة للـ Graphics والمستندات
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    mupdf-tools \
    && rm -rf /var/lib/apt/lists/*
    
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    dpkg \
    libgl1 \
    libglib2.0-0 \
    xvfb \
    libfontconfig1 \
    libxrender1 \
    libxi6 \
    libxext6 \
    libfreetype6 \
    libxkbcommon0 \
    xkb-data \
    fuse \
    wget \
    libfuse2 \
    xauth \
    x11-utils \
    libxcb1 \
    libxcb-render0 \
    libxcb-shape0 \
    libxcb-xfixes0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libxcb-xkb1 \
    libdbus-1-3 \
    libsm6 \
    libice6 \
    x11-xserver-utils \
    libxcb-cursor0 \
    libxkbcommon-x11-0 \
    libxcb-util1 \
    && rm -rf /var/lib/apt/lists/*
    
# تحميل حزمة ODAFileConverter وتثبيتها بشكل إجباري
RUN wget -O /tmp/oda.deb "https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_lnxX64_8.3dll_27.1.deb" \
    && dpkg -i /tmp/oda.deb || apt-get install -f -y \
    && rm -rf /tmp/oda.deb \
    && cd /usr/lib/x86_64-linux-gnu \
    && ln -s libxcb-util.so.1 libxcb-util.so.0
    
# 3. ضبط متغيرات البيئة الخاصة بـ Qt تلقائياً داخل الحاوية
ENV QT_QPA_PLATFORM=xcb
ENV QT_QPA_PLATFORM_PLUGIN_PATH=/usr/share/ODAFileConverter/platforms
# إخفاء تحذيرات Qt غير الضارة عشان stderr يفضل نظيف تماماً
ENV XDG_RUNTIME_DIR=/tmp/runtime-root
ENV QT_LOGGING_RULES="*.debug=false;qt.qpa.*=false"

# 4. عمل Wrapper لـ ODAFileConverter ليعمل دائماً تحت xvfb-run
RUN if [ -f /usr/bin/ODAFileConverter ]; then \
        mv /usr/bin/ODAFileConverter /usr/bin/ODAFileConverter.bin && \
        echo '#!/bin/bash\nxvfb-run -a /usr/bin/ODAFileConverter.bin "$@"' > /usr/bin/ODAFileConverter && \
        chmod +x /usr/bin/ODAFileConverter; \
    fi
    
RUN mkdir -p /tmp/runtime-root && chmod 700 /tmp/runtime-root
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8003