/************************************************************/
/*    NAME: Daniel Duecker                                  */
/*    ORGN: MIT, Cambridge MA                               */
/*    FILE: AhoiRangeSim.cpp                                */
/*    DATE: July 2024                                       */
/************************************************************/

#include <iterator>
#include "MBUtils.h"
#include "ACTable.h"
#include "AhoiRangeSim.h"

using namespace std;

//---------------------------------------------------------
// Constructor()

AhoiRangeSim::AhoiRangeSim()
{
  m_nav_x = 0.0;
  m_nav_y = 0.0;
  m_nav_z = 0.0;

  // Initialize anchor node positions
  m_anchor_nodes = {
    {0.0, 0.0, 0.0},
    {10.0, 0.0, 0.0},
    {0.0, 10.0, 0.0},
    {10.0, 10.0, 0.0}
  };
}

//---------------------------------------------------------
// Destructor

AhoiRangeSim::~AhoiRangeSim()
{
}

//---------------------------------------------------------
// Procedure: OnNewMail()

bool AhoiRangeSim::OnNewMail(MOOSMSG_LIST &NewMail)
{
  AppCastingMOOSApp::OnNewMail(NewMail);

  MOOSMSG_LIST::iterator p;
  for(p=NewMail.begin(); p!=NewMail.end(); p++) {
    CMOOSMsg &msg = *p;
    string key    = msg.GetKey();

    if(key == "NAV_X") 
    {
      m_nav_x = msg.GetDouble();
    }
    else if(key == "NAV_Y") 
    {
      m_nav_y = msg.GetDouble();
    }
    else if(key == "NAV_Z") 
    {
      m_nav_z = msg.GetDouble();
    }
    else if(key != "APPCAST_REQ") // handled by AppCastingMOOSApp
       reportRunWarning("Unhandled Mail: " + key);
  }
  return true;
}

//---------------------------------------------------------
// Procedure: OnConnectToServer()

bool AhoiRangeSim::OnConnectToServer()
{
  registerVariables();
  return true;
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

bool AhoiRangeSim::Iterate()
{
  AppCastingMOOSApp::Iterate();

  // Simulate and publish range measurements
  publishRangeMeasurements();

  AppCastingMOOSApp::PostReport();
  return true;
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool AhoiRangeSim::OnStartUp()
{
  AppCastingMOOSApp::OnStartUp();

  registerVariables();
  return true;
}

//---------------------------------------------------------
// Procedure: registerVariables()

void AhoiRangeSim::registerVariables()
{
  Register("NAV_X", 0);
  Register("NAV_Y", 0);
  Register("NAV_Z", 0);
}

//---------------------------------------------------------
// Procedure: publishRangeMeasurements()

void AhoiRangeSim::publishRangeMeasurements()
{
  arma::vec nav_position = {m_nav_x, m_nav_y, m_nav_z};
  for (size_t i = 0; i < m_anchor_nodes.size(); ++i)
  {
    double range = arma::norm(nav_position - m_anchor_nodes[i]);
    Notify("RANGE_MEASUREMENT" + to_string(i), range);
  }
}


//------------------------------------------------------------
// Procedure: buildReport()

bool AhoiRangeSim::buildReport() 
{
  m_msgs << "============================================" << endl;
  m_msgs << "File: AhoiRangeSim                          " << endl;
  m_msgs << "============================================" << endl;

  ACTable actab(6);
  actab << "Pos_true | Pos_est | Range1 | Range2 | Range3 | Range4";
  actab.addHeaderLines();
  m_msgs << actab.getFormattedString();

  return(true);
}