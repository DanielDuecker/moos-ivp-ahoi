#ifndef RANGING_LOC_EKF_H
#define RANGING_LOC_EKF_H

#include <armadillo>
#include <vector>

class RangingLocEKF {
public:
    RangingLocEKF();
    ~RangingLocEKF();

    void Initialize(const std::vector<arma::vec>& anchor_nodes);
    void Predict();
    void Update(int anchor_id, double range);

    arma::vec getState() const;

private:
    arma::vec m_x;  // State vector [x, y, z, vx, vy, vz]
    arma::mat m_P;  // State covariance matrix
    arma::mat m_F;  // State transition model
    arma::mat m_H;  // Observation model
    arma::mat m_R;  // Observation noise covariance
    arma::mat m_Q;  // Process noise covariance

    std::vector<arma::vec> m_anchor_nodes; // Positions of the anchor nodes in 3D space

    arma::rowvec computeJacobian(const arma::vec& state, const arma::vec& anchor_pos);
};

#endif // RANGING_LOC_EKF_H
