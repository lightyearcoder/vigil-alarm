#include "vigil_panel.h"
#include <cassert>
#include <iostream>
using namespace vigil;
int main(){
  ctx.ha_connected=true; ctx.state="disarmed"; ctx.features=7; ctx.open_now="Living PIR";
  ctx.sensors="Living PIR|binary_sensor.living_pir|open|1\nSmoke|binary_sensor.smoke|closed|0\nBad line\nA|b|bypassed|1";
  assert(sensor_count()==3 && open_count()==1);
  assert(row_at(0,1).bypassable==false && row_at(0,3).name=="");
  assert(state_sub(NAN)=="Open: Living PIR");
  ctx.lang=EN; assert(sensors_button_text()=="Sensors  (1 open)");
  assert(show_home()&&show_away()&&show_night()&&!show_disarm());
  ctx.state="arming"; ctx.mode="away"; ctx.delay_end=110; assert(state_sub(100)=="Away\nLeave within: 10 s");
  assert(!show_home()&&show_disarm());
  ctx.state="pending"; assert(wants_disarm_keypad());
  ctx.code_arm_required=false; assert(!needs_code(ARM_HOME)&&needs_code(DISARM));
  assert(truthy("on")&&!truthy("False")&&std::isnan(parse_number("None"))&&parse_number("3.5")==3.5);
  ctx.ha_connected=false; assert(state_title()=="No connection");
  ctx.ha_connected=true; ctx.state="pending"; assert(keypad_route(false,0)==1 && keypad_route(true,DISARM)==0);
  ctx.state="armed_home"; assert(keypad_route(true,DISARM)==2 && keypad_route(true,ARM_AWAY)==2 && keypad_route(true,BYPASS)==0 && keypad_route(false,0)==0);
  ctx.state="disarmed"; assert(keypad_route(true,ARM_AWAY)==0);
  // Who may see the sensors: the safe choice is a code.
  assert(parse_sensor_list("always")==LIST_ALWAYS && parse_sensor_list("never")==LIST_NEVER && parse_sensor_list("code")==LIST_CODE && parse_sensor_list("typo")==LIST_CODE);
  ctx.lang=EN; ctx.sensor_list=LIST_CODE; ctx.sensors_unlocked=false; ctx.open_now="Living PIR"; ctx.open_mode="Living PIR"; ctx.changed_by="Anna"; ctx.cause_sensor="Front door";
  ctx.state="armed_away"; assert(!sensors_visible() && show_sensors_button() && state_sub(NAN)=="" && sensors_button_text()=="Sensors");
  ctx.state="pending"; ctx.delay_end=110; assert(state_sub(100)=="Disarm within: 10 s");
  ctx.state="triggered"; ctx.cause="intrusion"; assert(state_sub(NAN).find("Front door")==std::string::npos);
  ctx.state="disarmed"; assert(state_sub(NAN)=="Open: Living PIR" && sensors_button_text()=="Sensors  (1 open)");  // needed to arm
  ctx.state="armed_away"; ctx.sensors_unlocked=true; assert(sensors_visible() && state_sub(NAN).find("Anna")!=std::string::npos);
  ctx.code_arm_required=true; assert(!needs_code(BYPASS) && needs_code(UNLOCK) && needs_code(DISARM));
  ctx.sensors_unlocked=false; assert(needs_code(BYPASS));
  ctx.sensor_list=LIST_ALWAYS; assert(sensors_visible() && details_visible() && state_sub(NAN).find("Anna")!=std::string::npos);
  ctx.sensor_list=LIST_NEVER; assert(!sensors_visible() && !show_sensors_button() && !details_visible());
  std::cout << "ok\n";
}
