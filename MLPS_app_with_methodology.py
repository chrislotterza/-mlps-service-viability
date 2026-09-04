
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="MLPS Service Viability",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.block-container {padding-top:1.1rem; max-width:1500px;}
div[data-testid="stMetric"] {
    border:1px solid rgba(120,120,120,.22);
    border-radius:14px;
    padding:14px 16px;
    background:rgba(120,120,120,.05);
}
.hero {
    padding:18px 22px;
    border-radius:16px;
    margin-bottom:12px;
    background:linear-gradient(135deg, rgba(32,105,74,.14), rgba(35,94,140,.08));
    border:1px solid rgba(100,100,100,.18);
}
.good {padding:13px 16px;border-radius:12px;background:rgba(25,150,80,.12);border:1px solid rgba(25,150,80,.30);font-weight:700;}
.warn {padding:13px 16px;border-radius:12px;background:rgba(230,165,30,.13);border:1px solid rgba(230,165,30,.32);font-weight:700;}
.bad {padding:13px 16px;border-radius:12px;background:rgba(210,60,60,.12);border:1px solid rgba(210,60,60,.30);font-weight:700;}
.small {opacity:.72;font-size:.88rem;}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# WORKING SERVICE DEFAULTS
# - Economy coach: 66 seats
# - Sleeper coach: 24 berths
# - Baseline operation: 1 departure/month, 1 month/year
# - Johannesburg–Durban distance: 730 km
# - Electric share is editable; diesel = 100% - electric share
# -------------------------------------------------------------------
SERVICES = {
    "Trans-Karoo": dict(
        distance=1530, departures=1, months=1, electric_share=100,
        locos=1, economy_coaches=8, sleeper_coaches=4, other_coaches=2,
        economy_seats=66, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=88.9,
        economy_fare=450, sleeper_fare=750, ancillary=35,
        economy_occ=65, sleeper_occ=60,
        access_fee=65, electric_rate=0.0627,
        diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=12, coach_maint=8, crew=12000, shunting=7500,
        onboard=45, ticketing=2.5, contingency=5.0,
        loco_lease=750000, route_fixed=750000
    ),
    "Amatola": dict(
        distance=1036, departures=1, months=1, electric_share=100,
        locos=1, economy_coaches=8, sleeper_coaches=4, other_coaches=2,
        economy_seats=66, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=88.9,
        economy_fare=330, sleeper_fare=500, ancillary=35,
        economy_occ=65, sleeper_occ=60,
        access_fee=65, electric_rate=0.0627,
        diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=12, coach_maint=8, crew=12000, shunting=7500,
        onboard=45, ticketing=2.5, contingency=5.0,
        loco_lease=750000, route_fixed=450000
    ),
    "Johannesburg–Durban": dict(
        distance=730, departures=1, months=1, electric_share=100,
        locos=1, economy_coaches=8, sleeper_coaches=4, other_coaches=2,
        economy_seats=66, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=88.9,
        economy_fare=280, sleeper_fare=450, ancillary=35,
        economy_occ=70, sleeper_occ=60,
        access_fee=65, electric_rate=0.0627,
        diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=12, coach_maint=8, crew=12000, shunting=7500,
        onboard=45, ticketing=2.5, contingency=5.0,
        loco_lease=750000, route_fixed=450000
    ),
    "Bosvelder": dict(
        distance=732, departures=1, months=1, electric_share=100,
        locos=1, economy_coaches=6, sleeper_coaches=3, other_coaches=2,
        economy_seats=66, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=88.9,
        economy_fare=260, sleeper_fare=420, ancillary=35,
        economy_occ=60, sleeper_occ=55,
        access_fee=50, electric_rate=0.0627,
        diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=12, coach_maint=8, crew=12000, shunting=7500,
        onboard=45, ticketing=2.5, contingency=5.0,
        loco_lease=750000, route_fixed=350000
    ),
    "Custom": dict(
        distance=500, departures=1, months=1, electric_share=50,
        locos=1, economy_coaches=6, sleeper_coaches=2, other_coaches=1,
        economy_seats=66, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=90,
        economy_fare=250, sleeper_fare=400, ancillary=25,
        economy_occ=60, sleeper_occ=55,
        access_fee=50, electric_rate=0.0627,
        diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=18, coach_maint=8, crew=12000, shunting=7500,
        onboard=45, ticketing=2.5, contingency=5.0,
        loco_lease=750000, route_fixed=250000
    ),
}

# -------------------------------------------------------------------
# ECONOMIC IMPACT DEFAULTS
# These are editable planning assumptions, not certified emissions factors.
# Road-mode emissions are calculated from fuel use; rail emissions use the
# selected traction mix. Wider economic activity is kept separate from
# incremental passenger/carbon benefits to avoid double counting.
# -------------------------------------------------------------------
ECON_DEFAULTS = {
    "alternative_mode": "Intercity coach",
    "alt_fare_coach": 650.0,
    "alt_transfer_coach": 50.0,
    "alt_fare_minibus": 800.0,
    "alt_transfer_minibus": 40.0,
    "alt_fare_car": 900.0,
    "alt_transfer_car": 0.0,
    "alt_fare_air": 1400.0,
    "alt_transfer_air": 250.0,
    "alt_fare_custom": 650.0,
    "alt_transfer_custom": 0.0,

    # Emissions / vehicle assumptions
    "diesel_co2_per_litre": 2.68,
    "grid_co2_per_kwh": 1.05,
    "electric_kwh_per_train_km": 22.0,
    "coach_capacity": 60,
    "coach_occ": 70,
    "coach_l100km": 30.0,
    "minibus_capacity": 14,
    "minibus_occ": 80,
    "minibus_l100km": 10.0,
    "car_capacity": 5,
    "car_occ": 40,
    "car_l100km": 7.5,
    "air_co2_per_pax_km": 0.126,
    "custom_co2_per_pax_km": 0.08,
    "carbon_value": 308.0,

    # Wider economic activity assumptions
    "associated_spend_per_pax": 500.0,
    "economic_multiplier": 1.30,
}

def money(x): return f"R {x:,.0f}"
def pct(x): return f"{x*100:.1f}%"
def n0(x): return f"{x:,.0f}"

