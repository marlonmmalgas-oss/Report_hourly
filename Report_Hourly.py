import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

SAVE_FILE = "vessel_report.json"
SA_TZ = ZoneInfo("Africa/Johannesburg")

# ----------------- Utilities -----------------
def load_persistent():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_persistent(data: dict):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Failed to save data: {e}")

def parse_time_str(hhmm: str):
    try:
        return datetime.strptime(hhmm, "%H:%M").time()
    except Exception:
        return time(0, 0)

def today_sa_str():
    return datetime.now(SA_TZ).strftime("%d/%m/%Y")

def build_24h_slots(start_first: int = 6):
    slots = []
    for k in range(24):
        start = (start_first + k) % 24
        end = (start + 1) % 24
        slots.append(f"{start:02d}h00 - {end:02d}h00")
    return slots

def fmt_cols(label_w, c1_w, c2_w, label, v1, v2):
    # Force all columns to be strings with fixed width
    return f"{label:<{label_w}}{str(v1):>{c1_w}}{str(v2):>{c2_w}}"

# ----------------- Load persistent state -----------------
persist = load_persistent()
defaults = {
    "vessel_name": persist.get("vessel_name", "MSC NILA"),
    "berthed_date": persist.get("berthed_date", date.today().isoformat()),
    "berthed_time": persist.get("berthed_time", "10:55"),
    "first_lift": persist.get("first_lift", "18h25"),
    "last_lift": persist.get("last_lift", "10h31"),
    "planned_load": persist.get("planned_load", 687),
    "planned_disch": persist.get("planned_disch", 38),
    "planned_restow_load": persist.get("planned_restow_load", 13),
    "planned_restow_disch": persist.get("planned_restow_disch", 13),
    "opening_load": persist.get("opening_load", 0),
    "opening_disch": persist.get("opening_disch", 0),
    "opening_restow_load": persist.get("opening_restow_load", 0),
    "opening_restow_disch": persist.get("opening_restow_disch", 0),
    "last_hour": persist.get("last_hour", "06h00 - 07h00"),
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
S = st.session_state

# ----------------- UI -----------------
st.set_page_config(page_title="Vessel Hourly Moves", layout="wide")
st.title("Vessel Hourly Moves Tracker")

# Vessel info
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", value=S["vessel_name"])

# Berthed Date/Time
berthed_date_input = st.date_input("Berthed Date", value=date.fromisoformat(S["berthed_date"]))
berthed_time_input = st.text_input("Berthed Time (HHhMM)", value=S["berthed_time"])

# First / Last Lift (manual input)
first_lift_input = st.text_input("First Lift (HHhMM)", value=S["first_lift"])
last_lift_input = st.text_input("Last Lift (HHhMM)", value=S["last_lift"])

# Plan totals & opening balances
with st.expander("Plan Totals & Opening Balance (internal)", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        planned_load = st.number_input("Planned Load", min_value=0, value=int(S["planned_load"]))
        planned_disch = st.number_input("Planned Discharge", min_value=0, value=int(S["planned_disch"]))
        planned_restow_load = st.number_input("Planned Restow Load", min_value=0, value=int(S["planned_restow_load"]))
        planned_restow_disch = st.number_input("Planned Restow Discharge", min_value=0, value=int(S["planned_restow_disch"]))
    with c2:
        opening_load = st.number_input("Opening Load (Deduction)", min_value=0, value=int(S["opening_load"]))
        opening_disch = st.number_input("Opening Discharge (Deduction)", min_value=0, value=int(S["opening_disch"]))
        opening_restow_load = st.number_input("Opening Restow Load (Deduction)", min_value=0, value=int(S["opening_restow_load"]))
        opening_restow_disch = st.number_input("Opening Restow Discharge (Deduction)", min_value=0, value=int(S["opening_restow_disch"]))

# Hourly dropdown
st.header("Hourly Time")
hours_list = build_24h_slots(6)
default_hour = S.get("last_hour", "06h00 - 07h00")
if default_hour not in hours_list:
    default_hour = "06h00 - 07h00"
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# ----------------- Hourly Moves Input -----------------
st.header(f"Hourly Moves Input ({hourly_time})")
c1, c2, c3, c4 = st.columns(4)
with c1:
    fwd_load = st.number_input("FWD Load", min_value=0, value=0)
    fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0)
with c2:
    mid_load = st.number_input("MID Load", min_value=0, value=0)
    mid_disch = st.number_input("MID Discharge", min_value=0, value=0)
with c3:
    aft_load = st.number_input("AFT Load", min_value=0, value=0)
    aft_disch = st.number_input("AFT Discharge", min_value=0, value=0)
with c4:
    poop_load = st.number_input("POOP Load", min_value=0, value=0)
    poop_disch = st.number_input("POOP Discharge", min_value=0, value=0)

# Restows
r1, r2, r3, r4 = st.columns(4)
with r1:
    fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
    fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)
with r2:
    mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
    mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)
with r3:
    aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
    aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)
with r4:
    poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)
    poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

# Hatch moves
h1, h2, h3 = st.columns(3)
with h1:
    hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
    hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
with h2:
    hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
    hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
with h3:
    hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)
    hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# ----------------- Calculations -----------------
def calc_done_remain(planned, opening, done_inputs):
    done_total = sum(done_inputs) + opening
    remain = max(planned - done_total, 0)
    return done_total, remain

