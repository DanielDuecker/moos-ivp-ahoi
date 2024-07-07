/************************************************************/
/*    NAME: Daniel Duecker                                  */
/*    ORGN: MIT, Cambridge MA                               */
/*    FILE: AhoiRangeSim.h                                  */
/*    DATE: July 2024                                       */
/************************************************************/

#ifndef AhoiRangeSim_HEADER
#define AhoiRangeSim_HEADER

#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include <armadillo>
#include <vector>

class AhoiRangeSim : public AppCastingMOOSApp
{
 public:
   AhoiRangeSim();
   ~AhoiRangeSim();

 protected: // Standard MOOSApp functions to overload  
   bool OnNewMail(MOOSMSG_LIST &NewMail);
   bool Iterate();
   bool OnConnectToServer();
   bool OnStartUp();

 protected: // Standard AppCastingMOOSApp function to overload 
   bool buildReport();
   
 protected:
   void registerVariables();
   void publishRangeMeasurements();

 private:
   double m_nav_x, m_nav_y, m_nav_z;
   std::vector<arma::vec> m_anchor_nodes; // Positions of the anchor nodes in 3D space
};

#endif 
