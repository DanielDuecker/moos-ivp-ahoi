#include "RangingLocEKF.h"
#include <cmath>
#include <iostream>

RangingLocEKF::RangingLocEKF() {
}

RangingLocEKF::~RangingLocEKF() {
}

void RangingLocEKF::Initialize(const std::vector<arma::vec>& anchor_nodes) {
    // Initialize state vector and covariance matrix
    m_x = arma::vec(6, arma::fill::zeros);  // [x, y, z, vx, vy, vz]
    m_P = arma::mat(6, 6, arma::fill::eye) * 0.1; // Initialize with small uncertainty

    // Initialize the state transition model (m_F), observation model (m_H),
    // process noise covariance (m_Q), and observation noise covariance (m_R)
    m_F = arma::mat(6, 6, arma::fill::eye);
    for (int i = 0; i < 3; ++i) {
        m_F(i, i+3) = 1; // Adding velocity terms
    }

    m_H = arma::mat(4, 6, arma::fill::zeros); // 4 measurements, 6 state variables
    for (int i = 0; i < 4; ++i) {
        m_H(i, 0) = 1; // x
        m_H(i, 1) = 1; // y
        m_H(i, 2) = 1; // z
    }

    m_Q = arma::mat(6, 6, arma::fill::eye) * 0.01;
    m_R = arma::mat(4, 4, arma::fill::eye) * 0.1; // 4 measurements

    // Positions of the anchor nodes
    m_anchor_nodes = anchor_nodes;
}

void RangingLocEKF::Predict() {
    m_x = m_F * m_x;
    m_P = m_F * m_P * m_F.t() + m_Q;
}

void RangingLocEKF::Update(int anchor_id, double range) {
    if (anchor_id >= m_anchor_nodes.size())
        return; // Ensure the anchor_id is valid

    arma::vec anchor_pos = m_anchor_nodes[anchor_id];
    
    double dx = m_x(0) - anchor_pos(0);
    double dy = m_x(1) - anchor_pos(1);
    double dz = m_x(2) - anchor_pos(2);
    double expected_range = std::sqrt(dx*dx + dy*dy + dz*dz);
    
    if (expected_range == 0) {
        std::cerr << "Error: Division by zero in expected range calculation" << std::endl;
        return;
    }

    arma::vec z(1);
    z(0) = range - expected_range;

    arma::rowvec H = computeJacobian(m_x, anchor_pos);

    arma::mat S = H * m_P * H.t() + m_R(anchor_id, anchor_id);
    if (S(0, 0) == 0) {
        std::cerr << "Error: Division by zero in matrix S calculation" << std::endl;
        return;
    }

    arma::mat K = m_P * H.t() * arma::inv(S);
    m_x = m_x + K * z;
    m_P = (arma::mat(m_P.n_rows, m_P.n_cols, arma::fill::eye) - K * H) * m_P;
}

arma::vec RangingLocEKF::getState() const {
    return m_x;
}

arma::rowvec RangingLocEKF::computeJacobian(const arma::vec& state, const arma::vec& anchor_pos) {
    double dx = state(0) - anchor_pos(0);
    double dy = state(1) - anchor_pos(1);
    double dz = state(2) - anchor_pos(2);
    double range = std::sqrt(dx*dx + dy*dy + dz*dz);

    if (range == 0) {
        std::cerr << "Error: Division by zero in Jacobian calculation" << std::endl;
        return arma::rowvec(6, arma::fill::zeros);
    }
    
    arma::rowvec H(6, arma::fill::zeros);
    H(0) = dx / range;
    H(1) = dy / range;
    H(2) = dz / range;
    // H(3), H(4), H(5) are already zero

    return H;
}
