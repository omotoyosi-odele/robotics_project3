#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from geometry_msgs.msg import Twist
import math

class JetAutoRealWorld:
    def __init__(self):
        rospy.init_node('jetauto_real_world', anonymous=True)
        
        # Make sure this matches your real robot's topic!
        self.cmd_vel_pub = rospy.Publisher('/jetauto_controller/cmd_vel', Twist, queue_size=10)
        
        self.linear_speed = 0.2   # m/s
        self.angular_speed = 0.5  # rad/s
        self.rate = rospy.Rate(50)

        # ==========================================
        # 🛠️ CALIBRATION DIALS (TUNE THESE) 🛠️
        # ==========================================
        # If the robot falls short, increase the number (e.g., 1.10 for 10% more time).
        # If the robot goes too far, decrease it (e.g., 0.95).
        
        self.forward_tune = 1.0   # Multiplier for moving forward
        self.strafe_tune = 1.2    # Mecanum wheels slip a lot when strafing, usually needs more time
        self.turn_tune = 1.05     # Multiplier for rotating
        self.step5_tune = 1.1     # Multiplier for the advanced move & rotate step
        # ==========================================

    def stop(self):
        self.cmd_vel_pub.publish(Twist())
        rospy.sleep(0.5) # Let momentum settle

    def move_robot(self, v_x, v_y, omega, distance_or_angle, tune_multiplier):
        vel_msg = Twist()
        vel_msg.linear.x = v_x
        vel_msg.linear.y = v_y
        vel_msg.angular.z = omega

        # Calculate base duration
        if omega != 0:
            base_duration = abs(distance_or_angle / omega)
        else:
            speed = math.sqrt(v_x**2 + v_y**2)
            base_duration = distance_or_angle / speed

        # Apply real-world calibration
        actual_duration = base_duration * tune_multiplier

        start_time = rospy.Time.now().to_sec()
        while (rospy.Time.now().to_sec() - start_time) < actual_duration and not rospy.is_shutdown():
            self.cmd_vel_pub.publish(vel_msg)
            self.rate.sleep()

        self.stop()

    def move_and_rotate(self, distance, start_angle, end_angle, tune_multiplier):
        rospy.loginfo("Performing Advanced Step 5...")
        
        base_duration = distance / self.linear_speed
        actual_duration = base_duration * tune_multiplier
        
        total_angle_change = end_angle - start_angle
        omega = total_angle_change / actual_duration
        
        start_time = rospy.Time.now().to_sec()
        
        while (rospy.Time.now().to_sec() - start_time) < actual_duration and not rospy.is_shutdown():
            current_time = rospy.Time.now().to_sec() - start_time
            current_heading = start_angle + (omega * current_time)
            
            # Project Global South onto local frame
            vel_msg = Twist()
            vel_msg.linear.x = -self.linear_speed * math.sin(current_heading)
            vel_msg.linear.y = -self.linear_speed * math.cos(current_heading)
            vel_msg.angular.z = omega
            
            self.cmd_vel_pub.publish(vel_msg)
            self.rate.sleep()
            
        self.stop()

    def run_sequence(self):
        try:
            try:
                raw_input("Press Enter to begin Tuned Square Pattern...")
            except NameError:
                input("Press Enter to begin Tuned Square Pattern...")
        except SyntaxError:
            pass

        for i in range(2):
            rospy.loginfo("--- Starting Loop {}/2 ---".format(i+1))

            # STEP 1: Forward
            rospy.loginfo("Step 1: Move Forward")
            self.move_robot(self.linear_speed, 0, 0, 1.0, self.forward_tune)

            # STEP 2: Strafe Left
            rospy.loginfo("Step 2: Strafe Left")
            self.move_robot(0, self.linear_speed, 0, 1.0, self.strafe_tune)

            # STEP 3: Turn CW
            rospy.loginfo("Step 3: Turn CW 90 deg")
            self.move_robot(0, 0, -self.angular_speed, math.pi/2, self.turn_tune)

            # STEP 4: Strafe Right
            rospy.loginfo("Step 4: Strafe Right")
            self.move_robot(0, -self.linear_speed, 0, 1.0, self.strafe_tune)

            # STEP 5: Move South & Turn CCW
            rospy.loginfo("Step 5: Advanced Move & Rotate")
            self.move_and_rotate(1.0, -math.pi/2, 0.0, self.step5_tune)

        rospy.loginfo("Pattern Complete.")

if __name__ == '__main__':
    try:
        controller = JetAutoRealWorld()
        controller.run_sequence()
    except rospy.ROSInterruptException:
        pass
