/************************************************************/
/*    NAME: Daniel Duecker                                  */
/*    ORGN: MIT, Cambridge MA // TU Munich, Germany         */
/*    FILE: AhoiLocSolution.cpp                             */
/*    DATE: July 2024                                       */
/************************************************************/

#include <iterator>
#include <iostream>
#include "MBUtils.h"
#include "ACTable.h"
#include "AhoiLocSolution.h"

using namespace std;

//---------------------------------------------------------
// Constructor()

AhoiLocSolution::AhoiLocSolution() {
  // Initialize the Kalman filter parameters with hardcoded anchor positions
  m_anchor_nodes = {
    {1.0, 0.0, 0.0},
    {10.0, 0.0, 0.0},
    {1.0, 10.0, 0.0},
    {10.0, 10.0, 0.0}
  };
  m_ekf.Initialize(m_anchor_nodes);
  m_ranges.resize(4, 0.0); // Initialize range measurements
}

//---------------------------------------------------------
// Destructor

AhoiLocSolution::~AhoiLocSolution() {
}

//---------------------------------------------------------
// Procedure: OnNewMail()

bool AhoiLocSolution::OnNewMail(MOOSMSG_LIST &NewMail) {
  AppCastingMOOSApp::OnNewMail(NewMail);

  MOOSMSG_LIST::iterator p;
  for(p=NewMail.begin(); p!=NewMail.end(); p++) {
    CMOOSMsg &msg = *p;
    string key    = msg.GetKey();

    if(key == "NAV_X") {
      m_current_x = msg.GetDouble();
    }
    else if(key == "NAV_Y") {
      m_current_y = msg.GetDouble();
    }
    else if(key == "NAV_Z") {
      m_current_z = msg.GetDouble();
    }
    else if(key.find("RANGE_MEASUREMENT") != string::npos) {
      int anchor_id = stoi(key.substr(key.size() - 1)); // Assuming keys are "RANGE_MEASUREMENT0", "RANGE_MEASUREMENT1", etc.
      if(anchor_id < m_ranges.size()) {
        double range = msg.GetDouble();
        m_ranges[anchor_id] = range;
        m_ekf.Update(anchor_id, range);
      }
    }
    else if(key != "APPCAST_REQ") // handled by AppCastingMOOSApp
       reportRunWarning("Unhandled Mail: " + key);
  }
  return(true);
}

//---------------------------------------------------------
// Procedure: OnConnectToServer()

bool AhoiLocSolution::OnConnectToServer() {
  registerVariables();
  return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

bool AhoiLocSolution::Iterate() {
  AppCastingMOOSApp::Iterate();

  // Predict the new state
  m_ekf.Predict();

  // Publish the current state estimate (position)
  arma::vec state = m_ekf.getState();
  Notify("POSITION_X", state(0));
  Notify("POSITION_Y", state(1));
  Notify("POSITION_Z", state(2));

  AppCastingMOOSApp::PostReport();
  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool AhoiLocSolution::OnStartUp() {
  AppCastingMOOSApp::OnStartUp();

  STRING_LIST sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if(!m_MissionReader.GetConfiguration(GetAppName(), sParams))
    reportConfigWarning("No config block found for " + GetAppName());

  STRING_LIST::iterator p;
  for(p=sParams.begin(); p!=sParams.end(); p++) {
    string orig  = *p;
    string line  = *p;
    string param = tolower(biteStringX(line, '='));
    string value = line;

    bool handled = false;
    if(param == "foo") {
      handled = true;
    }
    else if(param == "bar") {
      handled = true;
    }

    if(!handled)
      reportUnhandledConfigWarning(orig);
  }

  registerVariables();  
  return(true);
}

//---------------------------------------------------------
// Procedure: registerVariables()

void AhoiLocSolution::registerVariables() {
  AppCastingMOOSApp::RegisterVariables();
  Register("NAV_X", 0);
  Register("NAV_Y", 0);
  Register("NAV_Z", 0);
  Register("RANGE_MEASUREMENT0", 0);
  Register("RANGE_MEASUREMENT1", 0);
  Register("RANGE_MEASUREMENT2", 0);
  Register("RANGE_MEASUREMENT3", 0);
}

//------------------------------------------------------------
// Procedure: buildReport()

bool AhoiLocSolution::buildReport() {
  m_msgs << "============================================" << endl;
  m_msgs << "File: AhoiLocSolution                        " << endl;
  m_msgs << "============================================" << endl;

  ACTable actab(6);
  actab << "Pos_true | Pos_est | Range1 | Range2 | Range3 | Range4";
  actab.addHeaderLines();
  actab << m_current_x << m_ekf.getState()(0) << "---" << "---" << "---" << "---";
  actab << m_current_y << m_ekf.getState()(1) << m_ranges[0] << m_ranges[1] << m_ranges[2] << m_ranges[3];
  actab << m_current_z << m_ekf.getState()(2) << "---" << "---" << "---" << "---";
  m_msgs << actab.getFormattedString();

  return(true);
}
