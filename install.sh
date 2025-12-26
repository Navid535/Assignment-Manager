#!/bin/bash

mkdir -p ~/.local/bin
cp AssignmentManager.bin ~/.local/bin/

mkdir -p ~/.local/share/icons
cp icons/app_icon.png ~/.local/share/icons/assignment_manager.png

cat <<EOF > ~/.local/share/applications/AssignmentManager.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Assignment Manager
Exec=$HOME/.local/bin/AssignmentManager.bin
Icon=$HOME/.local/share/icons/assignment_manager.png
Terminal=false
Categories=Utility;
EOF

chmod +x ~/.local/share/applications/AssignmentManager.desktop

echo "نصب با موفقیت انجام شد! حالا می‌توانید برنامه را در لیست اپلیکیشن‌های سیستم پیدا کنید."
