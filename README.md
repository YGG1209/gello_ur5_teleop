# GELLO Teleoperation for UR5 Robot Arm

## Quick Start

```bash
git clone https://github.com/wuphilipp/gello_software.git
git clone https://github.com/YGG1209/gello_ur5_teleop.git
```

Copy the gello_ur5_teleop.py file from the gello_ur5_teleop repository into the scripts directory within the gello_software repository.

## Installation
## Conda Environment Setup

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

## Note:

Before running gello_ur5_teleop.py, you must configure the GELLO hardware parameters within the code, including:
Servo IDs、Initial Offsets、Rotation Directions、Gripper Parameters
(Note: This code does not control the gripper directly. You will need to add your own implementation based on your specific hardware setup.)

This project mainly focuses on the basic teleoperation framework for Gello teleoperation real machine UR5 and UR5 data acquisition.

For more detailed information, please refer to: https://github.com/wuphilipp/gello_software.
