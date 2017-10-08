#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint

import math
from tf.transformations import euler_from_quaternion

'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 200 # Number of waypoints we will publish. You can change this number
ONEMPH = 0.44704

class WaypointUpdater(object):
    def __init__(self):
        rospy.init_node('waypoint_updater')

        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        # TODO: Add a subscriber for /traffic_waypoint and /obstacle_waypoint below
		#rospy.Subscriber('/traffic_waypoint', Int32, self.traffic_cb)
		#rospy.Subscriber('/obstacle_waypoint', Int32, self.obstacle_cb)


        self.final_waypoints_pub = rospy.Publisher('final_waypoints', Lane, queue_size=1)

        # TODO: Add other member variables you need below
        self.waypoints = None
        self.pose = None
        self.max_vel = 20 * ONEMPH
        self.dt = 0.11
        self.min_dist_ahead = self.max_vel * self.dt

        rospy.Timer(rospy.Duration(self.dt), self.loop)
        rospy.spin()

    def loop(self, event):
        if (self.pose is not None and self.waypoints is not None):
            car_x = self.pose.position.x
            car_y = self.pose.position.y
            car_z = self.pose.position.z
            car_o = self.pose.orientation
            rospy.loginfo("current pose (%s, %s)", car_x, car_y)

            car_q = (car_o.x, car_o.y, car_o.z, car_o.w)
            car_roll, car_pitch, car_yaw = euler_from_quaternion(car_q)

            closest_wp = (float('inf'), -1)
            for i in range(len(self.waypoints)):
                wp = self.waypoints[i]
                wp_x = wp.pose.pose.position.x
                wp_y = wp.pose.pose.position.y

                is_ahead = ((wp_x - car_x)*math.cos(car_yaw) + (wp_y - car_y)*math.sin(car_yaw)) > 0.0      
                if(not is_ahead):
                     continue
                
                
                dist = math.sqrt((car_x - wp_x)**2 + (car_y - wp_y)**2)
                if dist < closest_wp[0]:
                    closest_wp = (dist, i)
            
            idx_begin = closest_wp[1]
            idx_end = min(idx_begin + LOOKAHEAD_WPS, len(self.waypoints))
            wps = self.waypoints[idx_begin:idx_end]

            for i in range(len(wps)):
                waypoint_velocity = wps[i].twist.twist.linear.x
                target_velocity = min(waypoint_velocity, self.max_vel)
                wps[i].twist.twist.linear.x = target_velocity
            
            lane = Lane()
            lane.waypoints = wps

            self.final_waypoints_pub.publish(lane)

    def pose_cb(self, msg):
        self.pose = msg.pose

    def waypoints_cb(self, msg):
        # TODO: Implement
        self.waypoints = msg.waypoints

    def traffic_cb(self, msg):
        # TODO: Callback for /traffic_waypoint message. Implement
        pass

    def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
        pass

    def get_waypoint_velocity(self, waypoint):
        return waypoint.twist.twist.linear.x

    def set_waypoint_velocity(self, waypoints, waypoint, velocity):
        waypoints[waypoint].twist.twist.linear.x = velocity

    def distance(self, waypoints, wp1, wp2):
        dist = 0
        dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
        for i in range(wp1, wp2+1):
            dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
            wp1 = i
        return dist


if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')
