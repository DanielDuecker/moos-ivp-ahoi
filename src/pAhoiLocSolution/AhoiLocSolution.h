/************************************************************/
/*    NAME: Daniel Duecker                                  */
/*    ORGN: MIT, Cambridge MA // TU Munich, Germany         */
/*    FILE: AhoiLocSolution.h                               */
/*    DATE: July 2024                                       */
/************************************************************/

#ifndef AhoiLocSolution_HEADER
#define AhoiLocSolution_HEADER

#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include "RangingLocEKF.h"
#include <armadillo>
#include <vector>

class AhoiLocSolution : public AppCastingMOOSApp
{
 public:
   AhoiLocSolution();
   ~AhoiLocSolution();

 protected: // Standard MOOSApp functions to overload  
   bool OnNewMail(MOOSMSG_LIST &NewMail);
   bool Iterate();
   bool OnConnectToServer();
   bool OnStartUp();

 protected: // Standard AppCastingMOOSApp function to overload 
   bool buildReport();

 protected:
   void registerVariables();

 private:
   RangingLocEKF m_ekf;  // Extended Kalman Filter object

 private: // State variables
   double m_current_x, m_current_y, m_current_z;
   std::vector<double> m_ranges; // Range measurements to anchor nodes
   std::vector<arma::vec> m_anchor_nodes; // Positions of the anchor nodes in 3D space
};

#endif 
