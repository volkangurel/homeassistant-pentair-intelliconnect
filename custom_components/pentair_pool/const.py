"""Constants for pentair_pool.

Values reverse-engineered from com.pentair.pentairhome v4.2.18; see
the ENDPOINTS.md document in the development notes for the source
captures and rationale for each constant.
"""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

# Integration metadata
DOMAIN = "pentair_pool"
ATTRIBUTION = "Data provided by Pentair Cloud"

# Platform parallel updates - applied to all platforms.
# Writes are serialized so a rapid double-tap of a switch can't reorder.
PARALLEL_UPDATES = 1

# Default polling cadence (seconds). The WebSocket pushes carry most state
# changes within a second; this is the fallback for missed pushes.
DEFAULT_POLL_INTERVAL_SECONDS = 60

# Legacy options-flow defaults (kept so the blueprint's options_flow imports
# still resolve). Not yet wired to anything functional.
DEFAULT_UPDATE_INTERVAL_HOURS = 1
DEFAULT_ENABLE_DEBUGGING = False

# --- Cognito (US pool) --------------------------------------------------------
COGNITO_REGION = "us-west-2"
COGNITO_USER_POOL_ID = "us-west-2_lbiduhSwD"
COGNITO_CLIENT_ID = "3de110o697faq7avdchtf07h4v"
IDENTITY_POOL_ID = "us-west-2:6f950f85-af44-43d9-b690-a431f753e9aa"

# EU pool (discovered in decompile; not yet exercised).
COGNITO_REGION_EU = "eu-west-1"
COGNITO_USER_POOL_ID_EU = "eu-west-1_rsBGJFuRd"

# --- Pentair Cloud API --------------------------------------------------------
API_HOST = "api.pentair.cloud"
API_BASE = f"https://{API_HOST}"
API_KEY_UNAUTH = "p4u60la7xH7q4aat3Tzrq9BfspTOslIs6oXzIhuS"
DETECT_USER_URL = f"{API_BASE}/user2/user2-service/unauth/detectUser"

# --- Real-time WebSocket ------------------------------------------------------
WS_URL = "wss://g44t970cbi.execute-api.us-west-2.amazonaws.com/prod"

# --- Token refresh safety margin (seconds) -----------------------------------
TOKEN_REFRESH_MARGIN_SECONDS = 60

# --- IntelliConnect (PIF0) field codes ---------------------------------------
FIELD_RA0 = "ra0"  # Relay1_Manual_Schedule (pump on/off + schedule mode)
FIELD_RA1 = "ra1"  # Relay1_Start_Time (UTC seconds-of-day)
FIELD_RA2 = "ra2"  # Relay1_End_Time
FIELD_RA3 = "ra3"  # Relay1_Timer (configured timer duration, seconds)
FIELD_RA4 = "ra4"  # Relay1_Power (watts, RO)
FIELD_RAS0 = "ras0"  # Relay1_Timer_Status (live pump-stop countdown, RO seconds)
FIELD_P1 = "p1"  # Relay1_Egg_Timer
FIELD_HTD1 = "htd1"  # Heater_Mode
FIELD_HTD2 = "htd2"  # Heater_SetPoint (tenths of degF)
FIELD_HTD13 = "htd13"  # Heater aux flag (written with htd1=0 on OFF)
FIELD_HTD14 = "htd14"  # Heater_Cooldown (seconds, RO)
FIELD_ICD1 = "icd1"  # Chlor_Set_Percentage
FIELD_ICD2 = "icd2"  # Boost_Mode_RPM (one-shot)
FIELD_ICD3 = "icd3"  # Boost_Mode_Timer (one-shot, seconds)
FIELD_ICS1 = "ics1"  # Chlor_Percentage (actual, RO)
FIELD_ICS2 = "ics2"  # Chlor_Salt_Value_PPM (RO)
FIELD_ICS3 = "ics3"  # Chlor_Error_Message (RO)
FIELD_ICS9 = "ics9"  # Chlor_Status_Call_Temp (RO)
FIELD_ICS11 = "ics11"  # Chlor_Status_Call_VerNum (RO)
FIELD_ICS12 = "ics12"  # Chlor_Device_Name (RO)
FIELD_ICS13 = "ics13"  # Chlor_BoostTimer_Status (countdown, RO)
FIELD_ICS15 = "ics15"  # Chlor_Operation_Hours (RO)

