import os
import json
import urllib.parse
from datetime import datetime, date, time
from zoneinfo import ZoneInfo

import streamlit as st

SAVE_FILE = "vessel_report.json"
SA_TZ = ZoneInfo("Africa/Johannesburg")

# ---------- load / init persistent state ----------
def load_state():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # defaults
    return {
        # persistent editable fields
        "vessel_name": "MSC NILA",
        "berthed_date": None,             # ISO date "YYYY-MM-DD"
        "berthed_time": "10:55",          # "HH:MM"
        "first_lift_time": "18:25",       # "HH:MM"
        "last_lift_time": "10:31",        # "HH:MM"

        "planned_load": 687,
        "planned_disch": 38,
        "planned_restow_load": 13,
        "planned_restow_disch": 13,

        "opening_load": 0,
        "opening_disch": 0,
        "opening_restow_load": 0,
        "opening_restow_disch": 0,

        "last_hour": "06h00 - 07h00",

        # cumulative done totals
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
    }

def save_state(state):
    with open(SAVE_FILE, "w") as f:
        json.dump(state, f)

S = load_state()

# ---------- helpers ----------
def hfmt_h(lower: bool, t: time) -> str:
    # "18h25" (lower=True) or "10H55" (lower=False)
    h = f"{t.hour:02d}"
    sep = "h" if lower else "H"
    return f"{h}{sep}{t.minute:02d}"

def today_sa_str() -> str:
    return datetime.now(SA_TZ).strftime("%d/%m/%Y")

def date_to_str(d: date) -> str:
    return d.strftime("%d/%m/%Y")

def parse_time_str(hhmm: str) -> time:
    try:
        h, m = hhmm.split(":")
        return time(int(h), int(m))
    except Exception:
        return time(0, 0)

def build_24h_slots(start_first: int = 6):
    slots = []
    for k in range(24):
        start = (start_first + k) % 24
        end = (start + 1) % 24
        slots.append(f"{start:02d}h00 - {end:02d}h00")
    return slots

def fmt_line_cols(label_w, c1_w, c2_w, label, v1, v2):
    # right-align numbers, keep spacing consistent
    return f"{label:<{label_w}}{str(v1):>{c1_w}}{str(v2):>{c2_w}}"

# ---------- UI ----------
st.title("Vessel Hourly Moves Tracker")

# Vessel info
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", S["vessel_name"])

# Berthed (date + time)
colb1, colb2 = st.columns(2)
with colb1:
    default_date = date.fromisoformat(S["berthed_date"]) if S["berthed_date"] else date.today()
    berthed_date = st.date_input("Berthed Date", value=default_date)
with colb2:
    berthed_time = st.time_input("Berthed Time", value=parse_time_str(S["berthed_time"]))

# First/Last Lift (time only)
coll1, coll2 = st.columns(2)
with coll1:
    first_lift_time = st.time_input("First Lift (Time Only)", value=parse_time_str(S["first_lift_time"]))
with coll2:
    last_lift_time = st.time_input("Last Lift (Time Only)", value=parse_time_str(S["last_lift_time"]))

# Plan & Opening (internal only)
with st.expander("Plan Totals & Opening Balance (internal – affects calculations only)"):
    c1, c2 = st.columns(2)
    with c1:
        planned_load = st.number_input("Planned Load", value=int(S["planned_load"]), min_value=0)
        planned_disch = st.number_input("Planned Discharge", value=int(S["planned_disch"]), min_value=0)
        planned_restow_load = st.number_input("Planned Restow Load", value=int(S["planned_restow_load"]), min_value=0)
        planned_restow_disch = st.number_input("Planned Restow Discharge", value=int(S["planned_restow_disch"]), min_value=0)
    with c2:
        opening_load = st.number_input("Opening Load (Deduction)", value=int(S["opening_load"]), min_value=0)
        opening_disch = st.number_input("Opening Discharge (Deduction)", value=int(S["opening_disch"]), min_value=0)
        opening_restow_load = st.number_input("Opening Restow Load (Deduction)", value=int(S["opening_restow_load"]), min_value=0)
        opening_restow_disch = st.number_input("Opening Restow Discharge (Deduction)", value=int(S["opening_restow_disch"]), min_value=0)

# Hourly time dropdown (full 24h from 06h00)
st.header("Hourly Time")
hours_list = build_24h_slots(6)
default_hour = S["last_hour"] if S["last_hour"] in hours_list else "06h00 - 07h00"
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# Hourly inputs
st.header(f"Hourly Moves Input ({hourly_time})")

st.subheader("Crane Moves")
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

st.subheader("Restows")
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

st.subheader("Hatch Moves")
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

# WhatsApp sending
st.header("Send to WhatsApp")
whatsapp_number = st.text_input("Number with country code (e.g., 27761234567)")
force_monospace = st.checkbox("Force monospace in WhatsApp (perfect columns, disables bold)", value=False)

