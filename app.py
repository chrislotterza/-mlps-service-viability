
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="PRASA LDPT Service Viability",
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
# LDPT Model
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
    "grid_co2_per_kwh": 0.85,
    "electric_kwh_per_train_km": 18.0,
    "coach_capacity": 60,
    "coach_occ": 70,
    "coach_l100km": 30.0,
    "minibus_capacity": 15,
    "minibus_occ": 80,
    "minibus_l100km": 12.0,
    "car_capacity": 5,
    "car_occ": 40,
    "car_l100km": 8.0,
    "air_co2_per_pax_km": 0.15,
    "custom_co2_per_pax_km": 0.08,
    "carbon_value": 1200.0,

    # Wider economic activity assumptions
    "associated_spend_per_pax": 750.0,
    "economic_multiplier": 1.40,
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
    train_electric_kwh = electric_km * d.get("electric_kwh_per_train_km", 18.0)
    train_electric_co2_kg = train_electric_kwh * d.get("grid_co2_per_kwh", 0.85)
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

t1, t2, t3, t4, t5 = st.tabs([
    "🚆 Service & Train",
    "🎟 Fares & Demand",
    "⚡ Traction & Access",
    "🧾 Costs",
    "🌍 Economic Impact"
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
