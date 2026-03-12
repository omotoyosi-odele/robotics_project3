# JetAuto Square Pattern Controller

This ROS package provides control scripts to navigate a JetAuto robot (equipped with Mecanum wheels) through a precise 1-meter square pattern. The project explores both **open-loop** (time-based) and **closed-loop** (odometry-based) control strategies, highlighting the differences between simulated environments (Gazebo) and physical hardware.

## Movement Pattern
The robot executes the following sequence twice upon receiving user input:
1. **Move Forward:** 1 meter.
2. **Strafe Left:** 1 meter (without turning).
3. **Turn Clockwise:** 90 degrees in place.
4. **Strafe Right:** 1 meter.
5. **Advanced Holonomic Move:** Move Global South 1 meter while simultaneously rotating Counter-Clockwise 90 degrees to return to the exact starting position and orientation.

## Prerequisites
* ROS 1 (Melodic / Noetic)
* Python 2.7 or Python 3 (Scripts are written to be compatible with both)
* `jetauto_description` and `jetauto_controller` packages (for physical robot or Gazebo simulation)

## Installation & Setup

1. **Clone/Place the package** into your Catkin workspace's `src` folder:
   ```bash
   cd ~/ros_ws/src
   # Ensure the folder is named square_jetauto_control

```

2. **Build the workspace:**
```bash
cd ~/ros_ws
catkin_make
source devel/setup.bash

```


3. **Make the scripts executable:**
```bash
chmod +x ~/ros_ws/src/square_jetauto_control/scripts/*.py

```



## Scripts Included

### 1. `jetauto_closed_loop.py` (Best for Gazebo Simulation)

Uses Proportional (P) control and subscribes to the `/odom` topic to calculate exact positions and headings.

* **Why use this?** In Gazebo, odometry is mathematically perfect. This script continuously corrects its trajectory, resulting in a flawless 1-meter square.
* **Topics Used:** Subscribes to `/odom` (or `/jetauto_controller/odom`), Publishes to `/cmd_vel` (or `/jetauto_controller/cmd_vel`).

### 2. `jetauto_open_loop.py` (Best for Physical Robot)

A time-based kinematic controller. It calculates the necessary velocities ($v_x, v_y, \omega_z$) and runs them for a specific duration.

* **Why use this?** On the physical robot, Mecanum wheels slip against the floor. This slip causes internal wheel encoders (odometry) to drift, failing closed-loop scripts. This open-loop script includes **Calibration Dials** (multipliers) at the top of the code to manually tune the timing for real-world friction and battery voltage.

## How to Run

### Running in Gazebo (Simulation)

1. Launch your Gazebo environment (make sure the simulation is **unpaused**):
```bash
roslaunch jetauto_gazebo jetauto_world.launch  # (Or your specific launch command)

```


2. In a new terminal, run the closed-loop script:
```bash
rosrun square_jetauto_control jetauto_closed_loop.py

```


3. Press `Enter` when prompted in the terminal to begin the sequence.

### Running on the Physical Robot

1. SSH into the JetAuto robot and launch the base hardware controllers:
```bash
roslaunch jetauto_controller jetauto_controller.launch

```


2. In a new terminal, run the tuned open-loop script:
```bash
rosrun square_jetauto_control jetauto_open_loop.py

```


3. *Note: If the robot falls short or turns too far, open `jetauto_open_loop.py` and adjust the `tune` variables at the top of the class, then run again.*

## Troubleshooting

* **Script says "Waiting for /odom data..." forever:**
* Check if your simulation is paused (simulated clock is frozen).
* Check if your topic names match. Run `rostopic list` to see if your robot uses `/odom` or `/jetauto_controller/odom`, and update the script accordingly.


* **Robot doesn't move but the script says it is running:**
* Verify the velocity publisher topic. Change `/cmd_vel` to `/jetauto_controller/cmd_vel` in the Python script to match the robot's hardware driver.


* **SyntaxError / TF Import Error:**
* Ensure the shebang at the top of the file is `#!/usr/bin/env python` and includes `# -*- coding: utf-8 -*-` to handle ROS's default Python 2 environment smoothly.
