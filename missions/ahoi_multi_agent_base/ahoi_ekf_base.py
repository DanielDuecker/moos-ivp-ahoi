# EKF based on https://github.com/HippoCampusRobotics/mu_auv_localization/blob/main/src/mu_auv_localization/ekf_class.py

from __future__ import print_function
import numpy as np
import time
#import rospy
import threading


class ExtendedKalmanFilter(object):
    def __init__(self, dim_state, dim_meas, measurement_model, process_model,
                 x0, p0_mat):
        self.dim_state = dim_state
        self.dim_meas = dim_meas
        self._x_est_0 = x0
        self._x_est = self._x_est_0
        self._x_est_last = self._x_est
        #self._last_time_stamp_update = rospy.get_time()
        #self._last_time_stamp_prediction = rospy.get_time()
        self._p0_mat = p0_mat
        self._p_mat = self._p0_mat
        self.lock = threading.Lock()

        self.process_model = process_model
        self.measurement_model = measurement_model

    def get_x_est(self):
        return np.copy(self._x_est)

    def get_x_est_0(self):
        return np.copy(self._x_est_0)

    def get_p_mat(self):
        return np.copy(self._p_mat)

    def get_x_est_last(self):
        return np.copy(self._x_est_last)

    def reset(self, x_est_0=None, p0_mat=None):
        if x_est_0:
            self._x_est = x_est_0
        else:
            self._x_est = self._x_est_0
        if p0_mat:
            self._p_mat = p0_mat
        else:
            self._p_mat = self._p0_mat

    def predict(self, dt):
        self._x_est_last = self._x_est
        self._x_est = self.process_model.f(self.get_x_est(), dt)
        a_mat = self.process_model.f_jacobian(self.get_x_est(), dt)
        self._p_mat = np.matmul(np.matmul(a_mat, self.get_p_mat()),
                                a_mat.transpose()) + self.process_model.V

        # # reset EKF if unrealistic values
        # if self.get_x_est()[0] > 5 or self.get_x_est()[1] > 5:
        #     print('Resetting EKF: x or y value outside tank')
        #     self.reset()
        # # TODO find better values
        # elif not np.all(np.isfinite(self.get_x_est())):
        #     print('Resetting EKF: unrealistically high value')
        #     print('x: ', self.get_x_est())
        #     self.reset()

        return True
    
    def update_dist_data(self, measurements, anchor_pos, w_mat_dist):
        self._x_est_last = self._x_est
        
        z_est_anchor = self.measurement_model.h_dist_anchor_data(
            self.get_x_est(), anchor_pos)
        h_mat_anchor = self.measurement_model.h_jacobian_dist_anchor_data(
            self.get_x_est(), anchor_pos)
        y_vision =  measurements - z_est_anchor

        self._x_est, self._p_mat = self._update(self.get_x_est(),
                                                self.get_p_mat(), y_vision,
                                                h_mat_anchor, w_mat_dist)

        return True

    def update_vision_data(self, measurements, detected_tags):
        # measurement is: dist, yaw to each tag

        self._x_est_last = self._x_est
        z_est_vision = self.measurement_model.h_vision_data(
            self.get_x_est(), detected_tags)
        h_mat_vision = self.measurement_model.h_jacobian_vision_data(
            self.get_x_est(), detected_tags)
        w_mat_vision = self.measurement_model.vision_dynamic_meas_model(
            self.get_x_est(), measurements, detected_tags)

        y_vision = measurements - z_est_vision
        # wrap yaw innovation (every second entry) so it is between -pi and pi
        y_vision[1::2] = np.arctan2(np.sin(y_vision[1::2]),
                                    np.cos(y_vision[1::2]))

        self._x_est, self._p_mat = self._update(self.get_x_est(),
                                                self.get_p_mat(), y_vision,
                                                h_mat_vision, w_mat_vision)

        return True

    def update_orientation_data(self, measurements):
        # measurement is: roll, pitch from /mavros/local_position/pose

        z_est_orient = self.measurement_model.h_orientation_data(
            self.get_x_est())
        h_mat_orient = self.measurement_model.h_jacobian_orientation_data()

        y_orient = measurements - z_est_orient
        # wrap angle innovations between -pi and pi
        y_orient = np.arctan2(np.sin(y_orient), np.cos(y_orient))

        self._x_est, self._p_mat = self._update(
            self.get_x_est(), self.get_p_mat(), y_orient, h_mat_orient,
            self.measurement_model.w_mat_orientation)

        return True

    def update_imu_data(self, measurements, w_mat_imu):
        # measurement is either: body rates + lin. acceleration
        #               or: only body rates

        # check which measurements we're using:
        if measurements.shape[0] == 3:
            # only using angular velocities
            using_lin_acc = False
        elif measurements.shape[0] == 6:
            using_lin_acc = True
        else:
            print("IMU measurement has unexpected size!")
            using_lin_acc = False

        z_est_imu = self.measurement_model.h_imu_data(self.get_x_est(),
                                                      using_lin_acc)
        h_mat_imu = self.measurement_model.h_jacobian_imu_data(using_lin_acc)
        y_imu = measurements - z_est_imu
        self._x_est, self._p_mat = self._update(self.get_x_est(),
                                                self.get_p_mat(), y_imu,
                                                h_mat_imu, w_mat_imu)

        return True

    def _update(self, x_est, p_mat, y, h_mat, w_mat):
        """ helper function for general update """
        
        # compute K gain
        tmp = np.matmul(np.matmul(h_mat, p_mat), h_mat.transpose()) + w_mat
        k_mat = np.matmul(np.matmul(p_mat, h_mat.transpose()),
                          np.linalg.inv(tmp))
        
        # update state
        if np.isscalar(y):
            tmp2 = k_mat*y
            x_est = x_est + tmp2[:,0]
        else:
            x_est = x_est + np.matmul(k_mat, y)

        # update covariance
        p_tmp = np.eye(self.dim_state) - np.matmul(k_mat, h_mat)
        p_mat = np.matmul(p_tmp, p_mat)
        # print('P_m diag: ', np.diag(self.get_p_mat()))
        return x_est, p_mat
    