def calculate(d):
    econ_occ = d["economy_occ"] / 100
    sleep_occ = d["sleeper_occ"] / 100
    ticketing = d["ticketing"] / 100
    contingency = d["contingency"] / 100
    electric_share = d["electric_share"] / 100
    diesel_share = 1 - electric_share

    total_coaches = d["economy_coaches"] + d["sleeper_coaches"] + d["other_coaches"]
    sellable_capacity = (
        d["economy_coaches"] * d["economy_seats"]
        + d["sleeper_coaches"] * d["sleeper_berths"]
    )
    economy_pax = d["economy_coaches"] * d["economy_seats"] * econ_occ
    sleeper_pax = d["sleeper_coaches"] * d["sleeper_berths"] * sleep_occ
    passengers = economy_pax + sleeper_pax

    train_tare_mass = (
        d["locos"] * d["loco_mass"]
        + d["economy_coaches"] * d["economy_mass"]
        + d["sleeper_coaches"] * d["sleeper_mass"]
        + d["other_coaches"] * d["other_mass"]
    )

    electric_km = d["distance"] * electric_share
    diesel_km = d["distance"] * diesel_share
    electric_gtk = train_tare_mass * electric_km

    passenger_revenue = (
        economy_pax * d["economy_fare"]
        + sleeper_pax * d["sleeper_fare"]
    )
    ancillary_revenue = passengers * d["ancillary"]
    revenue = passenger_revenue + ancillary_revenue

    access_cost = d["distance"] * d["access_fee"]
    electric_cost = electric_gtk * d["electric_rate"]
    diesel_cost = (
        diesel_km
        * d["locos"]
        * d["diesel_consumption"]
        * d["diesel_price"]
    )
    traction_cost = electric_cost + diesel_cost

    loco_maintenance = d["distance"] * d["locos"] * d["loco_maint"]
    coach_maintenance = d["distance"] * total_coaches * d["coach_maint"]
    crew = d["crew"]
    shunting = d["shunting"]
    onboard = passengers * d["onboard"]
    ticketing_cost = revenue * ticketing

    base_var = (
        access_cost + traction_cost + loco_maintenance + coach_maintenance
        + crew + shunting + onboard + ticketing_cost
    )
    contingency_cost = base_var * contingency
    variable_cost = base_var + contingency_cost

    contribution = revenue - variable_cost
    recovery = revenue / variable_cost if variable_cost else 0
    revenue_per_pax = revenue / passengers if passengers else 0
    variable_cost_per_pax = variable_cost / passengers if passengers else 0

    fixed_train_running = (
        access_cost + traction_cost + loco_maintenance
        + coach_maintenance + crew + shunting
    )
    denominator = (
        (revenue_per_pax - d["onboard"] - revenue_per_pax * ticketing)
        * (1 - contingency)
    )
    break_even_pax = (
        max(0, fixed_train_running * (1 + contingency) / denominator)
        if denominator > 0 else 0
    )
    break_even_occ = break_even_pax / sellable_capacity if sellable_capacity else 0

    revenue_gap = max(0, -contribution)
    required_uplift = max(0, variable_cost / revenue - 1) if revenue else 0

    fixed_cost_departure = (
        ((d["loco_lease"] * d["locos"]) + d["route_fixed"]) / d["departures"]
        if d["departures"] else 0
    )
    full_cost_departure = variable_cost + fixed_cost_departure
    full_cost_recovery = revenue / full_cost_departure if full_cost_departure else 0

    monthly_contribution = contribution * d["departures"]
    annual_contribution = monthly_contribution * d["months"]

    current_occ = passengers / sellable_capacity if sellable_capacity else 0

    # ---------------------------------------------------------------
    # ECONOMIC IMPACT
    # ---------------------------------------------------------------
    avg_ticket_fare = passenger_revenue / passengers if passengers else 0
    alt_mode = d.get("alternative_mode", "Intercity coach")

    alt_cost_map = {
        "Intercity coach": (d.get("alt_fare_coach", 0), d.get("alt_transfer_coach", 0)),
        "Minibus taxi": (d.get("alt_fare_minibus", 0), d.get("alt_transfer_minibus", 0)),
        "Private car": (d.get("alt_fare_car", 0), d.get("alt_transfer_car", 0)),
        "Air": (d.get("alt_fare_air", 0), d.get("alt_transfer_air", 0)),
        "Custom": (d.get("alt_fare_custom", 0), d.get("alt_transfer_custom", 0)),
    }
    alt_base_cost, alt_transfer_cost = alt_cost_map.get(alt_mode, (0, 0))
    alternative_cost_per_pax = alt_base_cost + alt_transfer_cost
    passenger_saving_per_pax = alternative_cost_per_pax - avg_ticket_fare
    passenger_financial_benefit = passenger_saving_per_pax * passengers

    diesel_litres = diesel_km * d["locos"] * d["diesel_consumption"]
    train_diesel_co2_kg = diesel_litres * d.get("diesel_co2_per_litre", 2.68)
    train_electric_kwh = electric_km * d.get("electric_kwh_per_train_km", 22.0)
    train_electric_co2_kg = train_electric_kwh * d.get("grid_co2_per_kwh", 1.05)
    train_co2_kg = train_diesel_co2_kg + train_electric_co2_kg
    train_co2_per_pax_km = train_co2_kg / (passengers * d["distance"]) if passengers and d["distance"] else 0

    if alt_mode == "Intercity coach":
        effective_capacity = d.get("coach_capacity", 60) * d.get("coach_occ", 70) / 100
        alt_vehicles = passengers / effective_capacity if effective_capacity else 0
        alt_fuel_litres = alt_vehicles * d["distance"] * d.get("coach_l100km", 30.0) / 100
        alternative_co2_kg = alt_fuel_litres * d.get("diesel_co2_per_litre", 2.68)
    elif alt_mode == "Minibus taxi":
        effective_capacity = d.get("minibus_capacity", 15) * d.get("minibus_occ", 80) / 100
        alt_vehicles = passengers / effective_capacity if effective_capacity else 0
        alt_fuel_litres = alt_vehicles * d["distance"] * d.get("minibus_l100km", 12.0) / 100
        alternative_co2_kg = alt_fuel_litres * d.get("diesel_co2_per_litre", 2.68)
    elif alt_mode == "Private car":
        effective_capacity = d.get("car_capacity", 5) * d.get("car_occ", 40) / 100
        alt_vehicles = passengers / effective_capacity if effective_capacity else 0
        alt_fuel_litres = alt_vehicles * d["distance"] * d.get("car_l100km", 8.0) / 100
        alternative_co2_kg = alt_fuel_litres * d.get("diesel_co2_per_litre", 2.68)
    elif alt_mode == "Air":
        alt_vehicles = 0
        alt_fuel_litres = 0
        alternative_co2_kg = passengers * d["distance"] * d.get("air_co2_per_pax_km", 0.15)
    else:
        alt_vehicles = 0
        alt_fuel_litres = 0
        alternative_co2_kg = passengers * d["distance"] * d.get("custom_co2_per_pax_km", 0.08)

    alternative_co2_per_pax_km = alternative_co2_kg / (passengers * d["distance"]) if passengers and d["distance"] else 0
    co2_saving_kg = alternative_co2_kg - train_co2_kg
    co2_saving_tonnes = co2_saving_kg / 1000
    emissions_reduction = co2_saving_kg / alternative_co2_kg if alternative_co2_kg else 0
    carbon_benefit = co2_saving_tonnes * d.get("carbon_value", 0)

    measurable_incremental_benefit = passenger_financial_benefit + carbon_benefit
    operating_support = max(0, -contribution)
    economic_benefit_per_support = (
        measurable_incremental_benefit / operating_support if operating_support > 0 else None
    )

    direct_economic_activity = passengers * d.get("associated_spend_per_pax", 0)
    total_economic_activity = direct_economic_activity * d.get("economic_multiplier", 1.0)
    multiplier_effect = total_economic_activity - direct_economic_activity
    activity_per_support = total_economic_activity / operating_support if operating_support > 0 else None

    return locals()