# ---------- on submit ----------
if st.button("Submit Hourly Moves"):
    # Update cumulative totals
    S["done_load"] += fwd_load + mid_load + aft_load + poop_load
    S["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    S["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    S["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    S["done_hatch_open"] += hatch_fwd_open + hatch_mid_open + hatch_aft_open
    S["done_hatch_close"] += hatch_fwd_close + hatch_mid_close + hatch_aft_close
    S["last_hour"] = hourly_time

    # Save persistent editable fields
    S["vessel_name"] = vessel_name
    S["berthed_date"] = berthed_date.isoformat()
    S["berthed_time"] = f"{berthed_time.hour:02d}:{berthed_time.minute:02d}"
    S["first_lift_time"] = f"{first_lift_time.hour:02d}:{first_lift_time.minute:02d}"
    S["last_lift_time"] = f"{last_lift_time.hour:02d}:{last_lift_time.minute:02d}"

    S["planned_load"] = int(planned_load)
    S["planned_disch"] = int(planned_disch)
    S["planned_restow_load"] = int(planned_restow_load)
    S["planned_restow_disch"] = int(planned_restow_disch)

    S["opening_load"] = int(opening_load)
    S["opening_disch"] = int(opening_disch)
    S["opening_restow_load"] = int(opening_restow_load)
    S["opening_restow_disch"] = int(opening_restow_disch)

    save_state(S)

    # Remaining totals (opening balances are deductions)
    remaining_load = S["planned_load"] - S["done_load"] - S["opening_load"]
    remaining_disch = S["planned_disch"] - S["done_disch"] - S["opening_disch"]
    remaining_restow_load = S["planned_restow_load"] - S["done_restow_load"] - S["opening_restow_load"]
    remaining_restow_disch = S["planned_restow_disch"] - S["done_restow_disch"] - S["opening_restow_disch"]

    # --- format strings for the template ---
    berthed_str = f"{date_to_str(berthed_date)} @ {hfmt_h(False, berthed_time)}"
    first_lift_str = hfmt_h(True, first_lift_time)
    last_lift_str = hfmt_h(True, last_lift_time)

    today_line = today_sa_str()

    # column widths
    # Crane/Restows tables
    lbl_w, col1_w, col2_w = 8, 7, 12  # label, Load, Discharge
    # Cumulative tables
    cum_lbl_w, cum_c1_w, cum_c2_w = 12, 7, 8

    # Headers/lines
    line = "_" * 25
    header_crane = fmt_line_cols(lbl_w, col1_w, col2_w, "", "Load", "Discharge")
    header_rest_dis = fmt_line_cols(lbl_w, col1_w, col2_w, "", "Load", "Discharge")
    header_cum = fmt_line_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "", "Load", "Disch")
    header_rest_cum = fmt_line_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "", "Load", "Disch")

    # Rows
    crane_lines = "\n".join([
        fmt_line_cols(lbl_w, col1_w, col2_w, "FWD", f"{fwd_load}", f"{fwd_disch}"),
        fmt_line_cols(lbl_w, col1_w, col2_w, "MID", f"{mid_load}", f"{mid_disch}"),
        fmt_line_cols(lbl_w, col1_w, col2_w, "AFT", f"{aft_load}", f"{aft_disch}"),
        fmt_line_cols(lbl_w, col1_w, col2_w, "POOP", f"{poop_load}", f"{poop_disch}"),
    ])

    restow_lines = "\n".join([
        fmt_line_cols(lbl_w, col1_w, col2_w, "FWD", f"{fwd_restow_load}", f"{fwd_restow_disch}"),
        fmt_line_cols(lbl_w, col1_w, col2_w, "MID", f"{mid_restow_load}", f"{mid_restow_disch}"),
        fmt_line_cols(lbl_w, col1_w, col2_w, "AFT", f"{aft_restow_load}", f"{aft_restow_disch}"),
        fmt_line_cols(lbl_w, col1_w, col2_w, "POOP", f"{poop_restow_load}", f"{poop_restow_disch}"),
    ])

    cum_lines = "\n".join([
        fmt_line_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Plan.", f"{S['planned_load']}", f"{S['planned_disch']}"),
        fmt_line_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Done", f"{S['done_load']}", f"{S['done_disch']}"),
        fmt_line_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Remain", f"{remaining_load}", f"{remaining_disch}"),
    ])

    restow_cum_lines = "\n".join([
        fmt_line_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Plan", f"{S['planned_restow_load']}", f"{S['planned_restow_disch']}"),
        fmt_line_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Done", f"{S['done_restow_load']}", f"{S['done_restow_disch']}"),
        fmt_line_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Remain", f"{remaining_restow_load}", f"{remaining_restow_disch}"),
    ])

    hatch_header = fmt_line_cols(lbl_w, col1_w, col2_w, "", "Open", "Close")
    hatch_lines = "\n".join([
        fmt_line_cols(lbl_w, col1_w, col2_w, "FWD", f"{hatch_fwd_open}", f"{hatch_fwd_close}"),
        fmt_line_cols(lbl_w, col1_w, col2_w, "MID", f"{hatch_mid_open}", f"{hatch_mid_close}"),
        fmt_line_cols(lbl_w, col1_w, col2_w, "AFT", f"{hatch_aft_open}", f"{hatch_aft_close}"),
    ])

    # --- final WhatsApp template (keeps your exact structure) ---
    template = (
f"""{vessel_name}
Berthed {berthed_str}

First Lift @ {first_lift_str}
Last Lift @ {last_lift_str}

{today_line}
{hourly_time}
{line}
   *HOURLY MOVES*
{line}
*Crane Moves*
{header_crane}
{crane_lines}
{line}
*Restows*
{header_rest_dis}
{restow_lines}
{line}
      *CUMULATIVE*
{line}
{header_cum}
{cum_lines}
{line}
*Restows*
{header_rest_cum}
{restow_cum_lines}
{line}
*Hatch Moves*
{hatch_header}
{hatch_lines}
{line}
*Gear boxes* 

{line}
*Idle*"""
    )

    # Preview in monospace so you can verify alignment
    st.code(template)

    # Build WhatsApp link
    msg = f"```{template}```" if force_monospace else template
    if whatsapp_number:
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(msg)}"
        st.markdown(f"[Tap to open WhatsApp with your message ready](<{wa_link}>)", unsafe_allow_html=True)

    st.success("Saved and updated. Copy the template above or use the WhatsApp link.")