# Temperature sensors (whole degrees F, NOT tenths like htd2)
FIELD_T0 = "t0"  # Current_Water_Temp (RO, degF integer)
FIELD_T1 = "t1"  # FP_Outside_Temp (RO, degF integer, S16 so signed)

# IntelliFlo VSF variable-speed pump on the controller's RS485 bus (RO).
# Present only when the controller reports a VSF pump (device_info lists it
# under "IntelliFlo pumps"). Values are raw integers/strings from the cloud.
FIELD_IFS1 = "ifs1"  # Running_Stopped (0-10; observed 10 while running, semantics undocumented)
FIELD_IFS2 = "ifs2"  # Active_Menu (0-15)
FIELD_IFS3 = "ifs3"  # Actual_Power (U16, watts)
FIELD_IFS4 = "ifs4"  # Actual_Speed_Status (U16, RPM)
FIELD_IFS5 = "ifs5"  # VFD_Software (firmware x100, e.g. 211 -> 2.11)
FIELD_IFS6 = "ifs6"  # Actual_Flow_VSF (U16, gallons per minute)
FIELD_IFS18 = "ifs18"  # Alarm (U32 bitfield/code; 0 = no alarm; not decoded)
FIELD_IFS27 = "ifs27"  # Duration (minutes, 0-1440)
FIELD_IFS28 = "ifs28"  # VFD_Model (string, e.g. "Intelli VSF")
FIELD_IFS29 = "ifs29"  # External_Control (0-32)
FIELD_IFS30 = "ifs30"  # temp_alarm_higher_than_150

# IntelliFlo VSF on RS485 -- pump config (RW). Speeds in RPM.
FIELD_IFD4 = "ifd4"  # Speed1_Set_Speed
FIELD_IFD5 = "ifd5"  # Speed2_Set_Speed
FIELD_IFD6 = "ifd6"  # Speed3_Set_Speed
FIELD_IFD7 = "ifd7"  # Speed4_Set_Speed
FIELD_IFD29 = "ifd29"  # Program1_Set_Speed
FIELD_IFD30 = "ifd30"  # Program2_Set_Speed
FIELD_IFD31 = "ifd31"  # Program3_Set_Speed
FIELD_IFD32 = "ifd32"  # Program4_Set_Speed
VSF_MIN_RPM = 450
VSF_MAX_RPM = 3450
VSF_RPM_STEP = 5

# Controller Wi-Fi link (RO)
FIELD_ECS2 = "ecs2"  # rfrssi (dBm)
FIELD_ECS20 = "ecs20"  # WiFiLevel (0-5 bars)

# --- ra0 state values (filter pump state machine) ----------------------------
RA0_OFF_NO_SCHEDULE = "0"
RA0_ON_NO_SCHEDULE = "1"
RA0_OFF_SCHEDULED = "2"
RA0_ON_SCHEDULED = "3"
RA0_TIMER_DONE_SCHEDULED = "4"

# --- htd1 values --------------------------------------------------------------
# Empirically confirmed by cross-referencing the Pentair Home app's UI:
#   htd1=1 -> app shows "Auto Idle"  (heater enabled, monitoring, NOT firing)
#   htd1=3 -> app shows "Heating"    (heater actively firing)
# Earlier code had these swapped. Mode 1 is also what we WRITE to turn the
# heater on, because that puts it in auto monitoring; the firmware itself
# transitions 1->3 when it decides to fire (water below setpoint AND pump
# flow available). Values 2 and 4 are firmware-managed and rarely seen.
HTD1_OFF = "0"
HTD1_AUTO_IDLE = "1"
HTD1_HEATING = "3"

HTD1_LABELS = {
    "0": "Off",
    "1": "Auto idle",
    "2": "Schedule running",  # tentative
    "3": "Heating",
    "4": "Schedule will run",  # tentative
}

# --- Salt cell boost ---------------------------------------------------------
BOOST_RPM = "450"
