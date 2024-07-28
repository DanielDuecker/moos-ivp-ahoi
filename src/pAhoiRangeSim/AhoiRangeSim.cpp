/************************************************************/
/*    NAME: Daniel Duecker                                  */
/*    ORGN: MIT, Cambridge MA // TU Munich, Germany         */
/*    FILE: AhoiRangeSim.cpp                                */
/*    DATE: July 2024                                       */
/************************************************************/

#include <iterator>
#include <iostream>
#include "MBUtils.h"
#include "ACTable.h"
#include "AhoiRangeSim.h"

using namespace std;

//---------------------------------------------------------
// Constructor()

AhoiRangeSim::AhoiRangeSim() {
  // Initialize the anchor positions
  m_anchor_nodes = {
    {1.0, 0.0, 0.0},
    {10.0, 0.0, 0.0},
    {1.0, 10.0, 0.0},
    {10.0, 10.0, 0.0}
  };
  m_ranges.resize(m_anchor_nodes.size(), 0.0);
}

//---------------------------------------------------------
// Destructor

AhoiRangeSim::~AhoiRangeSim() {
}

//---------------------------------------------------------
// Procedure: OnNewMail()

bool AhoiRangeSim::OnNewMail(MOOSMSG_LIST &NewMail) {
  AppCastingMOOSApp::OnNewMail(NewMail);

  MOOSMSG_LIST::iterator p;
  for(p = NewMail.begin(); p != NewMail.end(); p++) {
    CMOOSMsg &msg = *p;
    string key = msg.GetKey();

    if(key == "NAV_X") {
      m_mobile_x = msg.GetDouble();
    }
    else if(key == "NAV_Y") {
      m_mobile_y = msg.GetDouble();
    }
    else if(key == "NAV_Z") {
      m_mobile_z = msg.GetDouble();
    }
    else if(key != "APPCAST_REQ") // handled by AppCastingMOOSApp
      reportRunWarning("Unhandled Mail: " + key);
  }
  return(true);
}

//---------------------------------------------------------
// Procedure: OnConnectToServer()

bool AhoiRangeSim::OnConnectToServer() {
  registerVariables();
  return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

bool AhoiRangeSim::Iterate() {
  AppCastingMOOSApp::Iterate();

  // Calculate ranges to anchor nodes
  calculateRanges();

  // Publish the current position of the mobile robot
  Notify("MOBILE_X", m_mobile_x);
  Notify("MOBILE_Y", m_mobile_y);
  Notify("MOBILE_Z", m_mobile_z);

  // Publish the range measurements and anchor positions
  for(size_t i = 0; i < m_ranges.size(); ++i) {
    Notify("ANCHOR" + to_string(i) + "_POS_X", m_anchor_nodes[i](0) );
    Notify("ANCHOR" + to_string(i) + "_POS_Y", m_anchor_nodes[i](1) );
    Notify("ANCHOR" + to_string(i) + "_POS_Z", m_anchor_nodes[i](2) );
    Notify("RANGE_MEASUREMENT" + to_string(i), m_ranges[i]);
  }

  AppCastingMOOSApp::PostReport();
  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool AhoiRangeSim::OnStartUp() {
  AppCastingMOOSApp::OnStartUp();

  STRING_LIST sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if(!m_MissionReader.GetConfiguration(GetAppName(), sParams))
    reportConfigWarning("No config block found for " + GetAppName());

  STRING_LIST::iterator p;
  for(p = sParams.begin(); p != sParams.end(); p++) {
    string orig = *p;
    string line = *p;
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

void AhoiRangeSim::registerVariables() {
  AppCastingMOOSApp::RegisterVariables();
  Register("NAV_X", 0);
  Register("NAV_Y", 0);
  Register("NAV_Z", 0);
}

//---------------------------------------------------------
// Procedure: buildReport()

bool AhoiRangeSim::buildReport() {
  m_msgs << "============================================" << endl;
  m_msgs << "File: AhoiRangeSim                           " << endl;
  m_msgs << "============================================" << endl;

  ACTable actab(7);
  actab << "Pos_X | Pos_Y | Pos_Z | Range1 | Range2 | Range3 | Range4";
  actab.addHeaderLines();
  actab << m_mobile_x << m_mobile_y << m_mobile_z << m_ranges[0] << m_ranges[1] << m_ranges[2] << m_ranges[3];
  m_msgs << actab.getFormattedString();

  return(true);
}

//---------------------------------------------------------
// Procedure: calculateRanges()

void AhoiRangeSim::calculateRanges() {
  for(size_t i = 0; i < m_anchor_nodes.size(); ++i) {
    double dx = m_mobile_x - m_anchor_nodes[i](0) ;
    double dy = m_mobile_y - m_anchor_nodes[i](1) ;
    double dz = m_mobile_z - m_anchor_nodes[i](2) ;
    m_ranges[i] = std::sqrt(dx*dx + dy*dy + dz*dz);
  }
}
