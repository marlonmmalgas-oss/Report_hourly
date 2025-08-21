# vessel_hourly_app.py
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

def fmt_h_mm_lower(t: time):
    return f"{t.hour:02d}h{t.minute:02d}"

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
    return f"{label:<{label_w}}{str(v1):>{c1_w}}{str(v2):>{c2_w}}"

# ----------------- Load persistent state -----------------
persist = load_persistent()
defaults = {
    "vessel_name": persist.get("vessel_name", "MSC NILA"),
    "berthed_date": persist.get("berthed_date", date.today().isoformat()),
    "berthed_time": persist.get("berthed_time", "10:55"),
    "first_lift": persist.get("first_lift", "18:25"),
    "last_lift": persist.get("last_lift", "10:31"),
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

# Safe Berthed Date
berthed_date_str = S.get("berthed_date", "")
try:
    berthed_date_value = date.fromisoformat(berthed_date_str)
except Exception:
    berthed_date_value = date.today()
berthed_date_input = st.date_input("Berthed Date", value=berthed_date_value)

# Safe Berthed Time
berthed_time_str = S.get("berthed_time", "")
try:
    berthed_time_value = parse_time_str(berthed_time_str)
except Exception:
    berthed_time_value = time(10, 55)
berthed_time_input = st.time_input("Berthed Time", value=berthed_time_value)

# First / Last Lift
first_lift_str = S.get("first_lift", "")
try:
    first_lift_value = parse_time_str(first_lift_str)
except Exception:
    first_lift_value = time(18, 25)
first_lift_input = st.time_input("First Lift (time only)", value=first_lift_value)

last_lift_str = S.get("last_lift", "")
try:
    last_lift_value = parse_time_str(last_lift_str)
except Exception:
    last_lift_value = time(10, 31)
last_lift_input = st.time_input("Last Lift (time only)", value=last_lift_value)

# Plan totals & opening balances
with st.expander("Plan Totals & Opening Balance (internal — affects calculations only)", expanded=True):
    pcol1, pcol2 = st.columns(2)
    with pcol1:
        planned_load = st.number_input("Planned Load", min_value=0, value=int(S["planned_load"]))
        planned_disch = st.number_input("Planned Discharge", min_value=0, value=int(S["planned_disch"]))
        planned_restow_load = st.number_input("Planned Restow Load", min_value=0, value=int(S["planned_restow_load"]))
        planned_restow_disch = st.number_input("Planned Restow Discharge", min_value=0, value=int(S["planned_restow_disch"]))
    with pcol2:
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

# ----------------- Build WhatsApp template -----------------
def build_template():
    lines = []
    lines.append(f"{vessel_name}")
    lines.append(f"Berthed {berthed_date_input.strftime('%d/%m/%Y')} @ {berthed_time_input.strftime('%Hh%M')}")
    lines.append("")
    lines.append(f"First Lift @ {first_lift_input.strftime('%Hh%M')}")
    lines.append(f"Last Lift @  {last_lift_input.strftime('%Hh%M')}")
    lines.append("")
    lines.append(today_sa_str())
    lines.append(hourly_time)
    lines.append("_________________________")
    lines.append("   *HOURLY MOVES*")
    lines.append("_________________________")
    lines.append("*Crane Moves*")
    lines.append(fmt_cols(10,8,8,"Load","Discharge",""))
    lines.append(fmt_cols(10,8,8,"FWD",fwd_load,fwd_disch))
    lines.append(fmt_cols(10,8,8,"MID",mid_load,mid_disch))
    lines.append(fmt_cols(10,8,8,"AFT",aft_load,aft_disch))
    lines.append(fmt_cols(10,8,8,"POOP",poop_load,poop_disch))
    lines.append("_______________________")
    lines.append("*Restows*")
    lines.append(fmt_cols(10,8,8,"Load","Discharge",""))
    lines.append(fmt_cols(10,8,8,"FWD",fwd_restow_load,fwd_restow_disch))
    lines.append(fmt_cols(10,8,8,"MID",mid_restow_load,mid_restow_disch))
    lines.append(fmt_cols(10,8,8,"AFT",aft_restow_load,aft_restow_disch))
    lines.append(fmt_cols(10,8,8,"POOP",poop_restow_load,poop_restow_disch))
    lines.append("_______________________")
    lines.append("      *CUMULATIVE*")
    lines.append("_______________________")
    lines.append(fmt_cols(15,8,8,"Plan.",planned_load,planned_disch))
    lines.append(fmt_cols(15,8,8,"Done",done_load_total,done_disch_total))
    lines.append(fmt_cols(15,8,8,"Remain",remain_load,remain_disch))
    lines.append("________________________")
    lines.append("*Restows*")
    lines.append(fmt_cols(15,8,8,"Plan",planned_restow_load,planned_restow_disch))
    lines.append(fmt_cols(15,8,8,"Done",done_restow_load_total,done_restow_disch_total))
    lines.append(fmt_cols(15,8,8,"Remain",remain_restow_load,remain_restow_disch))
    lines.append("_______________________")
    lines.append("*Hatch Moves*")
    lines.append(fmt_cols(10,8,8,"Open","Close",""))
    lines.append(fmt_cols(10,8,8,"FWD",hatch_fwd_open,hatch_fwd_close))
    lines.append(fmt_cols(10,8,8,"MID",hatch_mid_open,hatch_mid_close))
    lines.append(fmt_cols(10,8,8,"AFT",hatch_aft_open,hatch_aft_close))
    lines.append("_________________________")
    lines.append("*Gear boxes*")
    lines.append("________________________")
    lines.append("*Idle*")
    return "\n".join(lines)

template_text = build_template()
st.subheader("WhatsApp Template Preview")
st.text_area("Template", value=template_text, height=600)

# ----------------- WhatsApp link (number or group) -----------------
st.subheader("Send to WhatsApp")
wa_choice = st.radio("Send to:", ["Private Number", "Group Invite Link"])
if wa_choice == "Private Number":
    phone_number = st.text_input("Enter WhatsApp number (with country code, e.g., 27831234567):")
    if phone_number:
        wa_url = f"https://wa.me/{phone_number}?text={urllib.parse.quote(template_text)}"
        st.markdown(f"[Open in WhatsApp]({wa_url})", unsafe_allow_html=True)
else:
    group_link = st.text_input("Enter WhatsApp group invite link:")
    if group_link:
        wa_url = f"{group_link}&text={urllib.parse.quote(template_text)}"
        st.markdown(f"[Open Group in WhatsApp]({wa_url})", unsafe_allow_html=True)

# ----------------- Save state -----------------
if st.button("Save Current State"):
    S.update({
        "vessel_name": vessel_name,
        "berthed_date": berthed_date_input.isoformat(),
        "berthed_time": berthed_time_input.strftime("%H:%M"),
        "first_lift": first_lift_input.strftime("%H:%M"),
        "last_lift": last_lift_input.strftime("%H:%M"),
        "planned_load": planned_load,
        "planned_disch": planned_disch,
        "planned_restow_load": planned_restow_load,
        "planned_restow_disch": planned_restow_disch,
        "opening_load": opening_load,
        "opening_disch": opening_disch,
        "opening_restow_load": opening_restow_load,
        "opening_restow_disch": opening_restow_disch,
        "last_hour": hourly_time
    })
    save_persistent(S)
    st.success("State saved successfully.")