done_load_total, remain_load = calc_done_remain(planned_load, opening_load, [fwd_load, mid_load, aft_load, poop_load])
done_disch_total, remain_disch = calc_done_remain(planned_disch, opening_disch, [fwd_disch, mid_disch, aft_disch, poop_disch])
done_restow_load_total, remain_restow_load = calc_done_remain(planned_restow_load, opening_restow_load, [fwd_restow_load, mid_restow_load, aft_restow_load, poop_restow_load])
done_restow_disch_total, remain_restow_disch = calc_done_remain(planned_restow_disch, opening_restow_disch, [fwd_restow_disch, mid_restow_disch, aft_restow_disch, poop_restow_disch])
# ----------------- Build WhatsApp Template -----------------
st.header("WhatsApp Template Preview")

def build_template():
    lines = []
    lines.append(f"{S['vessel_name']}")
    lines.append(f"Berthed {berthed_date_input.strftime('%d/%m/%Y')} @ {berthed_time_input}")
    lines.append("")
    lines.append(f"First Lift @ {first_lift_input}")
    lines.append(f"Last lift  @ {last_lift_input}")
    lines.append("")
    lines.append(f"{hourly_time}")
    lines.append("_________________________")
    lines.append("   *HOURLY MOVES*")
    lines.append("_________________________")
    lines.append("*Crane Moves*")
    lines.append(fmt_cols(10, 10, 10, "", "Load", "Discharge"))
    lines.append(fmt_cols(10, 10, 10, "FWD", fwd_load, fwd_disch))
    lines.append(fmt_cols(10, 10, 10, "MID", mid_load, mid_disch))
    lines.append(fmt_cols(10, 10, 10, "AFT", aft_load, aft_disch))
    lines.append(fmt_cols(10, 10, 10, "POOP", poop_load, poop_disch))
    lines.append("_______________________")
    lines.append("*Restows*")
    lines.append(fmt_cols(10, 10, 10, "", "Load", "Discharge"))
    lines.append(fmt_cols(10, 10, 10, "FWD", fwd_restow_load, fwd_restow_disch))
    lines.append(fmt_cols(10, 10, 10, "MID", mid_restow_load, mid_restow_disch))
    lines.append(fmt_cols(10, 10, 10, "AFT", aft_restow_load, aft_restow_disch))
    lines.append(fmt_cols(10, 10, 10, "POOP", poop_restow_load, poop_restow_disch))
    lines.append("_______________________")
    lines.append("      *CUMULATIVE*")
    lines.append("_______________________")
    lines.append(fmt_cols(10, 10, 10, "Plan.", planned_load, planned_disch))
    lines.append(fmt_cols(10, 10, 10, "Done", done_load_total, done_disch_total))
    lines.append(fmt_cols(10, 10, 10, "Remain", remain_load, remain_disch))
    lines.append("________________________")
    lines.append("*Restows*")
    lines.append(fmt_cols(10, 10, 10, "Plan", planned_restow_load, planned_restow_disch))
    lines.append(fmt_cols(10, 10, 10, "Done", done_restow_load_total, done_restow_disch_total))
    lines.append(fmt_cols(10, 10, 10, "Remain", remain_restow_load, remain_restow_disch))
    lines.append("_______________________")
    lines.append("*Hatch Moves*")
    lines.append(fmt_cols(10, 10, 10, "", "Open", "Close"))
    lines.append(fmt_cols(10, 10, 10, "FWD", hatch_fwd_open, hatch_fwd_close))
    lines.append(fmt_cols(10, 10, 10, "MID", hatch_mid_open, hatch_mid_close))
    lines.append(fmt_cols(10, 10, 10, "AFT", hatch_aft_open, hatch_aft_close))
    lines.append("_________________________")
    lines.append("*Gear boxes*")
    lines.append("________________________")
    lines.append("*Idle*")
    return "\n".join(lines)

template_text = build_template()
st.text_area("WhatsApp Template", value=template_text, height=600)

# ----------------- Send to WhatsApp -----------------
st.header("Send WhatsApp Message")
wa_input = st.text_input("WhatsApp Number or Group Invite Link (with https://wa.me/ or https://chat.whatsapp.com/)")
if st.button("Open in WhatsApp"):
    if wa_input:
        url = f"{wa_input}?text={urllib.parse.quote(template_text)}"
        st.markdown(f"[Click here to open WhatsApp]({url})", unsafe_allow_html=True)
    else:
        st.error("Enter a valid number (e.g., https://wa.me/27XXXXXXXXX) or group invite link")
        
# ----------------- Save State -----------------
S["vessel_name"] = vessel_name
S["berthed_date"] = berthed_date_input.isoformat()
S["berthed_time"] = berthed_time_input
S["first_lift"] = first_lift_input
S["last_lift"] = last_lift_input
S["planned_load"] = planned_load
S["planned_disch"] = planned_disch
S["planned_restow_load"] = planned_restow_load
S["planned_restow_disch"] = planned_restow_disch
S["opening_load"] = opening_load
S["opening_disch"] = opening_disch
S["opening_restow_load"] = opening_restow_load
S["opening_restow_disch"] = opening_restow_disch
S["last_hour"] = hourly_time
save_persistent(S)