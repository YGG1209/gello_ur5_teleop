# GELLO Teleoperation for UR5 Robot Arm

## Quick Start

```bash
git clone https://github.com/wuphilipp/gello_software.git
git clone https://github.com/YGG1209/gello_ur5_teleop.git
```

Copy the gello_ur5_teleop.py file from the gello_ur5_teleop repository into the scripts directory within the gello_software repository.

## Installation
## Virtual Environment Setup

```bash
conda create -n gello_software python=3.11
conda activate gello_software 
cd gello_software
pip install -r requirements.txt
pip install -e .
pip install -e third_party/DynamixelSDK/python
pip install numpy
pip install ur_rtde
```