def load_defaults(service):
    for k, v in SERVICES[service].items():
        st.session_state[k] = v
    for k, v in ECON_DEFAULTS.items():
        st.session_state[k] = v
    st.session_state["_loaded_service"] = service

def current_inputs(service):
    values = {k: st.session_state[k] for k in SERVICES[service].keys()}
    values.update({k: st.session_state[k] for k in ECON_DEFAULTS.keys()})
    return values

def sensitivity_table(base):
    base_r = calculate(base)

    tests = [
        ("Economy occupancy +10 pts", "economy_occ", min(100, base["economy_occ"] + 10)),
        ("Sleeper occupancy +10 pts", "sleeper_occ", min(100, base["sleeper_occ"] + 10)),
        ("Economy fare +10%", "economy_fare", base["economy_fare"] * 1.10),
        ("Sleeper fare +10%", "sleeper_fare", base["sleeper_fare"] * 1.10),
        ("Access fee -10%", "access_fee", base["access_fee"] * 0.90),
        ("Diesel price -10%", "diesel_price", base["diesel_price"] * 0.90),
        ("Electric traction rate -10%", "electric_rate", base["electric_rate"] * 0.90),
        ("On-board variable cost -10%", "onboard", base["onboard"] * 0.90),
        ("Coach maintenance -10%", "coach_maint", base["coach_maint"] * 0.90),
        ("Crew cost -10%", "crew", base["crew"] * 0.90),
    ]

    rows = []
    for label, key, value in tests:
        case = base.copy()
        case[key] = value
        rr = calculate(case)
        rows.append({
            "Lever": label,
            "Recovery": rr["recovery"],
            "Δ recovery": rr["recovery"] - base_r["recovery"],
            "Contribution": rr["contribution"],
            "Δ contribution": rr["contribution"] - base_r["contribution"],
            "Break-even occupancy": rr["break_even_occ"],
        })

    return pd.DataFrame(rows).sort_values("Δ contribution", ascending=False)

def recovery_gauge(recovery):
    value = min(max(recovery * 100, 0), 160)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix":"%"},
        title={"text":"Variable Cost Recovery"},
        gauge={
            "axis":{"range":[0,160]},
            "bar":{"thickness":0.35},
            "steps":[
                {"range":[0,90]},
                {"range":[90,100]},
                {"range":[100,160]}
            ],
            "threshold":{
                "line":{"width":4},
                "thickness":0.8,
                "value":100
            }
        }
    ))
    fig.update_layout(height=280, margin=dict(l=25,r=25,t=50,b=20))
    return fig

