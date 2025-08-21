import streamlit as st
import json
import os
import urllib.parse
from datetime import datetime
import pytz

SAVE_FILE = "vessel_report.json"

# Load or initialize cumulative data
def load_cumulative():
    default_data = {
        "done_load": 0,
        "done_disch": 0,
        "done_restow_load": 0,
        "done_restow_disch": 0,
        "done_hatch_open": 0,
        "done_hatch_close": 0,
        "last_hour": None,
        "vessel_name": "MSC NILA",
        "berthed_date": "14/08/2025 @ 10H55",
        "planned_load": 687,
        "planned_disch": 38,
        "planned_restow_load": 13,
        "planned_restow_disch": 13,
        "opening_load": 0,
        "opening_disch": 0,
        "opening_restow_load": 0,
        "opening_restow_disch": 0
    }
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
            for key in default_data:
                if key not in data:
                    data[key] = default_data[key]
            return data
        except (json.JSONDecodeError, ValueError):
            return default_data
    else:
        return default_data

cumulative = load_cumulative()

# Current South African Date
tz = pytz.timezone("Africa/Johannesburg")
today_date = datetime.now(tz).strftime("%d/%m/%Y")

st.title("Hourly Report by Marlon Malgas")

# Vessel Info
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", cumulative["vessel_name"])
berthed_date = st.text_input("Berthed Date", cumulative["berthed_date"])
first_lift = st.text_input("First Lift", "18h25")
last_lift = st.text_input("Last Lift", "10h31")

# Plan Totals & Opening Balance (internal only)
st.header("Plan Totals & Opening Balance (Internal Only)")
col1, col2 = st.columns(2)
with col1:
    planned_load = st.number_input("Planned Load", value=cumulative["planned_load"])
    planned_disch = st.number_input("Planned Discharge", value=cumulative["planned_disch"])
    planned_restow_load = st.number_input("Planned Restow Load", value=cumulative["planned_restow_load"])
    planned_restow_disch = st.number_input("Planned Restow Discharge", value=cumulative["planned_restow_disch"])
with col2:
    opening_load = st.number_input("Opening Load (Deduction)", value=cumulative["opening_load"])
    opening_disch = st.number_input("Opening Discharge (Deduction)", value=cumulative["opening_disch"])
    opening_restow_load = st.number_input("Opening Restow Load (Deduction)", value=cumulative["opening_restow_load"])
    opening_restow_disch = st.number_input("Opening Restow Discharge (Deduction)", value=cumulative["opening_restow_disch"])

# Hourly Dropdown
st.header("Hourly Time")
hours_list = []
for h in range(24):
    start_hour = h
    end_hour = (h + 1) % 24
    hours_list.append(f"{str(start_hour).zfill(2)}h00 - {str(end_hour).zfill(2)}h00")
default_hour = cumulative.get("last_hour") if cumulative.get("last_hour") in hours_list else "06h00 - 07h00"
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# Hourly Moves grouped by section
st.header(f"Hourly Moves Input ({hourly_time})")

# FWD
st.subheader("FWD")
fwd_load = st.number_input("FWD Load", min_value=0, value=0)
fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0)
fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0)
fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0)

# MID
st.subheader("MID")
mid_load = st.number_input("MID Load", min_value=0, value=0)
mid_disch = st.number_input("MID Discharge", min_value=0, value=0)
mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0)
mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0)

# AFT
st.subheader("AFT")
aft_load = st.number_input("AFT Load", min_value=0, value=0)
aft_disch = st.number_input("AFT Discharge", min_value=0, value=0)
aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0)
aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0)

# POOP
st.subheader("POOP")
poop_load = st.number_input("POOP Load", min_value=0, value=0)
poop_disch = st.number_input("POOP Discharge", min_value=0, value=0)
poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0)
poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0)

# Hatch Moves
st.subheader("Hatch Moves")
hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0)
hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0)
hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0)
hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0)
hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0)
hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0)

# WhatsApp
st.header("Send WhatsApp Message")
wa_type = st.radio("Send to:", ["Private Number", "Group Link"])
wa_input = st.text_input("Enter WhatsApp Number (with country code) or Group Invite Link")

