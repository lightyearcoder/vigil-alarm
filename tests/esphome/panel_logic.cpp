#include "vigil_panel.h"
#include <cassert>
#include <iostream>
using namespace vigil;
int main(){
  // Not linked yet: no profile, nothing to press.
  ctx.ha_connected=true; ctx.state="disarmed"; ctx.device_name="vigil-panel-garage"; ctx.lang=EN;
  assert(!linked() && !usable() && state_title()=="Not linked" && !show_home() && !show_disarm() && !show_sensors_button());
  assert(state_sub(NAN).find("vigil-panel-garage")!=std::string::npos);
  ctx.profile_version=2; assert(state_title()=="Not linked" && state_sub(NAN)=="Update the firmware or Vigil" && !usable());
  ctx.profile_version=1; ctx.modes_mask=7; ctx.sensor_list=LIST_ALWAYS; ctx.profile_unlocked=true;
  ctx.open_now="Living PIR"; ctx.open_total=1;
  ctx.sensors="Living PIR|binary_sensor.living_pir|open|1\nSmoke|binary_sensor.smoke|closed|0\nBad line\nA|b|bypassed|1";
  assert(usable() && sensor_count()==3 && open_count()==1 && open_total_count()==1);
  assert(row_at(0,1).bypassable==false && row_at(0,3).name=="");
  assert(state_sub(NAN)=="Open: 1");
  assert(sensors_button_text()=="Sensors  (1 open)");
  assert(show_home()&&show_away()&&show_night()&&!show_disarm());
  // The profile decides which modes there are, and blocking takes everything away.
  ctx.modes_mask=2; assert(!show_home()&&show_away()&&!show_night()); ctx.modes_mask=7;
  ctx.blocked=true; assert(state_title()=="Blocked" && state_sub(NAN)=="This panel is blocked in Vigil" && !show_away() && !show_sensors_button() && !bypass_allowed() && !show_disarm());
  ctx.blocked=false;
  ctx.state="arming"; ctx.mode="away"; ctx.delay_end=110; assert(state_sub(100)=="Away\nLeave within: 10 s");
  assert(!show_home()&&show_disarm());
  ctx.can_disarm=false; assert(!show_disarm()); ctx.can_disarm=true;
  ctx.can_bypass=false; assert(!bypass_allowed()); ctx.can_bypass=true; assert(bypass_allowed());
  ctx.code_arm_required=false; assert(!needs_code(ARM_HOME)&&needs_code(DISARM)&&needs_code(BYPASS)&&needs_code(UNBYPASS)&&needs_code(UNLOCK)&&needs_code(INFO));
  assert(is_admin_action(INFO)&&!is_admin_action(UNLOCK)&&!is_admin_action(BYPASS)&&!is_admin_action(DISARM));
  assert(is_unlock_action(UNLOCK)&&is_unlock_action(INFO)&&!is_unlock_action(DISARM));
  assert(truthy("on")&&!truthy("False")&&std::isnan(parse_number("None"))&&parse_number("3.5")==3.5);
  assert(parse_language("nl")==NL && parse_language("en")==EN && parse_language("")==EN);
  ctx.ha_connected=false; assert(state_title()=="No connection");
  ctx.ha_connected=true; ctx.state="pending"; assert(keypad_route(false,0)==0 && keypad_route(true,DISARM)==0 && show_disarm());
  ctx.state="triggered"; assert(keypad_route(false,0)==0 && keypad_route(true,DISARM)==0 && show_disarm());
  ctx.state="armed_home"; assert(keypad_route(true,DISARM)==0 && keypad_route(true,ARM_AWAY)==2 && keypad_route(true,ARM_AWAY)==2 && keypad_route(true,BYPASS)==0 && keypad_route(false,0)==0);
  ctx.state="disarmed"; assert(keypad_route(true,DISARM)==2 && keypad_route(true,ARM_AWAY)==0);
  // The screen may only go dark in a steady state; during an alarm it is a setting
  ctx.ha_connected=true; ctx.screen_off_on_alarm=false;
  for (auto st : {"disarmed","armed_home","armed_away","armed_night"}) { ctx.state=st; assert(screen_may_sleep()); }
  ctx.state="arming"; assert(!screen_may_sleep());
  ctx.state="pending"; assert(!screen_may_sleep());
  ctx.state="triggered"; assert(!screen_may_sleep());
  ctx.screen_off_on_alarm=true; assert(screen_may_sleep()); ctx.state="pending"; assert(!screen_may_sleep());
  ctx.ha_connected=false; ctx.state="arming"; assert(screen_may_sleep()); ctx.screen_off_on_alarm=false; ctx.ha_connected=true;
  // Vigil's refusals are shown in the language of the panel, whatever language Home Assistant answered in
  ctx.lang=NL;
  assert(localize_error("Invalid code.")=="Ongeldige code" && localize_error("Ongeldige code.")=="Ongeldige code");
  assert(localize_error("Too many wrong codes. Try again in 5 min")=="Te veel foute codes. Probeer het over 5 min opnieuw");
  assert(localize_error("Te veel foute codes. Probeer het over 12 min opnieuw.")=="Te veel foute codes. Probeer het over 12 min opnieuw");
  assert(localize_error("Too many wrong codes. This is locked until an administrator unlocks it in Vigil.").find("beheerder")!=std::string::npos);
  assert(localize_error("Too many wrong codes.")=="Te veel foute codes. Even wachten");
  assert(localize_error("Bypassing or restoring a tamper sensor needs the right to bypass tamper, or a Home Assistant administrator.").find("sabotage")!=std::string::npos);
  assert(localize_error("Bypassing or restoring sensors needs the right to bypass, given to this user in Vigil, or a Home Assistant administrator.").find("sensoren")!=std::string::npos);
  assert(localize_error("The panel Garage panel is blocked.")=="Dit paneel is geblokkeerd");
  assert(localize_error("Something nobody planned")=="Something nobody planned");
  ctx.lang=EN;
  assert(localize_error("Ongeldige code.")=="Invalid code" && localize_error("Te veel foute codes. Probeer het over 3 min opnieuw.")=="Too many wrong codes. Try again in 3 min");
  ctx.lang=EN;
  // Who may see the sensors: the safe choice is a code.
  assert(parse_sensor_list("always")==LIST_ALWAYS && parse_sensor_list("never")==LIST_NEVER && parse_sensor_list("code")==LIST_CODE && parse_sensor_list("typo")==LIST_CODE);
  ctx.sensor_list=LIST_CODE; ctx.sensors_unlocked=false; ctx.profile_unlocked=false; ctx.changed_by="Anna"; ctx.cause_sensor="Front door";
  // Vigil hides the names while locked: only numbers arrive.
  ctx.open_now=""; ctx.open_mode=""; ctx.sensors=""; ctx.open_total=3;
  ctx.state="disarmed"; assert(state_sub(NAN)=="Open: 3" && sensors_button_text()=="Sensors  (3 open)" && sensor_count()==0);
  ctx.open_total=0; assert(state_sub(NAN)=="All closed" && sensors_button_text()=="Sensors");
  ctx.faults_total=2; assert(state_sub(NAN)=="All closed\nProblems: 2"); ctx.faults_total=0;
  ctx.state="armed_away"; assert(!sensors_visible() && show_sensors_button() && state_sub(NAN)=="");
  ctx.state="pending"; ctx.delay_end=110; assert(state_sub(100)=="Disarm within: 10 s");
  ctx.state="triggered"; ctx.cause="intrusion"; assert(state_sub(NAN).find("Front door")==std::string::npos);
  // Unlocked: the panel entered the code, and Vigil agrees. Either one alone is not enough.
  ctx.state="armed_away"; ctx.sensors_unlocked=true; assert(!sensors_visible() && !details_visible());
  ctx.profile_unlocked=true; assert(sensors_visible() && details_visible() && state_sub(NAN).find("Anna")!=std::string::npos);
  ctx.sensors_unlocked=false; assert(!sensors_visible());  // the panel forgot, Vigil may still be unlocked
  ctx.sensors_unlocked=true; ctx.profile_unlocked=false; assert(!sensors_visible());  // Vigil locked again
  ctx.sensor_list=LIST_ALWAYS; assert(sensors_visible() && details_visible());
  ctx.sensor_list=LIST_NEVER; ctx.sensors_unlocked=false; assert(!sensors_visible() && !show_sensors_button() && !details_visible());
  assert(keypad_hint(DISARM)=="Enter your user code" && keypad_hint(UNLOCK)=="Enter your user code" && keypad_hint(INFO)=="Enter the installer code");
  assert(keypad_title(UNLOCK,"")=="View sensors" && keypad_title(INFO,"")=="View panel info");
  std::cout << "ok\n";
}