st.markdown("""
<div class="hero" style="display:flex;align-items:center;gap:22px;">
    <div style="flex:0 0 auto;">
        <img src="https://rmkcdn.successfactors.com/3adc3a8a/55933741-7481-45cd-b29e-0.png"
             alt="PRASA logo"
             style="height:68px;max-width:220px;object-fit:contain;">
    </div>
    <div>
        <h2 style="margin:0">MLPS Service Viability Model</h2>
        <div class="small">Standalone Python decision-support model</div>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Scenario")
    service = st.selectbox("Service", list(SERVICES), index=2)

    if st.session_state.get("_loaded_service") != service:
        load_defaults(service)
        st.rerun()

    if st.button("↺ Reset service defaults", use_container_width=True):
        load_defaults(service)
        st.rerun()

    st.divider()
    st.caption("Baseline: 1 departure/month and 1 month/year.")
    st.caption("Economy coach: 66 seats.")
    st.caption("Sleeper coach: 24 berths.")
    st.caption("Electric + diesel shares always sum to 100%.")

t1, t2, t3, t4, t5, t6 = st.tabs([
    "🚆 Service & Train",
    "🎟 Fares & Demand",
    "⚡ Traction & Access",
    "🧾 Costs",
    "🌍 Economic Impact",
    "📘 How the Model Works"
])

with t1:
    a, b, c = st.columns(3)
    with a:
        st.number_input("One-way distance (km)", min_value=1.0, step=10.0, key="distance")
        st.number_input("One-way departures / month", min_value=1, step=1, key="departures")
        st.number_input("Months operated / year", min_value=1, max_value=12, step=1, key="months")
    with b:
        st.number_input("Locomotives", min_value=1, step=1, key="locos")
        st.number_input("Economy coaches", min_value=0, step=1, key="economy_coaches")
        st.number_input("Sleeper coaches", min_value=0, step=1, key="sleeper_coaches")
        st.number_input("Other coaches / vans", min_value=0, step=1, key="other_coaches")
    with c:
        st.number_input("Economy seats / coach", min_value=1, step=1, key="economy_seats")
        st.number_input("Sleeper berths / coach", min_value=1, step=1, key="sleeper_berths")
        st.number_input("Economy coach mass (t)", min_value=0.0, step=1.0, key="economy_mass")
        st.number_input("Sleeper coach mass (t)", min_value=0.0, step=1.0, key="sleeper_mass")
        st.number_input("Other coach mass (t)", min_value=0.0, step=1.0, key="other_mass")
        st.number_input("Locomotive mass (t)", min_value=0.0, step=1.0, key="loco_mass")

with t2:
    st.markdown("#### Occupancy")
    a, b = st.columns(2)
    with a:
        st.slider("Economy occupancy (%)", 0, 100, step=1, key="economy_occ")
    with b:
        st.slider("Sleeper occupancy (%)", 0, 100, step=1, key="sleeper_occ")

    st.markdown("#### Fares & ancillary revenue")
    a, b, c = st.columns(3)
    with a:
        st.number_input("Economy realised fare (R)", min_value=0.0, step=10.0, key="economy_fare")
    with b:
        st.number_input("Sleeper realised fare (R)", min_value=0.0, step=10.0, key="sleeper_fare")
    with c:
        st.number_input("Ancillary net revenue / passenger (R)", min_value=0.0, step=5.0, key="ancillary")

with t3:
    st.markdown("#### Traction share")
    st.slider(
        "Electric share of route (%)",
        0, 100, step=1, key="electric_share"
    )
    electric_share = st.session_state["electric_share"]
    diesel_share = 100 - electric_share

    a, b = st.columns(2)
    a.metric("Electric share", f"{electric_share:.0f}%")
    b.metric("Diesel share", f"{diesel_share:.0f}%")

    st.caption(
        "The route distance is split between electric and diesel operation. "
        "Electric traction cost is applied to the electric section and diesel fuel cost to the balance."
    )

    a, b = st.columns(2)
    with a:
        st.number_input("TRIM access fee (R/train-km)", min_value=0.0, step=1.0, key="access_fee")
        st.number_input("Electric traction rate (R/GTK)", min_value=0.0, step=0.001, format="%.4f", key="electric_rate")
    with b:
        st.number_input("Diesel price (R/litre)", min_value=0.0, step=0.10, key="diesel_price")
        st.number_input("Diesel consumption (L/loco-km)", min_value=0.0, step=0.1, key="diesel_consumption")

with t4:
    a, b, c = st.columns(3)
    with a:
        st.number_input("Loco variable maintenance (R/loco-km)", min_value=0.0, step=1.0, key="loco_maint")
        st.number_input("Coach variable maintenance (R/coach-km)", min_value=0.0, step=1.0, key="coach_maint")
        st.number_input("Train crew (R/departure)", min_value=0.0, step=500.0, key="crew")
    with b:
        st.number_input("Shunting / terminal (R/departure)", min_value=0.0, step=500.0, key="shunting")
        st.number_input("On-board variable cost (R/passenger)", min_value=0.0, step=5.0, key="onboard")
        st.slider("Ticketing / collection (% revenue)", 0.0, 20.0, step=0.5, key="ticketing")
    with c:
        st.slider("Operational contingency (%)", 0.0, 30.0, step=1.0, key="contingency")
        st.number_input("Locomotive lease / hire (R/month)", min_value=0.0, step=50000.0, key="loco_lease")
        st.number_input("Route / station fixed cost (R/month)", min_value=0.0, step=50000.0, key="route_fixed")

with t5:
    st.markdown("#### Alternative transport comparison")
    st.caption(
        "Compare the same passenger movement with an alternative mode. Financial saving and emissions are "
        "incremental comparisons; wider economic activity is shown separately to avoid double counting."
    )
    st.selectbox(
        "Alternative mode",
        ["Intercity coach", "Minibus taxi", "Private car", "Air", "Custom"],
        key="alternative_mode"
    )

    mode = st.session_state["alternative_mode"]
    a, b = st.columns(2)
    if mode == "Intercity coach":
        with a:
            st.number_input("Coach fare / passenger (R)", min_value=0.0, step=25.0, key="alt_fare_coach")
            st.number_input("Coach capacity", min_value=1, step=1, key="coach_capacity")
            st.slider("Coach occupancy (%)", 1, 100, step=1, key="coach_occ")
        with b:
            st.number_input("Transfers / other passenger cost (R)", min_value=0.0, step=10.0, key="alt_transfer_coach")
            st.number_input("Coach fuel use (L/100 km)", min_value=0.0, step=1.0, key="coach_l100km")
    elif mode == "Minibus taxi":
        with a:
            st.number_input("Minibus fare / passenger (R)", min_value=0.0, step=25.0, key="alt_fare_minibus")
            st.number_input("Minibus capacity", min_value=1, step=1, key="minibus_capacity")
            st.slider("Minibus occupancy (%)", 1, 100, step=1, key="minibus_occ")
        with b:
            st.number_input("Transfers / other passenger cost (R)", min_value=0.0, step=10.0, key="alt_transfer_minibus")
            st.number_input("Minibus fuel use (L/100 km)", min_value=0.0, step=0.5, key="minibus_l100km")
    elif mode == "Private car":
        with a:
            st.number_input("Car journey cost / passenger (R)", min_value=0.0, step=25.0, key="alt_fare_car")
            st.number_input("Car seats / capacity", min_value=1, step=1, key="car_capacity")
            st.slider("Average seat occupancy (%)", 1, 100, step=1, key="car_occ")
        with b:
            st.number_input("Transfers / other passenger cost (R)", min_value=0.0, step=10.0, key="alt_transfer_car")
            st.number_input("Car fuel use (L/100 km)", min_value=0.0, step=0.5, key="car_l100km")
    elif mode == "Air":
        with a:
            st.number_input("Air fare / passenger (R)", min_value=0.0, step=50.0, key="alt_fare_air")
        with b:
            st.number_input("Airport transfers / other cost (R)", min_value=0.0, step=25.0, key="alt_transfer_air")
            st.number_input("Air emissions (kg CO₂e/passenger-km)", min_value=0.0, step=0.01, format="%.3f", key="air_co2_per_pax_km")
    else:
        with a:
            st.number_input("Alternative cost / passenger (R)", min_value=0.0, step=25.0, key="alt_fare_custom")
            st.number_input("Other passenger cost (R)", min_value=0.0, step=10.0, key="alt_transfer_custom")
        with b:
            st.number_input("Alternative emissions (kg CO₂e/passenger-km)", min_value=0.0, step=0.01, format="%.3f", key="custom_co2_per_pax_km")

    st.markdown("#### Rail emissions baseline")
    a, b, c = st.columns(3)
    with a:
        st.number_input("Diesel CO₂e (kg/litre)", min_value=0.0, step=0.01, format="%.2f", key="diesel_co2_per_litre")
    with b:
        st.number_input("Electric train energy (kWh/train-km)", min_value=0.0, step=1.0, key="electric_kwh_per_train_km")
    with c:
        st.number_input("Grid CO₂e (kg/kWh)", min_value=0.0, step=0.01, format="%.2f", key="grid_co2_per_kwh")
    st.caption(
        "Diesel locomotive emissions use the existing loco fuel-consumption input. Electric emissions use "
        "kWh/train-km × the grid factor. All factors are editable planning assumptions."
    )

    st.markdown("#### Carbon value & wider economic activity")
    a, b, c = st.columns(3)
    with a:
        st.number_input("Carbon value (R/tonne CO₂e)", min_value=0.0, step=100.0, key="carbon_value")
    with b:
        st.number_input("Associated spend / passenger (R)", min_value=0.0, step=50.0, key="associated_spend_per_pax")
    with c:
        st.number_input("Economic activity multiplier", min_value=1.0, max_value=5.0, step=0.05, format="%.2f", key="economic_multiplier")
    st.caption(
        "Associated passenger spend × multiplier estimates economic activity supported. It is not added to "
        "passenger savings or carbon benefit because that could overstate economic welfare benefits."
    )

    with st.expander("Baseline assumptions & evidence notes"):
        st.markdown("""
**Recommended baseline interpretation**

- **Diesel:** 2.68 kg CO₂/litre — standard combustion-factor approximation.
- **Electricity:** 1.05 kg CO₂/kWh — conservative South African baseline derived from Eskom's reported emissions and power sent out.
- **Electric train energy:** 22 kWh/train-km — engineering planning assumption for a locomotive-hauled intercity train; replace with metered traction-energy data when available.
- **Intercity coach:** 60 seats, 70% occupancy, 30 L/100 km — planning baseline; sensitivity-test occupancy and fuel use.
- **Minibus taxi:** 14 seats, 80% occupancy, 10 L/100 km — representative Quantum-class diesel planning assumption; actual fleet performance will vary.
- **Private car:** 5 seats, 40% seat occupancy (2 persons), 7.5 L/100 km — representative long-distance planning assumption.
- **Air:** 0.126 kg CO₂e/passenger-km — indicative short-haul economy proxy.
- **Carbon value:** R308/tCO₂e — 2026 headline South African carbon-tax rate. This is a policy price, not a full social cost of carbon.
- **Associated spend:** R500/passenger and **multiplier 1.30** — deliberately conservative placeholders. They should not be described as incremental welfare benefits and should be replaced with route-specific evidence and a South African SAM/input-output multiplier for formal appraisal.

The model is intentionally conservative: it can show **negative emissions savings** where a low-occupancy train performs worse than the selected alternative.
        """)

with t6:
    st.markdown("# How the MLPS Service Viability Model Works")
    st.markdown(
        """
This model is a **scenario-based decision-support tool** for testing whether an MLPS passenger service can cover its
**avoidable / variable operating costs**, how far it is from break-even when it cannot, and what wider passenger,
environmental and economic effects may be associated with operating the service.

It is deliberately designed as an **interactive operating model**, rather than a fixed forecast. Each service begins with
a set of working assumptions, but the user can change train composition, fares, occupancy, traction, access charges,
fuel prices, maintenance costs, operating frequency and economic-impact assumptions and immediately see how the result changes.

The model keeps three questions separate:

1. **Financial viability:** does the service recover its variable operating cost?
2. **Incremental economic and environmental benefit:** are passengers financially better off and are emissions lower than a selected alternative mode?
3. **Wider economic activity supported:** how much direct and multiplier-related activity may be associated with passengers making the trip?

The third measure is **not added** to the first two economic-benefit measures. This is intentional and avoids presenting
wider economic activity as if it were automatically an incremental welfare benefit.
        """
    )

    st.markdown("## 1. Scenario selection and operating period")
    st.markdown(
        """
The sidebar selects the service to be analysed. Each named service has its own default route, consist, fares, occupancy,
traction and cost assumptions. Selecting **Custom** allows the same calculation structure to be used for another corridor.

The model is calculated first on a **one-way departure basis**. Monthly and annual results are then derived from the selected
number of one-way departures per month and the number of months operated per year. The current starting convention is
**1 one-way departure per month and 1 operating month per year**, so frequency can be scaled explicitly rather than being
hidden in the model.

A departure is therefore one train movement over the entered one-way route distance. If the user wants to represent a
return service, both directions must be reflected in the number of departures.
        """
    )

    st.markdown("## 2. Train composition and sellable capacity")
    st.markdown(
        """
The train is built from four physical inputs:

- number of locomotives;
- number of economy coaches;
- number of sleeper coaches; and
- other coaches / vans that add mass and operating cost but do not create sellable passenger capacity in the current model.

The default capacity conventions are **66 seats per economy coach** and **24 berths per sleeper coach**. These remain editable.

**Sellable capacity** is calculated as:

`Economy coaches × economy seats per coach + sleeper coaches × sleeper berths per coach`

Other coaches are excluded from sellable capacity because they are treated as non-revenue vehicles. They still contribute
to total train mass and coach maintenance cost.

The entered coach and locomotive masses are used to estimate the tare mass of the consist. This mass is important for the
electric-traction calculation, which is expressed using gross-tonne-kilometres on the electrified section of the route.
        """
    )

    st.markdown("## 3. Passenger demand and occupancy")
    st.markdown(
        """
Economy and sleeper demand are modelled separately. For each accommodation type, passengers are estimated as:

`Number of coaches × capacity per coach × occupancy`

Total passengers are the sum of economy and sleeper passengers.

The model therefore treats **occupancy as a core commercial and environmental variable**. Increasing occupancy raises fare
and ancillary revenue without adding another coach or locomotive, while most train-running costs remain unchanged. It also
reduces rail emissions per passenger-kilometre because the same train movement is shared across more passengers.

The dashboard also reports a combined current occupancy:

`Total passengers ÷ total sellable capacity`

This combined measure is useful for the headline dashboard, while the model still retains separate economy and sleeper
occupancies for revenue estimation.
        """
    )

    st.markdown("## 4. Revenue calculation")
    st.markdown(
        """
Passenger revenue is based on the **realised fare**, rather than a published headline fare. This allows the input to represent
the average revenue actually received after discounts, concessions or product mix.

Economy and sleeper revenue are calculated separately:

`Economy passengers × economy realised fare`

plus

`Sleeper passengers × sleeper realised fare`

The model then adds **ancillary net revenue per passenger**. This can represent net on-board retail, catering, baggage or
other passenger-related revenue where appropriate.

Total revenue per departure is therefore:

`Passenger fare revenue + ancillary net revenue`

The dashboard also derives average revenue per passenger for break-even analysis.
        """
    )

    st.markdown("## 5. Access and traction")
    st.markdown(
        """
The route can be split between **electric and diesel traction**. The user enters the electric share as a percentage; the model
automatically treats the balance as diesel, ensuring that electric and diesel shares always sum to 100%.

### Access cost
Access cost is currently modelled as:

`Route distance × TRIM access fee per train-km`

This means the access charge is applied once to each one-way train movement.

### Electric traction cost
For the electric section, the model first calculates electrified kilometres and train gross-tonne-kilometres:

`Train tare mass × electric route km`

Electric traction cost is then:

`Electric GTK × electric traction rate (R/GTK)`

### Diesel traction cost
For the diesel section, fuel consumption is based on locomotive-kilometres:

`Diesel route km × locomotives × litres per loco-km × diesel price per litre`

The model therefore allows a service to be fully electric, fully diesel or any blended traction share. Changing the traction
mix affects both the operating-cost result and the emissions result.
        """
    )

    st.markdown("## 6. Variable operating cost")
    st.markdown(
        """
The main financial test is **variable-cost recovery**. Variable cost represents expenditure that is treated as associated with
running the selected departure. The current cost stack is:

- infrastructure access charge;
- electric traction cost;
- diesel fuel cost;
- locomotive variable maintenance;
- coach variable maintenance;
- train crew per departure;
- shunting / terminal cost per departure;
- on-board variable cost per passenger;
- ticketing / collection cost as a percentage of revenue; and
- an operating contingency applied to the calculated base variable cost.

Locomotive maintenance is calculated using locomotive-kilometres:

`Distance × locomotives × loco maintenance rate`

Coach maintenance is calculated using coach-kilometres:

`Distance × total coaches × coach maintenance rate`

On-board cost changes directly with passengers. Ticketing / collection cost changes with revenue. Crew, shunting, access,
traction and maintenance are primarily train-running costs and therefore do not fall simply because occupancy falls.

The contingency percentage is applied after the above base variable costs have been calculated. It is intended to give the
user an explicit allowance for operating uncertainty rather than embedding an unexplained buffer in individual cost lines.
        """
    )

    st.markdown("## 7. Contribution and variable-cost recovery")
    st.markdown(
        """
The model's central financial result is:

`Contribution per departure = total revenue − variable operating cost`

A positive contribution means the service covers the modelled variable cost of operating the departure. A negative
contribution is shown as the **operating support required** at the variable-cost level.

Variable-cost recovery is:

`Revenue ÷ variable operating cost`

Interpretation:

- **100% or more:** variable break-even is achieved;
- **90%–99.9%:** the dashboard identifies the service as close to variable break-even;
- **below 90%:** the service is materially below variable break-even on the current assumptions.

This is deliberately not the same as accounting profit. It is a service-operating test intended to answer whether the
additional train movement generates enough revenue to cover the costs treated as avoidable / variable in the model.
        """
    )

    st.markdown("## 8. Break-even passengers and occupancy")
    st.markdown(
        """
The model estimates how many passengers would be required for revenue to cover variable cost, given the current fare and cost
structure. The calculation separates relatively fixed train-running costs from passenger-related variable costs.

The break-even calculation uses:

- average revenue per passenger;
- on-board variable cost per passenger;
- ticketing cost as a share of revenue;
- contingency; and
- the train-running cost that exists before passenger-related costs.

The result is converted into a **break-even occupancy** by dividing break-even passengers by sellable capacity.

This is one of the most useful management indicators in the model. It allows the user to ask, for example, whether a service
needs 55%, 80% or more than 100% occupancy to cover its variable cost. A required occupancy above practical capacity is an
immediate signal that fare, consist, access, traction or other cost assumptions must change; demand growth alone cannot solve
the problem.
        """
    )

    st.markdown("## 9. Full-cost view")
    st.markdown(
        """
The main dashboard focuses on variable cost, but the model also provides a separate **full-cost view**. It allocates two
monthly fixed-cost inputs to each departure:

- locomotive lease / hire cost; and
- route / station fixed cost.

The allocation is:

`Monthly fixed cost ÷ departures per month`

This amount is added to variable cost to produce full cost per departure and a corresponding full-cost recovery ratio.

This distinction matters. A service can cover its variable cost and still fail to recover lease or route-level fixed cost.
Conversely, a service below full-cost recovery may still be rational to operate if the fixed costs would be incurred anyway
and the train makes a positive contribution toward them.
        """
    )

    st.markdown("## 10. Monthly and annual scaling")
    st.markdown(
        """
Once contribution per departure has been calculated, the model scales the result using the operating plan:

`Monthly contribution = contribution per departure × one-way departures per month`

`Annual contribution = monthly contribution × months operated per year`

This makes frequency an explicit scenario variable. It also means the user should ensure that the frequency convention is
applied consistently. If both outbound and inbound train movements are being modelled, each one-way movement should be
represented in the departure count.
        """
    )

    st.markdown("## 11. Alternative-mode passenger financial benefit")
    st.markdown(
        """
The Economic Impact section compares MLPS with a selected alternative mode: **intercity coach, minibus taxi, private car, air,
or a custom comparator**.

The comparator is intentionally editable because the realistic alternative differs by corridor and passenger market. The
model combines the entered alternative fare / journey cost with any transfer or other passenger cost.

The MLPS comparison uses the weighted realised MLPS fare, excluding ancillary revenue, because the purpose is to compare the
passenger's transport cost.

`Passenger saving per passenger = alternative passenger cost − MLPS average ticket fare`

`Total passenger financial benefit = saving per passenger × MLPS passengers`

A positive number means MLPS is cheaper for the passengers carried in the scenario. A negative number means the selected
alternative is cheaper.

This is a **financial saving measure**, not a full consumer-surplus calculation. It does not currently value differences in
journey time, comfort, reliability, safety, schedule convenience or willingness to pay.
        """
    )

    st.markdown("## 12. Rail emissions calculation")
    st.markdown(
        """
Rail emissions are estimated separately for the diesel and electric sections of the route.

### Diesel section
Diesel litres are calculated from:

`Diesel route km × locomotives × litres per loco-km`

CO₂e is then:

`Diesel litres × kg CO₂e per litre`

### Electric section
Electric energy is estimated from:

`Electric route km × kWh per train-km`

CO₂e is then:

`Electric kWh × grid kg CO₂e per kWh`

Total rail CO₂e is the sum of diesel and electric emissions. The model then divides this by passenger-kilometres to produce:

`kg CO₂e per passenger-km`

Because total train emissions are spread over actual passengers, occupancy has a direct effect on emissions intensity. A
lightly loaded train can therefore perform worse per passenger than a well-loaded road alternative.
        """
    )

    st.markdown("## 13. Alternative-mode emissions")
    st.markdown(
        """
For road alternatives, the model estimates how many vehicles are needed to carry the same number of passengers as the MLPS
scenario. Effective vehicle capacity is:

`Vehicle capacity × assumed occupancy`

The model then estimates vehicle fuel consumption over the same route distance and converts that fuel into CO₂e. This is
used for intercity coach, minibus taxi and private-car comparisons.

For air and the custom comparator, emissions are entered directly as **kg CO₂e per passenger-km** and multiplied by passenger
kilometres.

The comparison therefore asks a consistent question: **what would the emissions be if the passengers carried by this MLPS
train made the same trip using the selected alternative?**
        """
    )

    st.markdown("## 14. Emissions saving and carbon value")
    st.markdown(
        """
Emissions saving is:

`Alternative CO₂e − MLPS CO₂e`

A positive result indicates that MLPS emits less. A negative result is retained and displayed as a warning; the model does
not force rail to appear environmentally superior.

The percentage reduction is measured against the alternative-mode emissions baseline.

The model can also monetise the emissions difference:

`CO₂e saving in tonnes × selected carbon value per tonne`

The current carbon value is an editable policy / appraisal input. It should not automatically be interpreted as the full
social cost of carbon.
        """
    )

    st.markdown("## 15. Measurable incremental economic benefit")
    st.markdown(
        """
The model combines two directly modelled incremental effects:

`Passenger financial benefit + monetised carbon benefit`

This is labelled **measurable incremental benefit**.

The term is intentionally narrower than "total economic benefit". The model does not currently attempt to monetise all
possible transport benefits such as time savings, reliability, safety, accessibility, labour-market effects, option value,
road decongestion or infrastructure wear. These could be added later if suitable evidence and appraisal parameters are
available.
        """
    )

    st.markdown("## 16. Wider economic activity supported")
    st.markdown(
        """
The model separately provides an indicative measure of the economic activity associated with passengers undertaking the trip.

Direct associated activity is:

`Passengers × associated spend per passenger`

Total economic activity supported is:

`Direct associated activity × economic activity multiplier`

The difference between the two is shown as the indirect / induced multiplier effect.

This measure is best interpreted as **economic activity associated with or facilitated by the transport service**, not as
an incremental welfare benefit created entirely by MLPS. Some passenger expenditure may have occurred elsewhere in the
absence of the train, and multiplier estimates can overlap with other measures if used carelessly. For this reason, the model
reports wider economic activity separately and deliberately does **not** add it to passenger financial savings and carbon benefit.
        """
    )

    st.markdown("## 17. Economic leverage relative to operating support")
    st.markdown(
        """
Where the service does not cover its variable cost, the shortfall is treated as the **operating support required** for the
selected departure. The model then provides two different leverage indicators:

`Measurable incremental benefit ÷ operating support`

and
`Total economic activity supported ÷ operating support`

These answer different questions and should not be confused. The first compares a narrow set of incremental benefits with the
financial shortfall. The second shows the scale of wider activity associated with each rand of support.

Where variable break-even is achieved, the support denominator is zero and the model intentionally suppresses these ratios
rather than presenting an infinite or misleading value.
        """
    )

    st.markdown("## 18. Sensitivity analysis")
    st.markdown(
        """
The sensitivity table changes **one assumption at a time** while keeping all other current inputs constant. The standard tests
currently include:

- +10 percentage points economy occupancy;
- +10 percentage points sleeper occupancy;
- +10% economy fare;
- +10% sleeper fare;
- −10% access fee;
- −10% diesel price;
- −10% electric traction rate;
- −10% on-board variable cost;
- −10% coach maintenance; and
- −10% crew cost.

Each test reports the resulting recovery ratio, change in recovery, contribution, change in contribution and break-even
occupancy. The table is sorted by improvement in contribution, so the strongest of these standard one-at-a-time levers appears
first.

Sensitivity analysis is not a forecast of what will happen. It is a diagnostic tool showing **which assumptions have the most
financial leverage around the current scenario**.
        """
    )

    st.markdown("## 19. How to use the model in practice")
    st.markdown(
        """
A recommended workflow is:

1. **Select the corridor** and confirm the one-way distance.
2. **Build the likely train consist** and check sellable capacity and train mass.
3. **Set realistic occupancy** separately for economy and sleeper accommodation.
4. Enter the **realised fares** expected to be achieved, not simply aspirational published fares.
5. Confirm the **electric/diesel route split**, access charge, diesel price and traction assumptions.
6. Update variable maintenance, crew, terminal, on-board and ticketing costs with the best available operating evidence.
7. Review **variable-cost recovery, contribution and break-even occupancy** before looking at the wider economic case.
8. Select the **realistic alternative transport mode** for the corridor and use route-specific fare, occupancy, fuel and emissions assumptions where available.
9. Review passenger saving and CO₂e comparison. A negative result should be treated as information, not overridden.
10. Use the wider economic-activity result as contextual evidence, keeping it separate from incremental economic benefit.
11. Run the sensitivity analysis to identify the assumptions that matter most and therefore deserve the strongest evidence or management attention.
12. Save or document the final assumption set when using results in submissions so that the scenario can be reproduced.
        """
    )

    st.markdown("## 20. Interpretation and limitations")
    st.warning(
        "This is a decision-support model, not a certified tariff model, audited financial forecast, engineering simulation "
        "or full economic cost-benefit analysis. Its outputs are only as robust as the assumptions entered."
    )
    st.markdown(
        """
Key limitations to keep in mind:

- Costs are simplified into modelled variable and fixed categories; actual avoidability depends on contractual and operating arrangements.
- The access-fee calculation assumes a linear R/train-km charge.
- Electric traction cost and electric emissions use different engineering representations: the cost side uses GTK and the emissions side uses kWh/train-km. Both require route- and locomotive-specific validation for formal use.
- Train mass is a tare-mass approximation and does not currently add passenger, luggage, catering stock, water or fuel mass.
- Demand is represented through occupancy assumptions; the model does not forecast demand from price, timetable frequency or service quality.
- Revenue does not currently model product-specific discounts, cancellations, no-shows, revenue leakage or directional imbalance separately.
- Break-even assumes the current revenue mix remains broadly applicable as passenger numbers change.
- The alternative-mode financial comparison is a passenger cash-cost comparison, not a full generalised-cost or consumer-surplus model.
- Road emissions depend strongly on assumed vehicle occupancy and fuel consumption.
- Electric emissions depend strongly on the South African grid factor and the assumed kWh/train-km.
- Air emissions are represented by a passenger-kilometre factor rather than a detailed flight model.
- The carbon value is an appraisal / policy assumption and does not represent all environmental externalities.
- The economic-activity multiplier is an indicative scenario input and should be replaced with a suitable South African SAM / input-output estimate for formal economic appraisal.
- The model does not currently monetise travel-time, safety, reliability, road congestion, road maintenance, accessibility or regional-development benefits.
- Outputs should therefore be presented as **scenario estimates**, with the major assumptions disclosed.
        """
    )

    st.markdown("## 21. Current scenario snapshot")
    st.caption("This summary updates automatically from the assumptions entered in the other tabs.")
    methodology_snapshot = calculate(current_inputs(service))
    a, b, c, dcol = st.columns(4)
    a.metric("Route distance", f"{methodology_snapshot['d']['distance']:,.0f} km")
    b.metric("Passengers / departure", n0(methodology_snapshot["passengers"]))
    c.metric("Variable cost recovery", pct(methodology_snapshot["recovery"]))
    dcol.metric("Break-even occupancy", pct(methodology_snapshot["break_even_occ"]))

    a, b, c, dcol = st.columns(4)
    a.metric("Contribution / departure", money(methodology_snapshot["contribution"]))
    b.metric("MLPS CO₂e / departure", f"{methodology_snapshot['train_co2_kg']/1000:,.2f} t")
    c.metric("CO₂e saving vs alternative", f"{methodology_snapshot['co2_saving_tonnes']:,.2f} t")
    dcol.metric("Incremental economic benefit", money(methodology_snapshot["measurable_incremental_benefit"]))

    st.info(
        "For formal use, the strongest version of the model will be one where each material input is supported by a "
        "PRASA, Transnet/TRIM, supplier, metered-energy, market-fare or recognised economic-appraisal source and the "
        "assumption set is retained with the scenario output."
    )

d = current_inputs(service)
r = calculate(d)

st.divider()
st.subheader(f"Executive Dashboard — {service}")

if r["contribution"] >= 0:
    st.markdown('<div class="good">✓ VARIABLE BREAK-EVEN ACHIEVED</div>', unsafe_allow_html=True)
elif r["recovery"] >= 0.90:
    st.markdown('<div class="warn">◐ CLOSE TO VARIABLE BREAK-EVEN</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="bad">✕ BELOW VARIABLE BREAK-EVEN</div>', unsafe_allow_html=True)

st.write("")
a, b, c, dcol = st.columns(4)
a.metric("Revenue / departure", money(r["revenue"]))
b.metric("Variable cost / departure", money(r["variable_cost"]))
c.metric("Contribution / departure", money(r["contribution"]))
dcol.metric("Variable cost recovery", pct(r["recovery"]))

a, b, c, dcol = st.columns(4)
a.metric("Passengers / departure", n0(r["passengers"]))
b.metric("Break-even passengers", n0(r["break_even_pax"]))
c.metric("Current occupancy", pct(r["current_occ"]))
dcol.metric("Break-even occupancy", pct(r["break_even_occ"]))

# Executive visuals
left, right = st.columns([1, 1])

with left:
    st.plotly_chart(recovery_gauge(r["recovery"]), use_container_width=True)

with right:
    traction_df = pd.DataFrame({
        "Mode": ["Electric", "Diesel"],
        "Route km": [r["electric_km"], r["diesel_km"]],
        "Traction cost": [r["electric_cost"], r["diesel_cost"]]
    }).set_index("Mode")
    st.markdown("#### Traction mix")
    st.bar_chart(traction_df[["Route km"]])
    st.caption(
        f"Electric: {r['electric_km']:,.0f} km | Diesel: {r['diesel_km']:,.0f} km"
    )

st.markdown("#### Variable cost breakdown")
cost_df = pd.DataFrame({
    "Cost item": [
        "Access",
        "Electric traction",
        "Diesel fuel",
        "Loco maintenance",
        "Coach maintenance",
        "Crew",
        "Shunting / terminal",
        "On-board variable",
        "Ticketing / collection",
        "Contingency"
    ],
    "Rands": [
        r["access_cost"],
        r["electric_cost"],
        r["diesel_cost"],
        r["loco_maintenance"],
        r["coach_maintenance"],
        r["crew"],
        r["shunting"],
        r["onboard"],
        r["ticketing_cost"],
        r["contingency_cost"]
    ]
}).set_index("Cost item")
st.bar_chart(cost_df)

st.markdown("#### Break-even levers")
a, b, c = st.columns(3)
a.metric("Revenue / passenger", money(r["revenue_per_pax"]), delta=f"Cost {money(r['variable_cost_per_pax'])}")
b.metric("Required revenue uplift", pct(r["required_uplift"]))
c.metric("Annual contribution", money(r["annual_contribution"]))

# -------------------------------------------------------------------
# ECONOMIC IMPACT DASHBOARD
# -------------------------------------------------------------------
st.divider()
st.subheader("Economic & Environmental Impact")
st.caption(
    f"Comparison with **{r['alt_mode']}** using the assumptions in the Economic Impact tab. "
    "Financial and carbon benefits are incremental; wider economic activity is reported separately."
)

a, b, c, dcol = st.columns(4)
a.metric("MLPS avg ticket fare", money(r["avg_ticket_fare"]))
b.metric("Alternative cost / passenger", money(r["alternative_cost_per_pax"]))
c.metric(
    "Passenger saving / passenger",
    money(r["passenger_saving_per_pax"]),
    delta="MLPS cheaper" if r["passenger_saving_per_pax"] >= 0 else "MLPS more expensive"
)
dcol.metric("Total passenger financial benefit", money(r["passenger_financial_benefit"]))

a, b, c, dcol = st.columns(4)
a.metric("MLPS CO₂e / departure", f"{r['train_co2_kg']/1000:,.2f} t")
b.metric(f"{r['alt_mode']} CO₂e", f"{r['alternative_co2_kg']/1000:,.2f} t")
c.metric("CO₂e saving / departure", f"{r['co2_saving_tonnes']:,.2f} t")
dcol.metric("Emissions reduction", f"{r['emissions_reduction']*100:,.1f}%")

a, b, c, dcol = st.columns(4)
a.metric("MLPS kg CO₂e / pax-km", f"{r['train_co2_per_pax_km']:.3f}")
b.metric(f"{r['alt_mode']} kg CO₂e / pax-km", f"{r['alternative_co2_per_pax_km']:.3f}")
c.metric("Monetised carbon benefit", money(r["carbon_benefit"]))
dcol.metric("Measurable incremental benefit", money(r["measurable_incremental_benefit"]))

if r["co2_saving_kg"] >= 0:
    st.markdown(
        f'<div class="good">✓ This scenario emits approximately {r["emissions_reduction"]*100:,.1f}% less CO₂e than the selected alternative.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f'<div class="warn">⚠ This scenario emits approximately {abs(r["emissions_reduction"])*100:,.1f}% more CO₂e than the selected alternative. Occupancy and traction mix matter.</div>',
        unsafe_allow_html=True
    )

st.markdown("#### Wider economic activity supported")
a, b, c = st.columns(3)
a.metric("Direct associated activity", money(r["direct_economic_activity"]))
b.metric("Indirect / induced multiplier effect", money(r["multiplier_effect"]))
c.metric("Total economic activity supported", money(r["total_economic_activity"]))

if r["operating_support"] > 0:
    a, b, c = st.columns(3)
    a.metric("Operating support required", money(r["operating_support"]))
    b.metric(
        "Incremental benefit / R1 support",
        f"{r['economic_benefit_per_support']:.2f}×" if r["economic_benefit_per_support"] is not None else "—"
    )
    c.metric(
        "Economic activity / R1 support",
        f"{r['activity_per_support']:.2f}×" if r["activity_per_support"] is not None else "—"
    )
else:
    st.success(
        "This scenario covers variable operating cost, so no operating support is required at the variable-cost level. "
        "Economic impact is therefore shown without a support-leverage ratio."
    )

impact_df = pd.DataFrame({
    "Measure": ["MLPS", r["alt_mode"]],
    "kg CO₂e / passenger-km": [r["train_co2_per_pax_km"], r["alternative_co2_per_pax_km"]]
}).set_index("Measure")
st.markdown("#### Emissions intensity comparison")
st.bar_chart(impact_df)

with st.expander("Methodology & interpretation"):
    st.markdown(
        "**Passenger financial benefit** compares the selected alternative's passenger journey cost with the weighted "
        "MLPS realised ticket fare. **Carbon benefit** monetises the difference in CO₂e using the selected carbon value. "
        "Their sum is labelled measurable incremental benefit. **Economic activity supported** instead estimates the "
        "direct passenger-associated expenditure and its indirect/induced multiplier effect; it is deliberately not added "
        "to incremental benefit. Road-mode emissions estimate the number of vehicles needed to carry the same passengers "
        "at the selected occupancy. Rail emissions reflect the current diesel/electric route split."
    )

# -------------------------------------------------------------------
# SENSITIVITY ANALYSIS
# -------------------------------------------------------------------
st.divider()
st.subheader("Sensitivity Analysis")
st.caption(
    "Each test changes one assumption at a time while holding all other current assumptions constant."
)

sens = sensitivity_table(d)

display = sens.copy()
display["Recovery"] = display["Recovery"].map(lambda x: f"{x*100:.1f}%")
display["Δ recovery"] = display["Δ recovery"].map(lambda x: f"{x*100:+.1f} pts")
display["Contribution"] = display["Contribution"].map(money)
display["Δ contribution"] = display["Δ contribution"].map(lambda x: f"R {x:+,.0f}")
display["Break-even occupancy"] = display["Break-even occupancy"].map(lambda x: f"{x*100:.1f}%")

st.dataframe(display, use_container_width=True, hide_index=True)

st.markdown("#### Biggest positive levers")
chart_df = sens[["Lever", "Δ contribution"]].set_index("Lever")
st.bar_chart(chart_df)

best = sens.iloc[0]
st.info(
    f"On the current assumptions, the strongest of the standard tests is "
    f"**{best['Lever']}**, improving contribution by approximately "
    f"**{money(best['Δ contribution'])} per departure**."
)

with st.expander("Full-cost view"):
    a, b, c = st.columns(3)
    a.metric("Fixed cost / departure", money(r["fixed_cost_departure"]))
    b.metric("Full cost / departure", money(r["full_cost_departure"]))
    c.metric("Full-cost recovery", pct(r["full_cost_recovery"]))
