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
  ctx.state="arming"; ctx.mode="away"; ctx.delay_end=110; assert(state_sub(100)=="Away\nLeave the house now");
  assert(!show_home()&&show_disarm());
  ctx.can_disarm=false; assert(!show_disarm()); ctx.can_disarm=true;
  ctx.can_bypass=false; assert(!bypass_allowed()); ctx.can_bypass=true; assert(bypass_allowed());
  ctx.code_arm_required=false; assert(!needs_code(ARM_HOME)&&needs_code(DISARM)&&needs_code(BYPASS)&&needs_code(UNBYPASS)&&needs_code(UNLOCK)&&needs_code(INFO));
  assert(is_admin_action(INFO)&&!is_admin_action(UNLOCK)&&!is_admin_action(BYPASS)&&!is_admin_action(DISARM));
  assert(is_unlock_action(UNLOCK)&&is_unlock_action(INFO)&&!is_unlock_action(DISARM));
  assert(truthy("on")&&!truthy("False")&&std::isnan(parse_number("None"))&&parse_number("3.5")==3.5);
  assert(parse_language("nl")==NL && parse_language("en")==EN && parse_language("")==EN);
  assert(parse_language("de")==DE && parse_language("de-AT")==DE && parse_language("fr")==FR && parse_language("it")==IT && parse_language("es")==ES && parse_language("pt")==EN);
  // every language has every text, and the texts of the new languages are used
  { Context keep = ctx;
    for (int l = 0; l < LANGUAGE_COUNT; l++) { ctx.lang = l; for (const Text &t : TEXTS) assert(tr(t.key) == t.text[l] && !tr(t.key).empty()); }
    ctx.lang = DE; assert(tr("disarmed") == "Unscharf" && tr("force") == "Ueberbruecken und scharf schalten");
    ctx.lang = FR; assert(tr("disarm") == "Desactiver");
    ctx.lang = IT; assert(tr("blocked") == "Bloccato");
    ctx.lang = ES; assert(tr("arming") == "Activando");
    // what Home Assistant answers is recognised in any language and shown in the language of the panel
    ctx.lang = DE; assert(localize_error("Ungültiger Code.") == "Ungueltiger Code");
    ctx.lang = ES; assert(localize_error("Code invalid ... Invalid code.") == "Codigo no valido");
    ctx.lang = FR; assert(localize_error("Zu viele falsche Codes. Versuche es in 7 Min. erneut.") == "Trop de codes errones. Reessayez dans 7 min");
    ctx.lang = IT; assert(parse_refusal("Scharfschalten abgelehnt: sensor_open (Tuer).").text == "Impossibile inserire: Tuer e aperto");
    ctx.lang = DE; assert(parse_refusal("Activation refusée : sensor_unavailable (Porte, Cuisine).").text == "Scharfschalten nicht moeglich: Porte, Cuisine antwortet nicht");
    ctx.lang = EN; assert(parse_refusal("Activación rechazada: not_disarmed ().").forceable == false);
    ctx = keep; }
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
  ctx.state="pending"; ctx.delay_end=110; assert(state_sub(100)=="Disarm with your code");
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
  // The ring: colours, icon, countdown. The ring runs from full to empty over the length of the delay.
  ctx=Context(); ctx.lang=EN; ctx.ha_connected=true; ctx.profile_version=PROFILE_VERSION; ctx.modes_mask=7; ctx.state="disarmed";
  assert(state_color()==COL_OK && ring_color()==COL_OK && state_icon()==VIGIL_ICON_SHIELD_CHECK && ring_percent(NAN)==100 && ring_text(NAN)=="");
  ctx.open_total=1; assert(state_color()==COL_OK && ring_color()==COL_WARN && state_icon()==VIGIL_ICON_SHIELD_ALERT);  // not ready: amber
  ctx.open_total=0; ctx.faults_total=1; assert(ring_color()==COL_WARN); ctx.faults_total=0;
  ctx.state="arming"; ctx.mode="away"; ctx.delay_end=160; assert(counting(100) && ring_text(100)=="60" && ring_percent(100)==100);
  assert(ring_text(130)=="30" && ring_percent(130)==50 && ring_percent(160)==0 && ring_text(170)=="0");  // 60 s: halfway at 30 s
  ctx.state="armed_away"; assert(!counting(130) && ring_percent(130)==100 && ctx.delay_total==0 && state_color()==COL_AWAY && state_icon()==VIGIL_ICON_AWAY);
  ctx.state="pending"; ctx.delay_end=130; assert(ring_percent(120)==100 && ring_percent(125)==50);  // a new delay starts a new total
  ctx.state="arming"; ctx.delay_end=NAN; assert(!counting(100) && ring_text(100)=="" && ring_percent(100)==100);  // clock or end unknown: no number
  ctx.state="triggered"; assert(state_color()==COL_ALARM && state_icon()==VIGIL_ICON_BELL && tint_of(state_color())==0x3A1519);
  ctx.state="armed_home"; assert(state_color()==COL_HOME && tint_of(COL_HOME)==0x17233A);
  ctx.state="armed_night"; assert(state_color()==COL_NIGHT);
  ctx.ha_connected=false; assert(state_color()==COL_OFF && state_icon()==VIGIL_ICON_WIFI_OFF);
  ctx.ha_connected=true; ctx.blocked=true; assert(state_color()==COL_OFF && state_icon()==VIGIL_ICON_CANCEL);
  ctx.blocked=false; ctx.profile_version=0; assert(state_icon()==VIGIL_ICON_LINK_OFF);
  // Arming refused because something stops it: the text in the panel's language, and a button to bypass and arm
  ctx=Context(); ctx.lang=NL; ctx.ha_connected=true; ctx.profile_version=PROFILE_VERSION; ctx.modes_mask=7; ctx.state="disarmed";
  { Refusal r = parse_refusal("Arming refused: alarm_condition (Sabotage voordeur).");
    assert(r.text=="Inschakelen kan niet: Sabotage voordeur staat open" && r.forceable); }
  { Refusal r = parse_refusal("Inschakelen geweigerd: sensor_unavailable (Beweging gang, Keuken)."); assert(r.text=="Inschakelen kan niet: Beweging gang, Keuken reageert niet" && r.forceable); }
  { Refusal r = parse_refusal("Arming refused: not_disarmed ()."); assert(r.text=="Het alarm staat al aan" && !r.forceable); }
  assert(parse_refusal("Invalid code.").text.empty() && parse_refusal("Arming refused: something_new (X).").text.empty());
  ctx.lang=EN; assert(parse_refusal("Arming refused: sensor_open (Door).").text=="Cannot arm: Door is open");
  assert(!show_force()); ctx.refused_action=ARM_AWAY; assert(show_force());
  ctx.can_bypass=false; assert(!show_force()); ctx.can_bypass=true; ctx.state="armed_away"; assert(!show_force()); ctx.state="disarmed";
  ctx.code_arm_required=false; assert(!needs_code(ARM_AWAY)); ctx.force=true; assert(needs_code(ARM_AWAY));  // bypassing always asks a code
  assert(keypad_title(ARM_AWAY,"")=="Bypass and arm: Away"); ctx.force=false; assert(keypad_title(ARM_AWAY,"")=="Arm away");
  // 0.5.4: vacation and custom modes, the alarm memory line
  ctx=Context(); ctx.lang=EN; ctx.ha_connected=true; ctx.profile_version=PROFILE_VERSION; ctx.sensor_list=LIST_ALWAYS; ctx.state="disarmed";
  ctx.modes_mask=31; assert(show_home()&&show_away()&&show_night()&&show_vacation()&&show_custom()&&mode_count()==5);
  ctx.modes_mask=8; assert(!show_home()&&show_vacation()&&!show_custom()&&mode_count()==1);
  ctx.modes_mask=7; assert(!show_vacation()&&!show_custom()&&mode_count()==3);
  ctx.state="armed_vacation"; ctx.mode="vacation"; assert(is_armed_state(ctx.state)&&state_color()==COL_VACATION&&state_icon()==VIGIL_ICON_VACATION&&state_title()=="Vacation");
  ctx.state="armed_custom_bypass"; ctx.mode="custom"; assert(is_armed_state(ctx.state)&&state_color()==COL_CUSTOM&&state_icon()==VIGIL_ICON_CUSTOM&&state_title()=="Custom");
  assert(is_arm_action(ARM_VACATION)&&is_arm_action(ARM_CUSTOM)&&is_arm_action(ARM_HOME)&&!is_arm_action(DISARM)&&!is_arm_action(INFO));
  assert(std::string(arm_mode_name(ARM_VACATION))=="vacation"&&std::string(arm_mode_name(ARM_CUSTOM))=="custom"&&std::string(arm_mode_name(ARM_NIGHT))=="night");
  assert(keypad_route(true, ARM_VACATION)==2 && keypad_route(true, ARM_CUSTOM)==2);  // armed in the meantime: the keypad closes
  ctx.state="disarmed"; assert(keypad_route(true, ARM_CUSTOM)==0);
  ctx.last_alarm="14:03 Front door > Hall"; assert(state_sub(0).find("Last alarm: 14:03 Front door > Hall")!=std::string::npos);
  ctx.last_alarm=""; assert(state_sub(0).find("Last alarm")==std::string::npos);
  ctx.bypassed="Broken window"; assert(state_sub(0).find("Bypassed: Broken window")!=std::string::npos);
  ctx.bypassed=""; assert(state_sub(0).find("Bypassed")==std::string::npos);
  ctx.state="triggered"; ctx.cause="alarm24"; assert(cause_text()=="24-hour alarm"); ctx.cause="silent24"; assert(cause_text()=="Silent alarm");
  // 0.6.0: partitions. One partition on this panel while the house has more: a line with the name, no buttons.
  ctx=Context(); ctx.lang=EN; ctx.ha_connected=true; ctx.profile_version=PROFILE_VERSION; ctx.sensor_list=LIST_ALWAYS; ctx.state="disarmed"; ctx.modes_mask=2;
  assert(part_count()==0 && !parts_visible() && !parts_switch() && sel_name()=="");
  ctx.partition_list="p_gar|Garage|disarmed"; ctx.part_total=1; assert(!parts_visible());  // the house is one partition: nothing to say
  ctx.part_total=2; assert(parts_visible() && !parts_switch() && part_count()==1 && sel_id()=="p_gar" && sel_name()=="Garage");
  assert(chip_target(0)=="" && chip_target(4)=="" && state_title()=="Disarmed");  // no buttons, and no name in the title
  // More than one: a button for each, then "all"; the title names what is on the screen
  ctx.partition_list="main|Home|armed_away\np_gar|Garage|disarmed\nall||armed_away|mixed"; ctx.sel="p_gar"; ctx.default_part="p_gar";
  assert(parts_switch() && part_count()==2 && part_rows(true).size()==3 && part_rows(false).size()==2);
  assert(chip_target(0)=="main" && chip_target(1)=="p_gar" && chip_target(2)=="" && chip_target(4)=="all");
  assert(part_rows(true)[2].id=="all" && part_rows(true)[2].mixed && part_rows(true)[2].state=="armed_away" && part_rows(true)[0].name=="Home");
  assert(state_title()=="Garage: Disarmed" && sel_name()=="Garage");
  ctx.sel=""; assert(sel_id()=="main");  // Vigil says nothing: the first
  // Six partitions: arrows, four per page, "All" after the last partition (here on the second page, in third place)
  ctx.partition_list="a|A|disarmed\nb|B|disarmed\nc|C|disarmed\nd|D|disarmed\ne|E|disarmed\nf|F|disarmed\nall||disarmed"; ctx.sel="a"; ctx.chip_page=0; ctx.page_sel="";
  assert(parts_paged() && part_pages()==2 && chip_target(0)=="a" && chip_target(3)=="d" && chip_target(4)=="");
  ctx.chip_page=1; assert(chip_target(0)=="e" && chip_target(1)=="f" && chip_target(2)=="" && chip_target(4)=="all");
  ctx.sel="all"; ctx.chip_page=0; ctx.page_sel=""; sync_chip_page(); assert(chip_page_now()==1 && chip_target(4)=="all");  // "All" chosen elsewhere: its page comes into view
  // Eight: the last page is full of partitions, so "All" is alone on a third
  ctx.partition_list="a|A|disarmed\nb|B|disarmed\nc|C|disarmed\nd|D|disarmed\ne|E|disarmed\nf|F|disarmed\ng|G|disarmed\nh|H|disarmed\nall||disarmed"; ctx.sel="a"; ctx.chip_page=1; ctx.page_sel="";
  assert(part_pages()==3 && chip_target(3)=="h" && chip_target(4)=="");
  ctx.chip_page=2; assert(chip_target(0)=="" && chip_target(4)=="all");
  ctx.partition_list="main|Home|armed_away\np_gar|Garage|disarmed\nall||armed_away|mixed"; ctx.sel="p_gar"; ctx.chip_page=0; ctx.page_sel="";
  // The button on the sensors page: the partitions, then "Always on", then "All", round again
  ctx.sensors_always="x"; ctx.sel="main"; ctx.sens_always=false;
  assert(next_part_id()=="p_gar"); ctx.sel="p_gar"; assert(next_part_id()=="always");
  ctx.sens_always=true; assert(next_part_id()=="all"); ctx.sens_always=false; ctx.sel="all"; assert(next_part_id()=="main");
  ctx.sensors_always=""; ctx.sel="p_gar"; assert(next_part_id()=="all");
  ctx.sel="all"; assert(sel_name()=="All" && !mixed_now());  // only with the flag
  // "All" with the partitions in different states: Mixed, arm what is not armed, and disarm; not while it is going off
  ctx.mixed=true; ctx.state="armed_away"; ctx.modes_mask=3;
  assert(mixed_now() && state_title()=="All: Mixed" && state_color()==COL_WARN && state_icon()==VIGIL_ICON_SHIELD_ALERT);
  assert(show_home()&&show_away()&&!show_night()&&show_disarm() && state_sub(0)=="Home: Away, Garage: Disarmed");
  ctx.state="triggered"; assert(!mixed_now() && !show_home() && show_disarm() && state_title()=="All: ALARM");
  ctx.state="armed_away"; ctx.mixed=false; assert(!mixed_now() && !show_home() && show_disarm() && state_title()=="All: Away");
  // the colours of the buttons come from the states of the partitions
  assert(color_of_state("disarmed")==COL_OK && color_of_state("armed_home")==COL_HOME && color_of_state("nonsense")==COL_OFF);
  // back to the default after the time Vigil says, not while it counts down or goes off, not when it is there already
  ctx.sel="main"; ctx.state="disarmed"; ctx.return_seconds=30;
  assert(!should_return_to_default(29000) && should_return_to_default(30000) && should_return_to_default(60000));
  ctx.return_seconds=0; assert(!should_return_to_default(600000)); ctx.return_seconds=30;
  ctx.sel="p_gar"; assert(!should_return_to_default(60000));
  ctx.sel="main"; for (auto st : {"arming","pending","triggered"}) { ctx.state=st; assert(!should_return_to_default(60000)); }
  ctx.state="armed_home"; assert(should_return_to_default(60000)); ctx.default_part=""; assert(!should_return_to_default(60000));
  ctx.default_part="p_gar"; ctx.partition_list="p_gar|Garage|disarmed"; ctx.sel="p_gar"; assert(!should_return_to_default(60000));  // one partition: nothing to switch
  // the sensor list of a panel with partitions has a fifth field (the partition): the panel reads the first four
  ctx.sensors="Door|binary_sensor.door|open|1|main\nSmoke|binary_sensor.smoke|closed|0|\n"; assert(sensor_count()==2 && row_at(0,0).bypassable && !row_at(0,1).bypassable && row_at(0,0).status=="open");
  std::cout << "ok\n";
}
