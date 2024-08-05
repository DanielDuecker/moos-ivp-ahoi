import numpy as np
from ahoi_ekf_base import *


def main_sim():
    auv_dim_state = 3
    ahoi_dim_meas = 1
    x0_est = np.array([10,10,1])
    p_mat_est = np.diag([0.1,0.1,0.1])

    process_noise_mat = np.diag([0.1, 0.1, 0.1])
    meas_noise_val = 0.5

    ahoi_ekf = EKF_Node(auv_dim_state, ahoi_dim_meas, 
                        meas_noise_val, process_noise_mat, 
                        x0_est, p_mat_est)

    anchor_list = np.array([[0, 0, 0],
                           [20, 20, 0],
                           [0, 20, 0]])
    x_real = np.array([5,5,1])

    for i in range(20):
        print(f"[{i}] est position {ahoi_ekf.get_x_est()}")
        ahoi_ekf.predict(dt_sim=1)
        
        for anchor_pos in anchor_list:
            dist_real = np.sqrt((x_real[0] - anchor_pos[0])**2 +
                       (x_real[1] - anchor_pos[1])**2 + (x_real[2] - anchor_pos[2])**2)
            ahoi_ekf.measurement_update(dist_meas=dist_real, anchor_pos=anchor_pos, w_mat_dist=meas_noise_val)
            time.sleep(0.1)

if __name__ == '__main__':
    main_sim()