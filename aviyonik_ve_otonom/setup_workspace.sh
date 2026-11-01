#!/usr/bin/env bash
# METUAV DBF 2027 Aviyonik Çalışma Alanı Kurulum Betiği
set -e

echo "=== [METUAV DBF 2027] ROS 2 Humble Çalışma Alanı Kuruluyor ==="

# ROS2 Humble kaynağı
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
    echo "[OK] ROS 2 Humble ortamı yüklendi."
else
    echo "[UYARI] /opt/ros/humble/setup.bash bulunamadı. ROS 2 kurulu olduğundan emin olun."
fi

# Bağımlılıkları güncelle
if command -v rosdep &> /dev/null; then
    echo "[+] rosdep bağımlılıkları kontrol ediliyor..."
    rosdep update || true
    rosdep install --from-paths src --ignore-src -r -y || true
fi

# Python bağımlılıklarını kur
if [ -f "src/edge_ai_vision/requirements.txt" ]; then
    echo "[+] Python bağımlılıkları yükleniyor..."
    pip install -r src/edge_ai_vision/requirements.txt
fi

if [ -f "src/telemetri/requirements.txt" ]; then
    pip install -r src/telemetri/requirements.txt
fi

echo "[+] colcon derleme başlatılıyor..."
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

if [ -f "install/setup.bash" ]; then
    source install/setup.bash
    echo "=== [METUAV DBF 2027] Kurulum Başarıyla Tamamlandı! ==="
fi
