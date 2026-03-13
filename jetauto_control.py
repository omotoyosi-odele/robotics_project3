#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import Twist
import sys
import math

class JetAutoController:
    def __init__(self):
        # Initialize the ROS node
        rospy.init_node('jetauto_control', anonymous=True)
        
        # --- IMPORTANT: Ensure this matches your robot's topic ---
        # If your robot uses /jetauto/cmd_vel, change it here!
        self.cmd_vel_pub = rospy.Publisher('/jetauto_controller/cmd_vel', Twist, queue_size=10)
        
        # Define movement speeds
        self.linear_speed = 0.2   # m/s
        self.angular_speed = 0.5  # rad/s
        self.rate = rospy.Rate(50) # 50Hz for smoother advanced control

    def stop(self):
        """Stops the robot by publishing zero velocity."""
        vel_msg = Twist()
        self.cmd_vel_pub.publish(vel_msg)
        rospy.sleep(1.0) # Pause briefly between steps

    def move_robot(self, v_x, v_y, omega, distance_or_angle):
        """
        Standard open-loop movement for Steps 1-4.
        """
        vel_msg = Twist()
        vel_msg.linear.x = v_x
        vel_msg.linear.y = v_y
        vel_msg.angular.z = omega

        # Calculate duration: Time = Distance / Speed
        if omega != 0:
            duration = abs(distance_or_angle / omega)
        else:
            speed = math.sqrt(v_x**2 + v_y**2)
            duration = distance_or_angle / speed

        # Publish the velocity command for the calculated duration
        start_time = rospy.Time.now().to_sec()
        while (rospy.Time.now().to_sec() - start_time) < duration:
            self.cmd_vel_pub.publish(vel_msg)
            self.rate.sleep()

        self.stop()

    def move_and_rotate(self, distance, start_angle, end_angle):
        """
        Advanced Step 5: Moves the robot in a straight global line (South)
        while simultaneously rotating the robot body.
        """
        rospy.loginfo("Performing Advanced Step 5: Move & Rotate")
        
        linear_speed = 0.2
        duration = distance / linear_speed
        
        total_angle_change = end_angle - start_angle
        omega = total_angle_change / duration
        
        start_time = rospy.Time.now().to_sec()
        
        while (rospy.Time.now().to_sec() - start_time) < duration:
            current_time = rospy.Time.now().to_sec() - start_time
            
            # Calculate current heading
            current_heading = start_angle + (omega * current_time)
            
            # MATH: To move Global South while rotating:
            # v_x (forward) = -Speed * sin(theta)
            # v_y (left)    = -Speed * cos(theta)
            
            vel_x = -linear_speed * math.sin(current_heading)
            vel_y = -linear_speed * math.cos(current_heading)
            
            vel_msg = Twist()
            vel_msg.linear.x = vel_x
            vel_msg.linear.y = vel_y
            vel_msg.angular.z = omega
            self.cmd_vel_pub.publish(vel_msg)
            
            self.rate.sleep()
            
        self.stop()

    def run_sequence(self):
        print("Ready to start Square Pattern.")
        try:
            try:
                input("Press Enter to begin...")
            except NameError:
                raw_input("Press Enter to begin...")
        except EOFError:
            pass

        # Repeat the pattern twice
        for i in range(2):
            rospy.loginfo(f"--- Starting Loop {i+1}/2 ---")

            # STEP 1: Move Forward (0,0) -> (1,0)
            rospy.loginfo("Step 1: Move Forward")
            self.move_robot(v_x=self.linear_speed, v_y=0, omega=0, distance_or_angle=1.0)

            # STEP 2: Move Sideways Left (1,0) -> (1,1)
            rospy.loginfo("Step 2: Move Sideways Left")
            self.move_robot(v_x=0, v_y=self.linear_speed, omega=0, distance_or_angle=1.0)

            # STEP 3: Turn Clockwise (1,1, 0 deg) -> (1,1, -90 deg)
            rospy.loginfo("Step 3: Turn Clockwise 90 deg")
            self.move_robot(v_x=0, v_y=0, omega=-self.angular_speed, distance_or_angle=math.pi/2)

            # STEP 4: Move Sideways Right (1,1, -90 deg) -> (0,1, -90 deg)
            rospy.loginfo("Step 4: Move Sideways Right")
            self.move_robot(v_x=0, v_y=-self.linear_speed, omega=0, distance_or_angle=1.0)

            # STEP 5 (Advanced): Move South while turning CCW
            # Target: Move 1m South, Rotate -90 to 0
            rospy.loginfo("Step 5: Move Forward and Turn (Advanced)")
            start_rad = -math.pi/2
            end_rad = 0.0
            self.move_and_rotate(distance=1.0, start_angle=start_rad, end_angle=end_rad)

        rospy.loginfo("Pattern Complete.")

if __name__ == '__main__':
    try:
        controller = JetAutoController()
        controller.run_sequence()
    except rospy.ROSInterruptException:
        pass
