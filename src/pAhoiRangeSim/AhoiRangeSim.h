/************************************************************/
/*    NAME: Daniel Duecker                                  */
/*    ORGN: MIT, Cambridge MA // TU Munich, Germany         */
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

 private:
   void calculateRanges();

 private: // State variables
   double m_mobile_x, m_mobile_y, m_mobile_z;
   std::vector<arma::vec> m_anchor_nodes; // Positions of the anchor nodes in 3D space
   std::vector<double> m_ranges; // Range measurements to anchor nodes
};

#endif 
