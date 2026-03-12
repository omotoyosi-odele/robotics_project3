#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import math
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import tf.transformations

class JetAutoClosedLoop:
    def __init__(self):
        rospy.init_node('jetauto_closed_loop', anonymous=True)
        
        # Publishers and Subscribers
        self.cmd_vel_pub = rospy.Publisher('/jetauto_controller/cmd_vel', Twist, queue_size=10)
        self.odom_sub = rospy.Subscriber('/odom', Odometry, self.odom_callback)
        
        # Robot's current state
        self.current_x = None
        self.current_y = None
        self.current_yaw = None
        
        # Speed limits
        self.max_linear_speed = 0.3
        self.max_angular_speed = 0.8
        self.rate = rospy.Rate(50)

        # Wait for the first odometry reading before starting
        rospy.loginfo("Waiting for /odom data...")
        while self.current_x is None and not rospy.is_shutdown():
            self.rate.sleep()
        rospy.loginfo("Odometry received! Ready.")

    def odom_callback(self, msg):
        """Updates the robot's exact position every time /odom publishes."""
        self.current_x = msg.pose.pose.position.x
        self.current_y = msg.pose.pose.position.y
        
        # Odometry gives rotation in Quaternions (complex 3D math).
        # We convert it to Euler angles (roll, pitch, yaw) to get a simple heading.
        q = msg.pose.pose.orientation
        quaternion = (q.x, q.y, q.z, q.w)
        euler = tf.transformations.euler_from_quaternion(quaternion)
        self.current_yaw = euler[2] # Yaw is rotation around the Z-axis

    def normalize_angle(self, angle):
        """Ensures the angle stays between -PI and +PI. (Avoids spinning 360 unnecessarily)"""
        return math.atan2(math.sin(angle), math.cos(angle))

    def go_to_pose(self, target_x, target_y, target_yaw):
        """
        Universal closed-loop movement function.
        Drives the robot until it exactly reaches the target coordinates.
        """
        #rospy.loginfo(f"Moving to: X={target_x}, Y={target_y}, Yaw={math.degrees(target_yaw)}°")
        rospy.loginfo("Moving to: X={}, Y={}, Yaw={}".format(target_x, target_y, math.degrees(target_yaw)))
        
        while not rospy.is_shutdown():
            # 1. Calculate the Error (Difference between target and current state)
            e_x = target_x - self.current_x
            e_y = target_y - self.current_y
            e_yaw = self.normalize_angle(target_yaw - self.current_yaw)
            
            # Distance left to travel
            distance_error = math.sqrt(e_x**2 + e_y**2)
            
            # 2. Check if we arrived (within a 2cm and 2 degree tolerance)
            if distance_error < 0.02 and abs(e_yaw) < 0.035:
                break
                
            # 3. Proportional Control (P-Controller)
            # The further away we are, the faster we go. As we get close, we slow down.
            Kp_linear = 0.8  
            Kp_angular = 1.5 
            
            # Global velocities required to close the gap
            V_X_global = Kp_linear * e_x
            V_Y_global = Kp_linear * e_y
            omega = Kp_angular * e_yaw
            
            # Cap the global speeds to our maximum limits
            current_speed = math.sqrt(V_X_global**2 + V_Y_global**2)
            if current_speed > self.max_linear_speed:
                V_X_global = (V_X_global / current_speed) * self.max_linear_speed
                V_Y_global = (V_Y_global / current_speed) * self.max_linear_speed
                
            if abs(omega) > self.max_angular_speed:
                omega = math.copysign(self.max_angular_speed, omega)
                
            # 4. Transform Global velocities to Local Robot velocities
            # Since the robot might be facing sideways, we must rotate the global vector
            # into the robot's local frame so it knows which wheels to spin.
            v_x_local = V_X_global * math.cos(self.current_yaw) + V_Y_global * math.sin(self.current_yaw)
            v_y_local = -V_X_global * math.sin(self.current_yaw) + V_Y_global * math.cos(self.current_yaw)
            
            # 5. Publish to wheels
            vel_msg = Twist()
            vel_msg.linear.x = v_x_local
            vel_msg.linear.y = v_y_local
            vel_msg.angular.z = omega
            self.cmd_vel_pub.publish(vel_msg)
            
            self.rate.sleep()
            
        # Stop completely when arrived
        self.cmd_vel_pub.publish(Twist())
        rospy.sleep(0.5)

    def run_sequence(self):
        #try:
            #try:
                #input("Press Enter to begin PERFECT Square Pattern...")
            #except NameError:
                #raw_input("Press Enter to begin PERFECT Square Pattern...")
        #except EOFError:
            #pass
    	try:
            try:
                # Try Python 2 first
                raw_input("Press Enter to begin PERFECT Square Pattern...")
            except NameError:
                # Fallback for Python 3
                input("Press Enter to begin PERFECT Square Pattern...")
        except SyntaxError:
            pass

        # We record our starting position so the 1-meter square is relative to where
        # the robot actually sits in Gazebo, rather than an absolute (0,0) world origin.
        start_x = self.current_x
        start_y = self.current_y
        start_yaw = self.current_yaw

        for i in range(2):
            #rospy.loginfo(f"--- Starting Loop {i+1}/2 ---")
            rospy.loginfo("--- Starting Loop {}/2 ---".format(i+1))

            # STEP 1: (1, 0, 0°) relative to start
            self.go_to_pose(start_x + 1.0, start_y + 0.0, start_yaw + 0.0)

            # STEP 2: (1, 1, 0°) relative to start
            self.go_to_pose(start_x + 1.0, start_y + 1.0, start_yaw + 0.0)

            # STEP 3: (1, 1, -90°) relative to start
            self.go_to_pose(start_x + 1.0, start_y + 1.0, start_yaw - math.pi/2)

            # STEP 4: (0, 1, -90°) relative to start
            self.go_to_pose(start_x + 0.0, start_y + 1.0, start_yaw - math.pi/2)

            # STEP 5: (0, 0, 0°) Return to exact start position and orientation
            self.go_to_pose(start_x, start_y, start_yaw)

        rospy.loginfo("Pattern Complete.")

if __name__ == '__main__':
    try:
        controller = JetAutoClosedLoop()
        controller.run_sequence()
    except rospy.ROSInterruptException:
        pass