if st.button("Update Template"):
    total_done_load = cumulative["done_load"] + fwd_load + mid_load + aft_load + poop_load
    total_done_disch = cumulative["done_disch"] + fwd_disch + mid_disch + aft_disch + poop_disch
    total_done_restow_load = cumulative["done_restow_load"] + fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    total_done_restow_disch = cumulative["done_restow_disch"] + fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch

    remaining_load = planned_load - total_done_load - opening_load
    remaining_disch = planned_disch - total_done_disch - opening_disch
    remaining_restow_load = planned_restow_load - total_done_restow_load - opening_restow_load
    remaining_restow_disch = planned_restow_disch - total_done_restow_disch - opening_restow_disch

    template = f"""{vessel_name}
Berthed {berthed_date}

First Lift @ {first_lift}
Last Lift  @ {last_lift}

{today_date}
{hourly_time}
_________________________
   *HOURLY MOVES*
_________________________
*Crane Moves*
           Load   Discharge
FWD        {fwd_load:>5}     {fwd_disch:>5}
MID        {mid_load:>5}     {mid_disch:>5}
AFT        {aft_load:>5}     {aft_disch:>5}
POOP       {poop_load:>5}     {poop_disch:>5}
_________________________
*Restows*
           Load   Discharge
FWD        {fwd_restow_load:>5}     {fwd_restow_disch:>5}
MID        {mid_restow_load:>5}     {mid_restow_disch:>5}
AFT        {aft_restow_load:>5}     {aft_restow_disch:>5}
POOP       {poop_restow_load:>5}     {poop_restow_disch:>5}
_________________________
      *CUMULATIVE*
_________________________
           Load   Disch
Plan       {planned_load:>5}      {planned_disch:>5}
Done       {total_done_load:>5}      {total_done_disch:>5}
Remain     {remaining_load:>5}      {remaining_disch:>5}
_________________________
*Restows*
           Load   Disch
Plan       {planned_restow_load:>5}      {planned_restow_disch:>5}
Done       {total_done_restow_load:>5}      {total_done_restow_disch:>5}
Remain     {remaining_restow_load:>5}      {remaining_restow_disch:>5}
_________________________
*Hatch Moves*
           Open   Close
FWD        {hatch_fwd_open:>5}      {hatch_fwd_close:>5}
MID        {hatch_mid_open:>5}      {hatch_mid_close:>5}
AFT        {hatch_aft_open:>5}      {hatch_aft_close:>5}
_________________________
*Gear boxes*

_________________________
*Idle*
"""

    st.code(template)  # Show template in monospace

    # --- Send to WhatsApp ---
    if wa_input:
        wa_template = f"```{template}```"  # Force monospace in WhatsApp
        if wa_type == "Private Number":
            wa_link = f"https://wa.me/{wa_input}?text={urllib.parse.quote(wa_template)}"
        else:  # Group link
            wa_link = f"{wa_input}"  # User should paste full group invite link

        st.markdown(f"[Open WhatsApp]({wa_link})", unsafe_allow_html=True)

# --- Save cumulative on app exit ---
def save_cumulative():
    cumulative["done_load"] += fwd_load + mid_load + aft_load + poop_load
    cumulative["done_disch"] += fwd_disch + mid_disch + aft_disch + poop_disch
    cumulative["done_restow_load"] += fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    cumulative["done_restow_disch"] += fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    cumulative["last_hour"] = hourly_time

    # Save editable persistent fields
    cumulative.update({
        "vessel_name": vessel_name,
        "berthed_date": berthed_date,
        "planned_load": planned_load,
        "planned_disch": planned_disch,
        "planned_restow_load": planned_restow_load,
        "planned_restow_disch": planned_restow_disch,
        "opening_load": opening_load,
        "opening_disch": opening_disch,
        "opening_restow_load": opening_restow_load,
        "opening_restow_disch": opening_restow_disch
    })

    with open(SAVE_FILE, "w") as f:
        json.dump(cumulative, f)

# Save automatically when script exits
save_cumulative()