# ====================================================
# based on https://github.com/HippoCampusRobotics/mu_auv_localization/blob/main/src/mu_auv_localization/process_model_class.py

class ProcessModel(object):
    """ Simple process model: no prediction """
    def __init__(self, dim_state, dim_meas, V):
        self._dim_state = dim_state
        self._dim_meas = dim_meas
        self.V = V  # process noise

    def f(self, x_est, dt):
        x_next = np.copy(x_est)
        return x_next

    def f_jacobian(self, x_est, dt):
        A = np.eye(self._dim_state)
        return A  # dim [dim_state X dim_state]
    
# ====================================================
# based on https://github.com/HippoCampusRobotics/mu_auv_localization/blob/main/src/mu_auv_localization/meas_model_class.py


class MeasurementModelDistances(object):
    def __init__(self, dim_state, dim_meas, w_mat_dist):
    #def __init__(self, dim_state, dim_meas, w_mat_vision, c_penalty_dist,
    #             c_penalty_yaw, w_mat_orientation):
        self._dim_state = dim_state
        self._dim_meas = dim_meas
        self._w_mat_dist = w_mat_dist   # measurement noise

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


    def get_dist(self, x_est, ref_pos):
        # dist = sqrt((x - x_tag) ^ 2 + (y - y_tag) ^ 2 + (z - z_tag) ^ 2)
        dist = np.sqrt((x_est[0] - ref_pos[0])**2 +
                       (x_est[1] - ref_pos[1])**2 + 
                       (x_est[2] - ref_pos[2])**2)
        return dist


class EKF_Node():
    def __init__(self, auv_dim_state, ahoi_dim_meas, meas_noise, process_noise, x0_est, p_mat_est) -> None:

        # init EKF
        self.ekf = ExtendedKalmanFilter(dim_state=auv_dim_state, dim_meas=ahoi_dim_meas, 
                                    measurement_model=MeasurementModelDistances(dim_state=auv_dim_state,dim_meas=ahoi_dim_meas,w_mat_dist=meas_noise), 
                                    process_model=ProcessModel(dim_state=auv_dim_state,dim_meas=ahoi_dim_meas, V=process_noise),
                                    x0 = x0_est, 
                                    p0_mat = p_mat_est)
        self._last_predict_time = time.time()
    
    def get_x_est(self):
        return self.ekf.get_x_est()

    def get_p_mat(self):
        return self.ekf.get_p_mat()
    
    def predict(self, dt_sim=None):
        time_now = time.time()

        if dt_sim !=None:
            dt = dt_sim
        else:
            dt = time_now - self._last_predict_time
            
        self.ekf.predict(dt)

        self._last_predict_time = time_now
        return True

    def measurement_update(self, dist_meas, anchor_pos, w_mat_dist):
        self.ekf.update_dist_data(measurements=dist_meas, anchor_pos=anchor_pos,w_mat_dist=w_mat_dist)
