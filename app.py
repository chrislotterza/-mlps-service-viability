
import streamlit as st
import pandas as pd

st.set_page_config(page_title="MLPS Service Viability", page_icon="🚆", layout="wide")

st.markdown("""
<style>
.block-container {padding-top:1.2rem; max-width:1450px;}
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

SERVICES = {
    "Trans-Karoo": dict(distance=1530, departures=1, months=1, traction="Electric", locos=2,
        economy_coaches=8, sleeper_coaches=4, other_coaches=2, economy_seats=72, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=88.9,
        economy_fare=450, sleeper_fare=750, ancillary=35, economy_occ=65, sleeper_occ=60,
        access_fee=65, electric_rate=0.0627, diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=3, coach_maint=3, crew=12000, shunting=7500, onboard=45,
        ticketing=2.5, contingency=5.0, loco_lease=750000, route_fixed=750000),
    "Amatola": dict(distance=1036, departures=8, months=12, traction="Electric", locos=1,
        economy_coaches=8, sleeper_coaches=4, other_coaches=2, economy_seats=66, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=88.9,
        economy_fare=330, sleeper_fare=500, ancillary=35, economy_occ=65, sleeper_occ=60,
        access_fee=65, electric_rate=0.0627, diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=12, coach_maint=8, crew=12000, shunting=7500, onboard=45,
        ticketing=2.5, contingency=5.0, loco_lease=750000, route_fixed=450000),
    "Johannesburg–Durban": dict(distance=730, departures=11, months=11, traction="Electric", locos=1,
        economy_coaches=8, sleeper_coaches=4, other_coaches=2, economy_seats=66, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=88.9,
        economy_fare=280, sleeper_fare=450, ancillary=35, economy_occ=70, sleeper_occ=60,
        access_fee=65, electric_rate=0.0627, diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=12, coach_maint=8, crew=12000, shunting=7500, onboard=45,
        ticketing=2.5, contingency=5.0, loco_lease=750000, route_fixed=450000),
    "Bosvelder": dict(distance=732, departures=8, months=12, traction="Electric", locos=1,
        economy_coaches=6, sleeper_coaches=3, other_coaches=2, economy_seats=66, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=88.9,
        economy_fare=260, sleeper_fare=420, ancillary=35, economy_occ=60, sleeper_occ=55,
        access_fee=50, electric_rate=0.0627, diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=12, coach_maint=8, crew=12000, shunting=7500, onboard=45,
        ticketing=2.5, contingency=5.0, loco_lease=750000, route_fixed=350000),
    "Custom": dict(distance=500, departures=4, months=12, traction="Diesel", locos=1,
        economy_coaches=6, sleeper_coaches=2, other_coaches=1, economy_seats=66, sleeper_berths=24,
        economy_mass=44, sleeper_mass=48, other_mass=45, loco_mass=90,
        economy_fare=250, sleeper_fare=400, ancillary=25, economy_occ=60, sleeper_occ=55,
        access_fee=50, electric_rate=0.0627, diesel_price=26.16, diesel_consumption=4.3,
        loco_maint=18, coach_maint=8, crew=12000, shunting=7500, onboard=45,
        ticketing=2.5, contingency=5.0, loco_lease=750000, route_fixed=250000),
}

def money(x): return f"R {x:,.0f}"
def pct(x): return f"{x*100:.1f}%"
def n0(x): return f"{x:,.0f}"

def calculate(d):
    econ_occ=d["economy_occ"]/100
    sleep_occ=d["sleeper_occ"]/100
    ticketing=d["ticketing"]/100
    contingency=d["contingency"]/100

    total_coaches=d["economy_coaches"]+d["sleeper_coaches"]+d["other_coaches"]
    sellable_capacity=d["economy_coaches"]*d["economy_seats"]+d["sleeper_coaches"]*d["sleeper_berths"]
    economy_pax=d["economy_coaches"]*d["economy_seats"]*econ_occ
    sleeper_pax=d["sleeper_coaches"]*d["sleeper_berths"]*sleep_occ
    passengers=economy_pax+sleeper_pax

    train_tare_mass=(d["locos"]*d["loco_mass"]+d["economy_coaches"]*d["economy_mass"]+
                     d["sleeper_coaches"]*d["sleeper_mass"]+d["other_coaches"]*d["other_mass"])
    gross_tonne_km=train_tare_mass*d["distance"]

    passenger_revenue=economy_pax*d["economy_fare"]+sleeper_pax*d["sleeper_fare"]
    ancillary_revenue=passengers*d["ancillary"]
    revenue=passenger_revenue+ancillary_revenue

    access_cost=d["distance"]*d["access_fee"]
    traction_cost=(gross_tonne_km*d["electric_rate"] if d["traction"]=="Electric"
                   else d["distance"]*d["locos"]*d["diesel_consumption"]*d["diesel_price"])
    loco_maintenance=d["distance"]*d["locos"]*d["loco_maint"]
    coach_maintenance=d["distance"]*total_coaches*d["coach_maint"]
    crew=d["crew"]
    shunting=d["shunting"]
    onboard=passengers*d["onboard"]
    ticketing_cost=revenue*ticketing

    base_var=access_cost+traction_cost+loco_maintenance+coach_maintenance+crew+shunting+onboard+ticketing_cost
    contingency_cost=base_var*contingency
    variable_cost=base_var+contingency_cost

    contribution=revenue-variable_cost
    recovery=revenue/variable_cost if variable_cost else 0
    variable_cost_per_pax=variable_cost/passengers if passengers else 0
    revenue_per_pax=revenue/passengers if passengers else 0

    fixed_train_running=access_cost+traction_cost+loco_maintenance+coach_maintenance+crew+shunting
    denominator=((revenue_per_pax-d["onboard"]-(revenue_per_pax*ticketing))*(1-contingency))
    break_even_pax=max(0,fixed_train_running*(1+contingency)/denominator) if denominator>0 else 0
    break_even_occ=break_even_pax/sellable_capacity if sellable_capacity else 0
    revenue_gap=max(0,-contribution)
    required_uplift=max(0,variable_cost/revenue-1) if revenue else 0

    fixed_cost_departure=((d["loco_lease"]*d["locos"])+d["route_fixed"])/d["departures"] if d["departures"] else 0
    full_cost_departure=variable_cost+fixed_cost_departure
    full_cost_recovery=revenue/full_cost_departure if full_cost_departure else 0
    monthly_contribution=contribution*d["departures"]
    annual_contribution=monthly_contribution*d["months"]

    return locals()

def load_defaults(service):
    for k,v in SERVICES[service].items():
        st.session_state[k]=v
    st.session_state["_loaded_service"]=service

def current_inputs(service):
    return {k:st.session_state[k] for k in SERVICES[service].keys()}

def save_scenario(name, service):
    inputs=current_inputs(service).copy()
    st.session_state[name]={"service":service,"inputs":inputs,"results":calculate(inputs)}

st.markdown("""
<div class="hero" style="display:flex;align-items:center;gap:22px;">
<div style="flex:0 0 auto;">
<img src="https://rmkcdn.successfactors.com/3adc3a8a/55933741-7481-45cd-b29e-0.png"
alt="PRASA logo" style="height:68px;max-width:220px;object-fit:contain;">
</div>
<div>
<h2 style="margin:0">MLPS Service Viability Model</h2>
<div class="small">PRASA LDPT Viability Decision Making Model</div>
</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Scenario")
    service=st.selectbox("Service",list(SERVICES),index=2)
    if st.session_state.get("_loaded_service")!=service:
        load_defaults(service)
        st.rerun()
    if st.button("↺ Reset service defaults",use_container_width=True):
        load_defaults(service)
        st.rerun()
    st.divider()
    st.caption("Occupancy is entered from 0% to 100%.")
    st.caption("Scenario Planner.")

t1,t2,t3,t4=st.tabs(["🚆 Service & Train","🎟 Fares & Demand","⚡ Access & Traction","🧾 Costs"])

with t1:
    a,b,c=st.columns(3)
    with a:
        st.number_input("One-way distance (km)",min_value=1.0,step=10.0,key="distance")
        st.number_input("One-way departures / month",min_value=1,step=1,key="departures")
        st.number_input("Months operated / year",min_value=1,max_value=12,step=1,key="months")
        st.selectbox("Traction mode",["Electric","Diesel"],key="traction")
    with b:
        st.number_input("Locomotives",min_value=1,step=1,key="locos")
        st.number_input("Economy coaches",min_value=0,step=1,key="economy_coaches")
        st.number_input("Sleeper coaches",min_value=0,step=1,key="sleeper_coaches")
        st.number_input("Other coaches / vans",min_value=0,step=1,key="other_coaches")
    with c:
        st.number_input("Economy seats / coach",min_value=1,step=1,key="economy_seats")
        st.number_input("Sleeper berths / coach",min_value=1,step=1,key="sleeper_berths")
        st.number_input("Economy coach mass (t)",min_value=0.0,step=1.0,key="economy_mass")
        st.number_input("Sleeper coach mass (t)",min_value=0.0,step=1.0,key="sleeper_mass")
        st.number_input("Other coach mass (t)",min_value=0.0,step=1.0,key="other_mass")
        st.number_input("Locomotive mass (t)",min_value=0.0,step=1.0,key="loco_mass")

with t2:
    st.markdown("#### Occupancy")
    a,b=st.columns(2)
    with a: st.slider("Economy occupancy (%)",0,100,step=1,key="economy_occ")
    with b: st.slider("Sleeper occupancy (%)",0,100,step=1,key="sleeper_occ")
    st.markdown("#### Fares & ancillary revenue")
    a,b,c=st.columns(3)
    with a: st.number_input("Economy realised fare (R)",min_value=0.0,step=10.0,key="economy_fare")
    with b: st.number_input("Sleeper realised fare (R)",min_value=0.0,step=10.0,key="sleeper_fare")
    with c: st.number_input("Ancillary net revenue / passenger (R)",min_value=0.0,step=5.0,key="ancillary")

with t3:
    a,b=st.columns(2)
    with a:
        st.number_input("TRIM access fee (R/train-km)",min_value=0.0,step=1.0,key="access_fee")
        st.number_input("Electric traction rate (R/GTK)",min_value=0.0,step=0.01,format="%.4f",key="electric_rate")
    with b:
        st.number_input("Diesel price (R/litre)",min_value=0.0,step=0.10,key="diesel_price")
        st.number_input("Diesel consumption (L/loco-km)",min_value=0.0,step=0.1,key="diesel_consumption")

with t4:
    a,b,c=st.columns(3)
    with a:
        st.number_input("Loco variable maintenance (R/loco-km)",min_value=0.0,step=1.0,key="loco_maint")
        st.number_input("Coach variable maintenance (R/coach-km)",min_value=0.0,step=1.0,key="coach_maint")
        st.number_input("Train crew (R/departure)",min_value=0.0,step=500.0,key="crew")
    with b:
        st.number_input("Shunting / terminal (R/departure)",min_value=0.0,step=500.0,key="shunting")
        st.number_input("On-board variable cost (R/passenger)",min_value=0.0,step=5.0,key="onboard")
        st.slider("Ticketing / collection (% revenue)",0.0,20.0,step=0.5,key="ticketing")
    with c:
        st.slider("Operational contingency (%)",0.0,30.0,step=1.0,key="contingency")
        st.number_input("Locomotive lease / hire (R/month)",min_value=0.0,step=50000.0,key="loco_lease")
        st.number_input("Route / station fixed cost (R/month)",min_value=0.0,step=50000.0,key="route_fixed")

d=current_inputs(service)
r=calculate(d)

st.divider()
st.subheader(f"Executive Dashboard — {service}")

if r["contribution"]>=0:
    st.markdown('<div class="good">✓ VARIABLE BREAK-EVEN ACHIEVED</div>',unsafe_allow_html=True)
elif r["recovery"]>=.90:
    st.markdown('<div class="warn">◐ CLOSE TO VARIABLE BREAK-EVEN</div>',unsafe_allow_html=True)
else:
    st.markdown('<div class="bad">✕ BELOW VARIABLE BREAK-EVEN</div>',unsafe_allow_html=True)

st.write("")
a,b,c,dcol=st.columns(4)
a.metric("Revenue / departure",money(r["revenue"]))
b.metric("Variable cost / departure",money(r["variable_cost"]))
c.metric("Contribution / departure",money(r["contribution"]))
dcol.metric("Variable cost recovery",pct(r["recovery"]))

a,b,c,dcol=st.columns(4)
a.metric("Passengers / departure",n0(r["passengers"]))
b.metric("Break-even passengers",n0(r["break_even_pax"]))
current_occ=(r["passengers"]/r["sellable_capacity"]) if r["sellable_capacity"] else 0
c.metric("Current occupancy",pct(current_occ))
dcol.metric("Break-even occupancy",pct(r["break_even_occ"]))

st.markdown("#### Break-even position")
st.progress(min(max(current_occ,0),1))
a,b,c=st.columns(3)
a.metric("Current average occupancy",pct(current_occ))
b.metric("Break-even occupancy",pct(r["break_even_occ"]))
c.metric("Occupancy margin",f"{(current_occ-r['break_even_occ'])*100:+.1f} pts")

st.markdown("#### Variable cost breakdown")
cost_df=pd.DataFrame({
    "Cost item":["Access","Traction / fuel","Loco maintenance","Coach maintenance","Crew","Shunting / terminal","On-board variable","Ticketing / collection","Contingency"],
    "Rands":[r["access_cost"],r["traction_cost"],r["loco_maintenance"],r["coach_maintenance"],r["crew"],r["shunting"],r["onboard"],r["ticketing_cost"],r["contingency_cost"]]
}).set_index("Cost item")
st.bar_chart(cost_df)

st.markdown("#### What needs to change?")
a,b,c=st.columns(3)
a.metric("Revenue / passenger",money(r["revenue_per_pax"]),delta=f"Cost {money(r['variable_cost_per_pax'])}")
b.metric("Required revenue uplift",pct(r["required_uplift"]))
c.metric("Annual contribution",money(r["annual_contribution"]))

st.divider()
st.subheader("Scenario Comparison")
st.caption("Save the current settings as Scenario A or B, then change assumptions and compare.")

a,b,c=st.columns([1,1,2])
with a:
    if st.button("Save as Scenario A",use_container_width=True):
        save_scenario("scenario_a",service)
        st.success("Scenario A saved.")
with b:
    if st.button("Save as Scenario B",use_container_width=True):
        save_scenario("scenario_b",service)
        st.success("Scenario B saved.")
with c:
    if st.button("Clear scenarios",use_container_width=True):
        st.session_state.pop("scenario_a",None)
        st.session_state.pop("scenario_b",None)
        st.rerun()

if "scenario_a" in st.session_state and "scenario_b" in st.session_state:
    A=st.session_state["scenario_a"]
    B=st.session_state["scenario_b"]
    comparison=pd.DataFrame({
        "Metric":["Service","Economy fare","Sleeper fare","Economy occupancy","Sleeper occupancy","Revenue / departure","Variable cost / departure","Contribution / departure","Variable cost recovery","Break-even occupancy","Annual contribution"],
        "Scenario A":[A["service"],money(A["inputs"]["economy_fare"]),money(A["inputs"]["sleeper_fare"]),f'{A["inputs"]["economy_occ"]:.0f}%',f'{A["inputs"]["sleeper_occ"]:.0f}%',money(A["results"]["revenue"]),money(A["results"]["variable_cost"]),money(A["results"]["contribution"]),pct(A["results"]["recovery"]),pct(A["results"]["break_even_occ"]),money(A["results"]["annual_contribution"])],
        "Scenario B":[B["service"],money(B["inputs"]["economy_fare"]),money(B["inputs"]["sleeper_fare"]),f'{B["inputs"]["economy_occ"]:.0f}%',f'{B["inputs"]["sleeper_occ"]:.0f}%',money(B["results"]["revenue"]),money(B["results"]["variable_cost"]),money(B["results"]["contribution"]),pct(B["results"]["recovery"]),pct(B["results"]["break_even_occ"]),money(B["results"]["annual_contribution"])]
    })
    st.dataframe(comparison,use_container_width=True,hide_index=True)
else:
    st.info("Save both Scenario A and Scenario B to see the comparison table.")

with st.expander("Full-cost view"):
    a,b,c=st.columns(3)
    a.metric("Fixed cost / departure",money(r["fixed_cost_departure"]))
    b.metric("Full cost / departure",money(r["full_cost_departure"]))
    c.metric("Full-cost recovery",pct(r["full_cost_recovery"]))
