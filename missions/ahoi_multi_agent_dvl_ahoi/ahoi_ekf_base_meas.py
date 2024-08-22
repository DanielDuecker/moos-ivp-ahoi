from __future__ import print_function
import numpy as np



# ====================================================
# based on https://github.com/HippoCampusRobotics/mu_auv_localization/blob/main/src/mu_auv_localization/meas_model_class.py

"""
Different measurement models for the EKF for the visual localization
    - Distances: using distance and yaw angle to tag as measurement
    - ...

EKF state: [x, y, z, roll, pitch, yaw, dx, dy, dz, droll, dpitch, dyaw]
(linear and angular velocities in body frame)
"""

class MeasurementModelDistances(object):
    def __init__(self, dim_state, dim_meas):


        # measurement noise w_mat_list - list of meas noise matrices [ahoi_mat, yaw_mat, imu_mat,...]

        self._dim_state = dim_state
        self._dim_meas = dim_meas
        # self._w_mat_dist = w_mat_list[0]        # ahoi measurement noise
        # self._w_mat_yaw = w_mat_list[1]         # yaw measurement noise
        # #self._w_mat_orientation = w_mat_list[2] # roll/pitch measurement noise

        # self._w_mat_vision_static = w_mat_vision
        # self._c_penalty_dist = c_penalty_dist
        # self._c_penalty_yaw = c_penalty_yaw
        # self.w_mat_orientation = w_mat_orientation

    def h_dist_anchor_data(self, x_est, anchor_pos_3d):
        # measurement is: distance to anchor
        z_est = self.get_dist(x_est, anchor_pos_3d)

        return z_est  # dim [1 X 1]
    
    def h_jacobian_dist_anchor_data(self, x_est, anchor_pos_3d):
        
        h_mat = np.zeros((self._dim_meas, self._dim_state))
        

        dist = self.get_dist(x_est, anchor_pos_3d)

        # dh /dx = 1/2 * (dist ^2)^(-1/2) * (2 * (x1 - t1) * 1)
        h_jac_x = (x_est[0] - anchor_pos_3d[0]) / dist
        # dh /dy
        h_jac_y = (x_est[1] - anchor_pos_3d[1]) / dist
        # dh /dz
        h_jac_z = (x_est[2] - anchor_pos_3d[2]) / dist
        ## dh /dyaw
        #h_jac_yaw = 1.0

        h_mat[0, 0:3] = [h_jac_x, h_jac_y, h_jac_z]
        #h_mat[self._dim_meas * i + 1, 5] = h_jac_yaw
        # all other derivatives are zero

        return h_mat  # dim [1x3]
    
    def h_yaw_data(self, x_est):
        # measurement is: yaw
        z_est = np.array([x_est[5]]).reshape((-1, 1))
        return z_est  # dim: [1 X 1]

    def h_jacobian_yaw_data(self):
        h_mat = np.zeros((1, self._dim_state))
        # all derivatives zero except for roll, pitch:
        h_mat[0, 5] = 1.0  # dh /dyaw
        
        return h_mat  # dim [1 X dim_state]

    def h_orientation_data(self, x_est):
        # measurement is: roll, pitch from /mavros/local_position/pose
        z_est = np.array([x_est[3], x_est[4]]).reshape((-1, 1))
        return z_est  # dim: [2 X 1]

    def h_jacobian_orientation_data(self):
        h_mat = np.zeros((2, self._dim_state))
        # all derivatives zero except for roll, pitch:
        h_mat[0, 3] = 1.0  # dh /droll
        h_mat[1, 4] = 1.0  # dh/ dpitch
        return h_mat  # dim [2 X dim_state]

    def h_imu_data(self, x_est, using_lin_acc=False):
        if not using_lin_acc:
            # measurement is: roll rate, pitch rate, yaw rate
            z_est = np.array([x_est[9], x_est[10], x_est[11]]).reshape((-1, 1))
        else:
            # measurement is: angular velocities and linear accelerations
            print(f"[EKF] Using linear acceleration measurements from IMU!" +
                "Not implemented yet")
            
        return z_est

    def h_jacobian_imu_data(self, using_lin_acc=False):
        if not using_lin_acc:
            h_mat = np.zeros((3, self._dim_state))
            # all derivatives zero except for body rates
            h_mat[0, 9] = 1.0
            h_mat[1, 10] = 1.0
            h_mat[2, 11] = 1.0
        else:
            # rospy.logfatal(
            #     "[%s] Using linear acceleration measurements from IMU! " +
            #     "Not implemented yet", rospy.get_name())
            pass

        return h_mat  # dim [3 X dim_state]


    def get_dist(self, x_est, ref_pos):
        # dist = sqrt((x - x_tag) ^ 2 + (y - y_tag) ^ 2 + (z - z_tag) ^ 2)
        dist = np.sqrt((x_est[0] - ref_pos[0])**2 +
                       (x_est[1] - ref_pos[1])**2 + 
                       (x_est[2] - ref_pos[2])**2)
        return dist

