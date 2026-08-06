import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random

st.set_page_config(
    page_title="Pro Quantitative & Behavioral Simulator",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .ui-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 24px; border-radius: 12px; border: 1px solid #334155;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4); margin-bottom: 24px;
    }
    .ai-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #311b92 100%);
        padding: 24px; border-radius: 12px; border: 1px solid #6366f1;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.2); margin-top: 24px;
    }
    h1, h2, h3 { color: #f8fafc; font-weight: 700; }
    .stProgress .st-bo { background-color: #38bdf8; }
    .metric-box {
        background-color: #0f172a; padding: 15px; border-radius: 8px; margin-top: 15px; margin-bottom: 10px; border-left: 4px solid #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

TAX_DATA = pd.DataFrame([
    {"iso_alpha": "USA", "country": "United States", "region": "North America", "tax_rate": 20.0},
    {"iso_alpha": "CAN", "country": "Canada", "region": "North America", "tax_rate": 25.0},
    {"iso_alpha": "FRA", "country": "France", "region": "Europe", "tax_rate": 30.0},
    {"iso_alpha": "DEU", "country": "Germany", "region": "Europe", "tax_rate": 26.375},
    {"iso_alpha": "GBR", "country": "United Kingdom", "region": "Europe", "tax_rate": 20.0},
    {"iso_alpha": "CHE", "country": "Switzerland", "region": "Europe", "tax_rate": 0.0},
    {"iso_alpha": "ARE", "country": "UAE", "region": "Middle East", "tax_rate": 0.0},
    {"iso_alpha": "SGP", "country": "Singapore", "region": "Asia", "tax_rate": 0.0},
    {"iso_alpha": "JPN", "country": "Japan", "region": "Asia", "tax_rate": 20.315},
    {"iso_alpha": "AUS", "country": "Australia", "region": "Oceania", "tax_rate": 24.0},
    {"iso_alpha": "BRA", "country": "Brazil", "region": "South America", "tax_rate": 15.0}
])

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'responses' not in st.session_state:
    st.session_state.responses = {}


def next_step(): st.session_state.step += 1


def prev_step(): st.session_state.step -= 1


def calculate_behavior_profile(resp):
    scores = {
        "Discipline": 100,
        "Risk_Management": 100,
        "Emotional_Control": 100,
        "Instant_Fail": False
    }

    if "Yes, position sizing" not in resp.get('q7', ''): scores["Risk_Management"] -= 30
    if "predefined structural point" not in resp.get('q8', ''): scores["Risk_Management"] -= 20
    if "I have no limit" in resp.get('q9', ''):
        scores["Risk_Management"] -= 50
        scores["Instant_Fail"] = True

    if "re-enter immediately" in resp.get('q10', '') or "blame market" in resp.get('q10', ''): scores[
        "Emotional_Control"] -= 30
    if "double my size" in resp.get('q11', ''): scores["Emotional_Control"] -= 40
    if "market-buy immediately" in resp.get('q12', ''): scores["Emotional_Control"] -= 25
    if "abandon my strategy" in resp.get('q14', ''): scores["Emotional_Control"] -= 30

    if "No, my broker history" in resp.get('q16', ''): scores["Discipline"] -= 25
    if "gamble" in resp.get('q18', ''): scores["Discipline"] -= 30
    if "False. Capital magnifies" not in resp.get('q21', ''): scores["Discipline"] -= 20
    if "Accept the -5%" not in resp.get('q6', ''): scores["Discipline"] -= 20

    for k in ["Discipline", "Risk_Management", "Emotional_Control"]:
        scores[k] = max(0, min(100, scores[k]))

    scores["Global"] = (scores["Discipline"] + scores["Risk_Management"] + scores["Emotional_Control"]) / 3
    return scores


def run_simulation(resp, profiles, days_in_year=252):
    initial_capital = resp.get('initial_capital', 10000)
    monthly_injection = resp.get('monthly_injection', 0)
    tax_rate = resp.get('tax_rate', 0) / 100
    tax_frequency = resp.get('tax_frequency', 'Monthly')
    reset_strategy = resp.get('reset_strategy', 'Compound everything')
    inflation_rate = resp.get('inflation_rate', 3.0) / 100
    asset_class = resp.get('q2', 'Stocks')

    if asset_class == "Crypto":
        vol_mod = 1.8;
        gap_prob = 0.15;
        slip_range = (0.10, 0.25)
    elif asset_class == "Forex":
        vol_mod = 1.2;
        gap_prob = 0.05;
        slip_range = (0.02, 0.15)
    elif asset_class == "Indices":
        vol_mod = 0.9;
        gap_prob = 0.08;
        slip_range = (0.05, 0.10)
    else:
        vol_mod = 1.0;
        gap_prob = 0.10;
        slip_range = (0.05, 0.15)

    dates = pd.date_range(start='2020-01-01', periods=days_in_year, freq='B')

    total_invested = initial_capital
    current_capital = initial_capital
    base_capital = initial_capital
    month_start_capital = initial_capital
    total_taxes_paid = 0.0

    plot_dates, plot_caps_nominal, plot_caps_monthly, event_labels = [], [], [], []
    month_boundaries = []

    wins = total_trades = 0
    peak_capital = current_capital
    max_loss_pct = 0.0

    win_prob_base = 0.55 if profiles["Emotional_Control"] > 75 else (
        0.45 if profiles["Emotional_Control"] > 45 else 0.35)
    margin_call_day = random.randint(120, 180) if profiles["Instant_Fail"] else -1

    np.random.seed(42)
    random.seed(42)

    for day in range(days_in_year):
        current_date = dates[day]
        event_today = ""

        if day < 84:
            regime_mod = 1.2
        elif day < 168:
            regime_mod = 0.6
        else:
            regime_mod = 0.85

        if random.random() < 0.6:
            total_trades += 1
            risk_amount = current_capital * 0.01
            fee = risk_amount * 0.10

            if random.random() < (win_prob_base * regime_mod):
                wins += 1
                mean_rr = 2.0 if profiles["Discipline"] > 60 else 1.2
                rr = max(0.5, np.random.normal(loc=mean_rr, scale=vol_mod * 0.5))
                profit = (risk_amount * rr) - fee
                current_capital += profit
                event_today = f"Win (+{rr:.1f}R)" if rr > 3.0 else ""
            else:
                slippage = risk_amount * random.uniform(*slip_range)
                is_gap = random.random() < gap_prob

                if is_gap and profiles["Risk_Management"] < 80:
                    gap_multiplier = max(1.5, np.random.normal(loc=3.0, scale=1.5))
                    loss = (risk_amount * gap_multiplier) + slippage + fee
                    event_today = "⚠️ Weekend Gap Down!"
                else:
                    loss = risk_amount + slippage + fee

                current_capital -= loss

        if day == margin_call_day and current_capital > 0:
            current_capital *= 0.10
            event_today = "🔥 MARGIN CALL (No DD Limit)"

        if current_capital > peak_capital:
            peak_capital = current_capital
        drawdown = ((peak_capital - current_capital) / peak_capital) * 100
        if drawdown > max_loss_pct: max_loss_pct = drawdown

        plot_dates.append(current_date)
        plot_caps_nominal.append(current_capital)
        plot_caps_monthly.append((current_capital - month_start_capital) + monthly_injection)
        event_labels.append(event_today)

        if (day + 1) % 21 == 0:
            monthly_profit = current_capital - base_capital
            if "Monthly" in tax_frequency and monthly_profit > 0:
                tax = monthly_profit * tax_rate
                total_taxes_paid += tax
                current_capital -= tax

            if "Strict Reset" in reset_strategy:
                if current_capital < base_capital: total_invested += (base_capital - current_capital)
                current_capital = base_capital
            elif "Withdraw profits only" in reset_strategy and current_capital > base_capital:
                current_capital = base_capital

            current_capital += monthly_injection
            total_invested += monthly_injection
            base_capital = current_capital
            month_start_capital = current_capital

            if day != days_in_year - 1:
                plot_dates.append(current_date + pd.Timedelta(hours=12))
                plot_caps_nominal.append(np.nan)
                plot_caps_monthly.append(np.nan)
                event_labels.append("")
                month_boundaries.append(current_date + pd.Timedelta(hours=12))

    if "Annually" in tax_frequency:
        total_net_profit = current_capital - total_invested
        if total_net_profit > 0:
            tax = total_net_profit * tax_rate
            total_taxes_paid += tax
            current_capital -= tax

    df = pd.DataFrame({'Date': plot_dates, 'Nominal_Capital': plot_caps_nominal, 'Monthly_Zoom': plot_caps_monthly,
                       'Event': event_labels})
    df.set_index('Date', inplace=True)

    valid_dates_mask = df['Nominal_Capital'].notna()
    days_elapsed = (df.index.to_series()[valid_dates_mask] - df.index[0]).dt.days
    discount_factors = (1 + inflation_rate) ** (days_elapsed / 365.25)
    df['Real_Capital'] = np.nan
    df.loc[valid_dates_mask, 'Real_Capital'] = df.loc[valid_dates_mask, 'Nominal_Capital'] / discount_factors.values

    yearly_profits = current_capital - total_invested
    regime_dates = [dates[0], dates[83], dates[167], dates[-1]]

    return df, month_boundaries, regime_dates, total_invested, current_capital, total_taxes_paid, max_loss_pct, wins, total_trades, yearly_profits


st.progress(min(st.session_state.step / 5, 1.0))

if st.session_state.step == 1:
    st.title("🛡️ Institutional Trading & Behavioral Simulator")
    st.markdown("""
    <div class="ui-card">
        <h3 style="color: #60a5fa;">Mission & Reality Check</h3>
        <p>This simulator is currently a project in development. As part of future research, a trained AI will be integrated to enhance modeling. Right now, it shatters the "fairy tale" illusions of trading. Financial ruin impacts your entire life. You will face realistic market mechanics powered by Normal Distribution mathematics: <strong>slippage, asymmetric volatility, and brutal weekend market gaps.</strong></p>
    </div>
    """, unsafe_allow_html=True)
    st.button("I understand the risks. Proceed ➔", on_click=next_step)

elif st.session_state.step == 2:
    st.title("🌍 Step 1: Select Your Jurisdiction")
    st.write("Click directly on your country/continent on the map to set your Capital Gains Tax rate.")

    col1, col2 = st.columns([2, 1])
    with col1:
        fig_map = px.choropleth(TAX_DATA, locations="iso_alpha", color="tax_rate", hover_name="country",
                                color_continuous_scale="Blues", projection="natural earth")
        fig_map.update_geos(showcountries=True, countrycolor="#334155", showland=True, landcolor="#0f172a",
                            showocean=True, oceancolor="#020617")
        fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)")
        event = st.plotly_chart(fig_map, on_select="rerun", selection_mode="points", use_container_width=True)

    with col2:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        selected_country = TAX_DATA.iloc[event.selection.points[0]["point_index"]][
            "country"] if event and event.selection.points else "United States"
        tax_rate = TAX_DATA[TAX_DATA["country"] == selected_country]["tax_rate"].values[0]
        st.metric("Capital Gains Tax Rate", f"{tax_rate}%")
        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.responses['tax_rate'] = tax_rate

    col_b1, col_b2 = st.columns([1, 5])
    with col_b1:
        st.button("⬅️ Back", on_click=prev_step)
    with col_b2:
        st.button("Proceed to Financials ➔", on_click=next_step)

elif st.session_state.step == 3:
    st.title("💰 Step 2: Capital & Taxation Logistics")
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.responses['initial_capital'] = st.number_input("Starting Capital ($)", min_value=100,
                                                                        value=10000, step=1000)
        st.session_state.responses['monthly_injection'] = st.number_input("Monthly Capital Injection / DCA ($):",
                                                                          min_value=0, value=0, step=100)
        st.session_state.responses['inflation_rate'] = st.slider("Expected Annual Inflation (%)", min_value=1.0,
                                                                 max_value=10.0, value=3.0, step=0.1)

    with col2:
        tax_freq = st.radio("When do you withdraw money for taxes?",
                            ["Monthly (Deducted each month)", "Annually (Compound all year)"])
        st.session_state.responses['tax_frequency'] = tax_freq
        if "Monthly" in tax_freq:
            st.session_state.responses['reset_strategy'] = st.radio("Monthly Capital Reset Strategy:",
                                                                    ["Strict Reset (Withdraw & Refill)",
                                                                     "Withdraw profits only",
                                                                     "Compound everything (Carry all profits and losses)"])

    st.markdown('</div>', unsafe_allow_html=True)
    col_b1, col_b2 = st.columns([1, 5])
    with col_b1:
        st.button("⬅️ Back", on_click=prev_step)
    with col_b2:
        st.button("Proceed to Assessment ➔", on_click=next_step)

elif st.session_state.step == 4:
    st.title("🧠 Step 3: Deep Behavioral Assessment")

    st.subheader("Part 1: Strategy")
    q1 = st.selectbox("1. Primary MA Strategy:",
                      ["SMA 20/50", "SMA 50/200", "EMA 20/50", "EMA 50/200", "A moving average I created"])
    q2 = st.selectbox("2. Preferred Asset Class (Affects Volatility):", ["Stocks", "Indices", "Crypto", "Forex"])
    q3 = st.selectbox("3. Trading Days:", ["Monday to Friday only", "Every day including weekends (Crypto)",
                                           "Only 2-3 specific days a week"])
    q4 = st.selectbox("4. Trading Hours:", ["Only highly liquid opens (London/NY)", "Asian session (Low volatility)",
                                            "Staring at charts all day"])
    q5 = st.radio("5. How do you take profits?",
                  ["Fixed Risk/Reward (e.g., 1:2)", "Trailing Stop Loss", "Gut feeling / When it looks like reversing"])

    st.subheader("Part 2: Risk Management")
    q6 = st.radio(
        "6. You hold a trade over the weekend. Monday opens with a massive gap down (-5% capital). What do you do?",
        ["Accept the -5% market execution and close immediately.", "Hold the trade, hoping it fills the gap.",
         "Average down (buy more) because it's 'discounted'."])
    q7 = st.radio("7. Do you strictly risk only 1% of your total capital per trade?",
                  ["Yes, position sizing is strictly calculated every time.", "Mostly, but I round up numbers.",
                   "No, I trade fixed lot sizes."])
    q8 = st.radio("8. When do you move your Stop Loss to Breakeven?",
                  ["At a predefined structural point (e.g., 1R profit).",
                   "As soon as it's slightly in profit because I fear losing.", "I rarely use hard Stop Losses."])
    q9 = st.radio("9. What is your Max Daily Drawdown limit?",
                  ["2% to 3%. Once hit, the platform is closed.", "Around 5%, then I try to be careful.",
                   "I have no limit, I trade until I make it back."])
    q10 = st.radio("10. A trade hits your SL, but immediately reverses into your original direction. Reaction?",
                   ["It's part of the game. I wait for the next setup.", "I re-enter immediately out of frustration.",
                    "I blame market manipulation and increase leverage."])

    st.subheader("Part 3: Psychology")
    q11 = st.radio("11. You are on a 5-trade losing streak. Mindset?",
                   ["Take a break, review the journal.", "Slightly angry, but I keep trading my edge.",
                    "Furious. I double my size to recover."])
    q12 = st.radio("12. You see a massive 15% momentum candle print WITHOUT you. FOMO strikes.",
                   ["I do nothing. Chasing is how you die.", "I wait for a minor pullback and jump in.",
                    "I market-buy immediately."])
    q13 = st.radio("13. You hit your weekly profit target on Tuesday morning.",
                   ["I stop trading for the week.", "I keep trading normally.", "I increase my risk (house money)."])
    q14 = st.radio("14. Your portfolio is currently in a 12% drawdown.",
                   ["Normal business.", "I am losing sleep.", "I abandon my strategy and look for a new indicator."])
    q15 = st.radio("15. You see a 19-year-old on Twitter make your yearly salary in one trade.",
                   ["I mute them.", "I feel inadequate and force a trade.", "I buy their course."])

    st.subheader("Part 4: Routine")
    q16 = st.radio("16. Do you maintain a detailed trading journal?",
                   ["Yes, log emotions and mistakes daily.", "Only when I win.",
                    "No, my broker history is my journal."])
    q17 = st.radio("17. Pre-market routine:",
                   ["Review calendar, mark key levels.", "Turn on the screens and look for movement.",
                    "Trade directly from my phone in bed."])
    q18 = st.radio("18. Reaction to major news events:",
                   ["I am flat (no positions).", "I widen my SL.", "I gamble and enter a heavy position."])
    q19 = st.radio("19. Health/Sleep effect:",
                   ["I don't trade if highly stressed.", "I trade anyway, caffeine fixes it.",
                    "I use trading to escape real-life stress."])
    q20 = st.radio("20. Define a 'successful' day:",
                   ["Following my rules perfectly.", "Making money.", "Making a lot of money."])
    q21 = st.radio("21. 'If I just had more capital, I would be profitable.'",
                   ["False. Capital magnifies bad habits.", "True. I could use less leverage.",
                    "True. I just need one big account."])

    st.session_state.responses.update(
        {'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'q5': q5, 'q6': q6, 'q7': q7, 'q8': q8, 'q9': q9, 'q10': q10,
         'q11': q11, 'q12': q12, 'q13': q13, 'q14': q14, 'q15': q15, 'q16': q16, 'q17': q17, 'q18': q18, 'q19': q19,
         'q20': q20, 'q21': q21})

    col_b1, col_b2 = st.columns([1, 5])
    with col_b1:
        st.button("⬅️ Back", on_click=prev_step)
    with col_b2:
        st.button("Run Year-Long Simulation ➔", on_click=next_step)

elif st.session_state.step == 5:
    st.title("📊 Step 4: Post-Simulation Quantitative Dashboard")

    resp = st.session_state.responses
    profiles = calculate_behavior_profile(resp)
    df, month_bounds, regimes, tot_invested, final_cap, taxes, max_loss, wins, trades, pnl = run_simulation(resp,
                                                                                                            profiles)

    col_rad, col_met = st.columns([1, 2])
    with col_rad:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=[profiles["Discipline"], profiles["Risk_Management"], profiles["Emotional_Control"],
               profiles["Discipline"]],
            theta=['Discipline', 'Risk Management', 'Emotional Control', 'Discipline'],
            fill='toself', line_color='#38bdf8'
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False,
                                margin=dict(l=30, r=30, t=30, b=30), height=250, paper_bgcolor="rgba(0,0,0,0)",
                                font_color="#e2e8f0")
        st.plotly_chart(fig_radar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_met:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Invested", f"${tot_invested:,.2f}")
        c2.metric("Final Capital (Before Tax)", f"${(final_cap + taxes):,.2f}")
        c3.metric("Final Capital (After Tax)", f"${final_cap:,.2f}")

        st.write("")

        if st.toggle("🔍 Show Detailed Metrics"):
            st.markdown('<div class="metric-box">', unsafe_allow_html=True)
            dc1, dc2, dc3, dc4 = st.columns(4)
            dc1.metric("Max Drawdown", f"{max_loss:.2f}%")
            dc2.metric("Total Taxes Paid", f"${taxes:,.2f}")
            win_rate = (wins / trades) * 100 if trades > 0 else 0
            avg_profit = pnl / trades if trades > 0 else 0
            dc3.metric("Win Rate", f"{win_rate:.1f}%")
            dc4.metric("Avg PnL / Trade", f"${avg_profit:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        graph_view = st.selectbox("Graph View Style:", ["Cumulative (Full Year)", "Monthly Zoom (Volatility)"])
    with c2:
        show_inflation = st.checkbox("Apply Inflation Adjustment", value=True)

    fig = go.Figure()
    hover_temp = "<b>Date:</b> %{x|%d %b %Y}<br><b>Capital:</b> $%{y:,.2f}<br><span style='color:orange'>%{customdata}</span><extra></extra>"

    if "Monthly" in graph_view:
        fig.add_trace(go.Scatter(x=df.index, y=df['Monthly_Zoom'], mode='lines', line=dict(color='#eab308', width=3),
                                 customdata=df['Event'], hovertemplate=hover_temp))
    else:
        if show_inflation:
            fig.add_trace(go.Scatter(x=df.index, y=df['Real_Capital'], mode='lines', name='Real (Adjusted)',
                                     line=dict(color='#10b981', width=3), customdata=df['Event'],
                                     hovertemplate=hover_temp))
            fig.add_trace(go.Scatter(x=df.index, y=df['Nominal_Capital'], mode='lines', name='Nominal',
                                     line=dict(color='#64748b', width=1.5, dash='dot'), customdata=df['Event'],
                                     hovertemplate=hover_temp))
        else:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Nominal_Capital'], mode='lines', line=dict(color='#38bdf8', width=3),
                           customdata=df['Event'], hovertemplate=hover_temp))

    fig.add_vrect(x0=regimes[0], x1=regimes[1], fillcolor="green", opacity=0.1, layer="below", line_width=0,
                  annotation_text="Bull Market", annotation_font_color="green")
    fig.add_vrect(x0=regimes[1], x1=regimes[2], fillcolor="red", opacity=0.1, layer="below", line_width=0,
                  annotation_text="Bear Market", annotation_font_color="red")
    fig.add_vrect(x0=regimes[2], x1=regimes[3], fillcolor="orange", opacity=0.1, layer="below", line_width=0,
                  annotation_text="Chop / Volatility", annotation_font_color="orange")

    for b in month_bounds: fig.add_vline(x=b, line_dash="dash", line_color="rgba(255,255,255,0.15)", line_width=1)

    event_mask = df['Event'] != ""
    if event_mask.any():
        fig.add_trace(go.Scatter(x=df[event_mask].index,
                                 y=df.loc[event_mask, 'Monthly_Zoom' if "Monthly" in graph_view else 'Nominal_Capital'],
                                 mode='markers', marker=dict(color='red', size=8, symbol='x'), name='Market Event',
                                 customdata=df.loc[event_mask, 'Event'], hovertemplate=hover_temp))

    fig.update_layout(template="plotly_dark", height=450, hovermode="x unified", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="ai-card">', unsafe_allow_html=True)
    if profiles["Instant_Fail"]:
        st.error(
            f"💀 **CRITICAL FAILURE:** Your lack of a daily Drawdown limit caused a total account liquidation (Margin Call). The market does not care about your feelings. You MUST implement a hard limit before trading real money.")
    elif profiles["Global"] >= 80:
        st.success(
            f"📈 **Analysis (Score: {profiles['Global']:.0f}/100):** Excellent discipline. Notice how your account survived the Bear Market due to strict risk management. Keep it up.")
    elif profiles["Global"] >= 50:
        st.warning(
            f"⚠️ **Analysis (Score: {profiles['Global']:.0f}/100):** You survived, but your emotional control is lacking. Look at the radar chart: FOMO and revenge trading caused unnecessary drawdowns during the Choppy phase.")
    else:
        st.error(
            f"🚨 **Analysis (Score: {profiles['Global']:.0f}/100):** High risk of ruin. Your psychological profile guarantees destruction under real market stress. Do NOT trade live.")

    st.markdown("""
    <div style="background-color: #0f172a; padding: 18px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #f59e0b; font-size: 0.95em; color: #cbd5e1;">
        <b>⚠️ Disclaimer & Limitations:</b> Human behavior is never permanently fixed, and external factors (macroeconomic news, unexpected geopolitical shifts, or sudden black swan events) can radically disrupt market conditions. This simulation serves as a psychological baseline and risk awareness tool—it should <b>never</b> be used as a standalone crystal ball or absolute guarantee for live market success.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #1e1b4b; padding: 18px; border-radius: 8px; margin-top: 15px; margin-bottom: 15px; border-left: 4px solid #6366f1; font-size: 0.95em; color: #e2e8f0;">
        <b>🚀 Future Development Roadmap:</b> Human behavior is not static, and markets face unpredictable external shocks (macroeconomic news, black swans). Therefore, this simulator is designed to evolve. 
        <br><br>
        In future versions, the integration of finer <b>multi-scale timeframes</b> and an adaptive <b>AI behavioral model</b> will enable the simulation of dynamic real-time psychological reactions, bringing this simulation much closer to real-world complexity.
    </div>
    """, unsafe_allow_html=True)

    col_restart, col_export = st.columns(2)
    with col_restart:
        st.button("🔄 Restart Simulator", on_click=lambda: st.session_state.update(step=1))
    with col_export:
        csv = df[['Nominal_Capital', 'Real_Capital', 'Event']].to_csv().encode('utf-8')
        st.download_button(label="📥 Download Data (CSV)", data=csv, file_name='trading_simulation.csv', mime='text/csv')
    st.markdown('</div>', unsafe_allow_html=True)
