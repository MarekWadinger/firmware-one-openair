# AirGradient reference models

Published by AirGradient, downloaded 2026-10-09, unmodified:

- `Lower Case 11AUG22.stl`, `Upper Case 11AUG22.stl`, `Cable Area 11AUG22.stl`, `Complete Assembly 11AUG22.stp`
  from https://www.airgradient.com/documents/diy-pro/diy_pro_3d.zip (3D-printable enclosure, fits the ONE V9 PCB)
- `airgradient-stand-stl.stl` from https://www.airgradient.com/documents/diy-pro/airgradient-stand-stl.zip

The CO box generator cuts its hook profile from the stand model:

```
.venv/bin/python docs/3d/co_sensor_box.py docs/3d/reference/airgradient-stand-stl.stl
```
