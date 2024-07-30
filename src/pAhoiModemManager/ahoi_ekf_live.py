import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from ahoi_ekf_base import *

class EKFPlotter:
    def __init__(self, anchor_list, anchor_id_list, show_last_n=10):
        self.anchor_list = anchor_list
        self.anchor_id_list = anchor_id_list
        self.show_last_n = show_last_n
        self.xdata, self.ydata, self.zdata = [], [], []
        self.std_x, self.std_y, self.std_z = [], [], []
        self.dist_data = [[] for _ in range(len(anchor_list))]

        self.fig = plt.figure(figsize=(15, 10))
        self.gs = GridSpec(3, 2, width_ratios=[1, 2])

        self.ax1 = self.fig.add_subplot(self.gs[:, 0])
        self.ax2 = self.fig.add_subplot(self.gs[0, 1])
        self.ax3 = self.fig.add_subplot(self.gs[1, 1])
        self.ax4 = self.fig.add_subplot(self.gs[2, 1])

        self.ln1, = self.ax1.plot([], [], 'ro')
        self.lines2 = [self.ax2.plot([], [], '.-', label=f'Anchor {anchor_id_list[i]}')[0] for i in range(len(anchor_list))]
        self.line_x, = self.ax3.plot([], [], 'r.-', label='x')
        self.line_y, = self.ax3.plot([], [], 'g.-', label='y')
        self.line_z, = self.ax3.plot([], [], 'b.-', label='z')
        self.std_line_x, = self.ax4.plot([], [], 'r.-', label='std_x')
        self.std_line_y, = self.ax4.plot([], [], 'g.-', label='std_y')
        self.std_line_z, = self.ax4.plot([], [], 'b.-', label='std_z')

        self.init_plot()

    def init_plot(self):
        anchor_x = self.anchor_list[:, 0]
        anchor_y = self.anchor_list[:, 1]

        self.ax1.set_xlim(0, 25)
        self.ax1.set_ylim(0, 25)
        self.ax1.set_aspect('equal')
        self.ax1.plot(anchor_x, anchor_y, 'bo', label='Anchors')
        for i, (x, y) in enumerate(zip(anchor_x, anchor_y)):
            self.ax1.text(x, y, f'id_{self.anchor_id_list[i]}', fontsize=12, ha='right')
        self.ax1.set_title('Estimated Position')
        self.ax1.legend()
        self.ax1.grid(True)

        self.ax2.set_xlim(0, self.show_last_n)
        self.ax2.set_ylim(0, 25)
        self.ax2.set_ylabel('Measured Distance')
        self.ax2.set_xlabel('Time Step')
        self.ax2.set_title('Measured Distances to Anchors')
        self.ax2.legend()
        self.ax2.grid(True)

        self.ax3.set_xlim(0, self.show_last_n)
        self.ax3.set_ylim(0, 25)
        self.ax3.set_ylabel('Position')
        self.ax3.set_xlabel('Time Step')
        self.ax3.set_title('x, y, z Positions Over Time')
        self.ax3.legend()
        self.ax3.grid(True)

        self.ax4.set_xlim(0, self.show_last_n)
        self.ax4.set_ylim(0, 1)
        self.ax4.set_ylabel('Standard Deviation')
        self.ax4.set_xlabel('Time Step')
        self.ax4.set_title('Standard Deviations of x, y, z Over Time')
        self.ax4.legend()
        self.ax4.grid(True)

    def update_plot(self, frame, est_pos, p_mat, dist_meas):
        self.xdata.append(est_pos[0])
        self.ydata.append(est_pos[1])
        self.zdata.append(est_pos[2])
        self.std_x.append(np.sqrt(p_mat[0, 0]))
        self.std_y.append(np.sqrt(p_mat[1, 1]))
        self.std_z.append(np.sqrt(p_mat[2, 2]))
        self.ln1.set_data(self.xdata, self.ydata)

        for i, dist in enumerate(dist_meas):
            self.dist_data[i].append(dist)
            self.lines2[i].set_data(range(len(self.dist_data[i])), self.dist_data[i])

        self.ax2.set_xlim(max(0, frame - self.show_last_n), frame)
        self.ax3.set_xlim(max(0, frame - self.show_last_n), frame)
        self.ax4.set_xlim(max(0, frame - self.show_last_n), frame)

        self.line_x.set_data(range(len(self.xdata)), self.xdata)
        self.line_y.set_data(range(len(self.ydata)), self.ydata)
        self.line_z.set_data(range(len(self.zdata)), self.zdata)

        self.std_line_x.set_data(range(len(self.std_x)), self.std_x)
        self.std_line_y.set_data(range(len(self.std_y)), self.std_y)
        self.std_line_z.set_data(range(len(self.std_z)), self.std_z)

        plt.draw()
        plt.pause(0.1)

def main_sim():
    auv_dim_state = 3
    ahoi_dim_meas = 1
    x0_est = np.array([20, 10, 1])
    p_mat_est = np.diag([0.1, 0.1, 0.1])

    process_noise_mat = np.diag([0.1, 0.1, 0.1])
    meas_noise_val = 0.5

    ahoi_ekf = EKF_Node(auv_dim_state, ahoi_dim_meas,
                        meas_noise_val, process_noise_mat,
                        x0_est, p_mat_est)
    
    anchor_id_list = [2, 6, 9]
    anchor_list = np.array([[10, 0, 0],
                            [20, 20, 0],
                            [0, 20, 0]])
    x_real = np.array([5, 5, 1])

    N = 100
    show_last_n = 10

    plotter = EKFPlotter(anchor_list, anchor_id_list, show_last_n)

    for i in range(N):
        print(f"[{i}] est position {ahoi_ekf.get_x_est()}")
        ahoi_ekf.predict(dt_sim=1)
        
        dist_meas = []
        for anchor_pos in anchor_list:
            dist = np.sqrt((x_real[0] - anchor_pos[0])**2 +
                           (x_real[1] - anchor_pos[1])**2 + (x_real[2] - anchor_pos[2])**2)
            dist_meas.append(dist)
            ahoi_ekf.measurement_update(dist_meas=dist, anchor_pos=anchor_pos, w_mat_dist=meas_noise_val)
        
        est_pos = ahoi_ekf.get_x_est()
        p_mat = ahoi_ekf.get_p_mat()
        plotter.update_plot(i, est_pos, p_mat, dist_meas)
        # time.sleep(0.1)  # Additional sleep if needed

    plt.show()

if __name__ == '__main__':
    main_sim()
