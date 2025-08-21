# vessel_report_app.py
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
    """Return datetime.time from 'HH:MM' or fallback 00:00"""
    try:
        parts = hhmm.split(":")
        return time(int(parts[0]), int(parts[1]))
    except Exception:
        return time(0, 0)


def fmt_h_mm_lower(t: time):
    return f"{t.hour:02d}h{t.minute:02d}"


def fmt_h_MM_upper(t: time):
    return f"{t.hour:02d}H{t.minute:02d}"


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
    """Produce one line with fixed widths. Right-align numbers."""
    return f"{label:<{label_w}}{str(v1):>{c1_w}}{str(v2):>{c2_w}}"


# ----------------- Init persistent state -> st.session_state -----------------
persist = load_persistent()

# Ensure keys exist in session_state with safe defaults
defaults = {
    "vessel_name": persist.get("vessel_name", "MSC NILA"),
    "berthed_date": persist.get("berthed_date", date.today().isoformat()),
    "berthed_time": persist.get("berthed_time", "10:55"),
    "first_lift_time": persist.get("first_lift_time", "18:25"),
    "last_lift_time": persist.get("last_lift_time", "10:31"),
    "planned_load": persist.get("planned_load", 687),
    "planned_disch": persist.get("planned_disch", 38),
    "planned_restow_load": persist.get("planned_restow_load", 13),
    "planned_restow_disch": persist.get("planned_restow_disch", 13),
    "opening_load": persist.get("opening_load", 0),
    "opening_disch": persist.get("opening_disch", 0),
    "opening_restow_load": persist.get("opening_restow_load", 0),
    "opening_restow_disch": persist.get("opening_restow_disch", 0),
    "last_hour": persist.get("last_hour", "06h00 - 07h00"),
    # cumulative done totals
    "done_load": persist.get("done_load", 0),
    "done_disch": persist.get("done_disch", 0),
    "done_restow_load": persist.get("done_restow_load", 0),
    "done_restow_disch": persist.get("done_restow_disch", 0),
    "done_hatch_open": persist.get("done_hatch_open", 0),
    "done_hatch_close": persist.get("done_hatch_close", 0),
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Shortcut local alias
S = st.session_state

# ----------------- UI -----------------
st.set_page_config(page_title="Vessel Hourly Moves", layout="wide")
st.title("Hourly Report by Malgas")

# Vessel info
st.header("Vessel Info")
vessel_name = st.text_input("Vessel Name", value=S["vessel_name"])
col_date, col_time = st.columns(2)
with col_date:
    # Berthed date picker
    berthed_date_input = st.date_input("Berthed Date", value=date.fromisoformat(S["berthed_date"]))
with col_time:
    berthed_time_input = st.time_input(
        "Berthed Time",
        value=parse_time_str(S["berthed_time"])
    )

# First / Last lift (time only)
st.header("Lifts (time only)")
flt_col1, flt_col2 = st.columns(2)
with flt_col1:
    first_lift_time_input = st.time_input(
        "First Lift (time only)",
        value=parse_time_str(S["first_lift_time"])
    )
with flt_col2:
    last_lift_time_input = st.time_input(
        "Last Lift (time only)",
        value=parse_time_str(S["last_lift_time"])
    )

# Plan & Opening (internal only)
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

# Hourly time dropdown (full 24h starting at 06h)
st.header("Hourly Time")
hours_list = build_24h_slots(6)
default_hour = S.get("last_hour", "06h00 - 07h00")
if default_hour not in hours_list:
    default_hour = "06h00 - 07h00"
hourly_time = st.selectbox("Select Hourly Time", options=hours_list, index=hours_list.index(default_hour))

# Hourly inputs: Crane moves
st.header(f"Hourly Moves Input ({hourly_time})")
st.subheader("Crane Moves")
c1, c2, c3, c4 = st.columns(4)
with c1:
    fwd_load = st.number_input("FWD Load", min_value=0, value=0, key="ui_fwd_load")
    fwd_disch = st.number_input("FWD Discharge", min_value=0, value=0, key="ui_fwd_disch")
with c2:
    mid_load = st.number_input("MID Load", min_value=0, value=0, key="ui_mid_load")
    mid_disch = st.number_input("MID Discharge", min_value=0, value=0, key="ui_mid_disch")
with c3:
    aft_load = st.number_input("AFT Load", min_value=0, value=0, key="ui_aft_load")
    aft_disch = st.number_input("AFT Discharge", min_value=0, value=0, key="ui_aft_disch")
with c4:
    poop_load = st.number_input("POOP Load", min_value=0, value=0, key="ui_poop_load")
    poop_disch = st.number_input("POOP Discharge", min_value=0, value=0, key="ui_poop_disch")

# Restows
st.subheader("Restows")
r1, r2, r3, r4 = st.columns(4)
with r1:
    fwd_restow_load = st.number_input("FWD Restow Load", min_value=0, value=0, key="ui_fr_load")
    fwd_restow_disch = st.number_input("FWD Restow Discharge", min_value=0, value=0, key="ui_fr_disch")
with r2:
    mid_restow_load = st.number_input("MID Restow Load", min_value=0, value=0, key="ui_mr_load")
    mid_restow_disch = st.number_input("MID Restow Discharge", min_value=0, value=0, key="ui_mr_disch")
with r3:
    aft_restow_load = st.number_input("AFT Restow Load", min_value=0, value=0, key="ui_ar_load")
    aft_restow_disch = st.number_input("AFT Restow Discharge", min_value=0, value=0, key="ui_ar_disch")
with r4:
    poop_restow_load = st.number_input("POOP Restow Load", min_value=0, value=0, key="ui_pr_load")
    poop_restow_disch = st.number_input("POOP Restow Discharge", min_value=0, value=0, key="ui_pr_disch")

# Hatch moves
st.subheader("Hatch Moves")
h1, h2, h3 = st.columns(3)
with h1:
    hatch_fwd_open = st.number_input("FWD Hatch Open", min_value=0, value=0, key="ui_hf_open")
    hatch_fwd_close = st.number_input("FWD Hatch Close", min_value=0, value=0, key="ui_hf_close")
with h2:
    hatch_mid_open = st.number_input("MID Hatch Open", min_value=0, value=0, key="ui_hm_open")
    hatch_mid_close = st.number_input("MID Hatch Close", min_value=0, value=0, key="ui_hm_close")
with h3:
    hatch_aft_open = st.number_input("AFT Hatch Open", min_value=0, value=0, key="ui_ha_open")
    hatch_aft_close = st.number_input("AFT Hatch Close", min_value=0, value=0, key="ui_ha_close")

# WhatsApp send options
st.header("Send to WhatsApp")
whatsapp_number = st.text_input("Enter WhatsApp number with country code (e.g., 27761234567)")
force_mono = st.checkbox("Force monospace in WhatsApp (recommended for perfect columns)", value=True)

# ---------- Submit ----------
if st.button("Submit Hourly Moves"):

    # Update S (session_state) cumulative
    done_load_this = fwd_load + mid_load + aft_load + poop_load
    done_disch_this = fwd_disch + mid_disch + aft_disch + poop_disch
    done_restow_load_this = fwd_restow_load + mid_restow_load + aft_restow_load + poop_restow_load
    done_restow_disch_this = fwd_restow_disch + mid_restow_disch + aft_restow_disch + poop_restow_disch
    done_hatch_open_this = hatch_fwd_open + hatch_mid_open + hatch_aft_open
    done_hatch_close_this = hatch_fwd_close + hatch_mid_close + hatch_aft_close

    S["done_load"] += int(done_load_this)
    S["done_disch"] += int(done_disch_this)
    S["done_restow_load"] += int(done_restow_load_this)
    S["done_restow_disch"] += int(done_restow_disch_this)
    S["done_hatch_open"] += int(done_hatch_open_this)
    S["done_hatch_close"] += int(done_hatch_close_this)
    S["last_hour"] = hourly_time

    # Save persistent editable fields
    S["vessel_name"] = vessel_name
    S["berthed_date"] = berthed_date_input.isoformat()
    S["berthed_time"] = f"{berthed_time_input.hour:02d}:{berthed_time_input.minute:02d}"
    S["first_lift_time"] = f"{first_lift_time_input.hour:02d}:{first_lift_time_input.minute:02d}"
    S["last_lift_time"] = f"{last_lift_time_input.hour:02d}:{last_lift_time_input.minute:02d}"

    S["planned_load"] = int(planned_load)
    S["planned_disch"] = int(planned_disch)
    S["planned_restow_load"] = int(planned_restow_load)
    S["planned_restow_disch"] = int(planned_restow_disch)

    S["opening_load"] = int(opening_load)
    S["opening_disch"] = int(opening_disch)
    S["opening_restow_load"] = int(opening_restow_load)
    S["opening_restow_disch"] = int(opening_restow_disch)

    save_persistent({k: S[k] for k in S.keys()})  # save all session_state keys

    # Remaining calculations (opening balances are deductions)
    remaining_load = S["planned_load"] - S["done_load"] - S["opening_load"]
    remaining_disch = S["planned_disch"] - S["done_disch"] - S["opening_disch"]
    remaining_restow_load = S["planned_restow_load"] - S["done_restow_load"] - S["opening_restow_load"]
    remaining_restow_disch = S["planned_restow_disch"] - S["done_restow_disch"] - S["opening_restow_disch"]

    # Formatted strings
    berthed_str = f"{berthed_date_input.strftime('%d/%m/%Y')} @ {fmt_h_MM_upper(berthed_time_input)}"
    first_lift_str = fmt_h_mm_lower(first_lift_time_input)
    last_lift_str = fmt_h_mm_lower(last_lift_time_input)
    today_line = today_sa_str()

    # Column widths for alignment
    lbl_w, c1_w, c2_w = 8, 11, 12
    cum_lbl_w, cum_c1_w, cum_c2_w = 12, 12, 10

    # Lines / headers
    big_line = "_" * 25
    # Build sections using fmt_cols to keep columns aligned
    header_crane = fmt_cols(lbl_w, c1_w, c2_w, "", "Load", "Discharge")
    crane_rows = "\n".join([
        fmt_cols(lbl_w, c1_w, c2_w, "FWD", fwd_load, fwd_disch),
        fmt_cols(lbl_w, c1_w, c2_w, "MID", mid_load, mid_disch),
        fmt_cols(lbl_w, c1_w, c2_w, "AFT", aft_load, aft_disch),
        fmt_cols(lbl_w, c1_w, c2_w, "POOP", poop_load, poop_disch),
    ])

    header_rest = fmt_cols(lbl_w, c1_w, c2_w, "", "Load", "Discharge")
    restow_rows = "\n".join([
        fmt_cols(lbl_w, c1_w, c2_w, "FWD", fwd_restow_load, fwd_restow_disch),
        fmt_cols(lbl_w, c1_w, c2_w, "MID", mid_restow_load, mid_restow_disch),
        fmt_cols(lbl_w, c1_w, c2_w, "AFT", aft_restow_load, aft_restow_disch),
        fmt_cols(lbl_w, c1_w, c2_w, "POOP", poop_restow_load, poop_restow_disch),
    ])

    header_cum = fmt_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "", "Load", "Disch")
    cum_rows = "\n".join([
        fmt_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Plan.", S["planned_load"], S["planned_disch"]),
        fmt_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Done", S["done_load"], S["done_disch"]),
        fmt_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Remain", remaining_load, remaining_disch),
    ])

    header_rest_cum = fmt_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "", "Load", "Disch")
    restow_cum_rows = "\n".join([
        fmt_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Plan", S["planned_restow_load"], S["planned_restow_disch"]),
        fmt_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Done", S["done_restow_load"], S["done_restow_disch"]),
        fmt_cols(cum_lbl_w, cum_c1_w, cum_c2_w, "Remain", remaining_restow_load, remaining_restow_disch),
    ])

    header_hatch = fmt_cols(lbl_w, c1_w, c2_w, "", "Open", "Close")
    hatch_rows = "\n".join([
        fmt_cols(lbl_w, c1_w, c2_w, "FWD", hatch_fwd_open, hatch_fwd_close),
        fmt_cols(lbl_w, c1_w, c2_w, "MID", hatch_mid_open, hatch_mid_close),
        fmt_cols(lbl_w, c1_w, c2_w, "AFT", hatch_aft_open, hatch_aft_close),
    ])

    # Build the final template exactly matching your structure, with double underscore around CUMULATIVE
    template = (
f"""{vessel_name}
Berthed {berthed_str}

First Lift @ {first_lift_str}
Last Lift @ {last_lift_str}

{today_line}
{hourly_time}
{big_line}
   *HOURLY MOVES*
{big_line}
*Crane Moves*
{header_crane}
{crane_rows}
{big_line}
*Restows*
{header_rest}
{restow_rows}
{big_line}
      *CUMULATIVE*
{big_line}
{header_cum}
{cum_rows}
{big_line}
*Restows*
{header_rest_cum}
{restow_cum_rows}
{big_line}
*Hatch Moves*
{header_hatch}
{hatch_rows}
{big_line}
*Gear boxes*

{big_line}
*Idle*"""
    )

    # Show template in monospace in the app for perfect preview
    st.code(template, language=None)

    # Prepare WhatsApp message: wrap with triple backticks if force_mono True
    wa_msg = f"```{template}```" if force_mono else template

    if whatsapp_number:
        wa_link = f"https://wa.me/{whatsapp_number}?text={urllib.parse.quote(wa_msg)}"
        st.markdown(f"[Open WhatsApp with this template](<{wa_link}>)", unsafe_allow_html=True)

    st.success("Saved. Template preview is shown above. Use the WhatsApp link or copy the template.")