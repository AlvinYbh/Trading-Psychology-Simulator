# requirements.txt
# streamlit>=1.35.0
# pandas
# numpy
# plotly

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Pro Quantitative & Behavioral Simulator",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS (DARK PREMIUM THEME) ---
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
</style>
""", unsafe_allow_html=True)

# --- TAX DATA ---
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
    {"iso_alpha": "BRA", "country": "Brazil", "region": "South America", "tax_rate": 15.0},
    {"iso_alpha": "ZAF", "country": "South Africa", "region": "Africa", "tax_rate": 18.0}
])

# --- SESSION STATE INITIALIZATION ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'responses' not in st.session_state:
    st.session_state.responses = {}


def next_step(): st.session_state.step += 1


def prev_step(): st.session_state.step -= 1


st.progress(st.session_state.step / 5)

# ==============================================================================
# STEP 1: INTRODUCTION
# ==============================================================================
if st.session_state.step == 1:
    st.title("🛡️ Institutional Trading & Behavioral Simulator")

    st.markdown("""
    <div class="ui-card">
        <h3 style="color: #60a5fa;">Mission & Reality Check</h3>
        <p>This simulator is built to shatter the "fairy tale" illusions of trading. Financial ruin impacts not just the trader, but their entire family and community.</p>
        <p>You will face realistic market mechanics: <strong>0.1% fees, slippage, and brutal weekend market gaps that destroy Stop Losses.</strong> Before risking real capital, discover if your psychology can survive.</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("I understand the risks. Proceed ➔", on_click=next_step)

# ==============================================================================
# STEP 2: INTERACTIVE MAP (JURISDICTION)
# ==============================================================================
elif st.session_state.step == 2:
    st.title("🌍 Step 1: Select Your Jurisdiction")
    st.write("Click directly on your country/continent on the map to set your Capital Gains Tax rate.")

    col1, col2 = st.columns([2, 1])

    with col1:
        fig_map = px.choropleth(
            TAX_DATA, locations="iso_alpha", color="tax_rate", hover_name="country",
            color_continuous_scale="Blues", projection="natural earth"
        )
        fig_map.update_geos(showcountries=True, countrycolor="#334155", showland=True, landcolor="#0f172a",
                            showocean=True, oceancolor="#020617", showlakes=False)
        fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False)

        # Clickable Map Feature (Streamlit 1.35+)
        event = st.plotly_chart(fig_map, on_select="rerun", selection_mode="points", use_container_width=True)

    with col2:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        # Fallback / Display logic
        selected_country = "United States"
        if event and event.selection.points:
            selected_idx = event.selection.points[0]["point_index"]
            selected_country = TAX_DATA.iloc[selected_idx]["country"]
            st.success(f"Map Selection: **{selected_country}**")
        else:
            st.info("You can click the map, or use the dropdown below.")
            selected_country = st.selectbox("Fallback Selection:", TAX_DATA["country"].tolist())

        tax_rate = TAX_DATA[TAX_DATA["country"] == selected_country]["tax_rate"].values[0]
        st.metric("Capital Gains Tax Rate", f"{tax_rate}%")
        st.markdown('</div>', unsafe_allow_html=True)

        st.session_state.responses['tax_rate'] = tax_rate
        st.session_state.responses['country'] = selected_country

    col_b1, col_b2 = st.columns([1, 5])
    with col_b1:
        st.button("⬅️ Back", on_click=prev_step)
    with col_b2:
        st.button("Proceed to Financials ➔", on_click=next_step)

# ==============================================================================
# STEP 3: FINANCIAL PARAMETERS
# ==============================================================================
elif st.session_state.step == 3:
    st.title("💰 Step 2: Capital & Taxation Logistics")
    st.write("Set your capital injection and tax withdrawal schedule for the 1-year simulation.")

    st.markdown('<div class="ui-card">', unsafe_allow_html=True)

    st.session_state.responses['initial_capital'] = st.number_input("Starting Capital ($)", min_value=100, value=10000,
                                                                    step=1000)

    st.session_state.responses['tax_frequency'] = st.radio(
        "When do you declare and withdraw money for taxes/living?",
        ["Monthly (Taxes/withdrawals deducted at the end of each month)",
         "Annually (Compound all year, deduct taxes on year-end net profit)"]
    )

    st.session_state.responses['monthly_injection'] = st.number_input(
        "Monthly Capital Injection / DCA ($) added to account:", min_value=0, value=0, step=100)

    st.markdown('</div>', unsafe_allow_html=True)

    col_b1, col_b2 = st.columns([1, 5])
    with col_b1:
        st.button("⬅️ Back", on_click=prev_step)
    with col_b2:
        st.button("Proceed to Assessment ➔", on_click=next_step)

# ==============================================================================
# STEP 4: 21-QUESTION BEHAVIORAL ASSESSMENT
# ==============================================================================
elif st.session_state.step == 4:
    st.title("🧠 Step 3: Deep Behavioral Assessment")
    st.write(
        "Be completely honest. The AI will cross-reference your answers to simulate your real win rate and drawdown.")

    with st.container():
        st.subheader("Part 1: Strategy & Logistics")
        q1 = st.selectbox("1. Primary MA Strategy:",
                          ["SMA 20/50", "SMA 50/200", "EMA 20/50", "EMA 50/200", "AAMA Adaptive"])
        q2 = st.selectbox("2. Preferred Asset Class:", ["Stocks", "Indices", "Crypto", "Forex"])
        q3 = st.selectbox("3. Trading Days:", ["Monday to Friday only", "Every day including weekends (Crypto)",
                                               "Only 2-3 specific days a week"])
        q4 = st.selectbox("4. Trading Hours:",
                          ["Only highly liquid opens (London/NY)", "Asian session (Low volatility)",
                           "Staring at charts all day"])
        q5 = st.radio("5. How do you take profits?", ["Fixed Risk/Reward (e.g., 1:2)", "Trailing Stop Loss",
                                                      "Gut feeling / When it looks like reversing"])

        st.markdown("---")
        st.subheader("Part 2: Risk Management & Realism")
        q6 = st.radio(
            "6. You hold a swing trade over the weekend. Monday opens with a massive gap down, putting you at -5% capital (Your SL was at -2%). What do you do?",
            ["Accept the -5% market execution and close immediately.",
             "Hold the trade, hoping it fills the gap and goes back to -2%.",
             "Average down (buy more) because it's 'discounted'."])
        q7 = st.radio("7. Do you strictly risk only 1% of your total capital per trade?",
                      ["Yes, position sizing is strictly calculated every time.", "Mostly, but I round up numbers.",
                       "No, I trade fixed lot sizes regardless of stop distance."])
        q8 = st.radio("8. When do you move your Stop Loss to Breakeven?",
                      ["At a predefined structural point (e.g., 1R profit).",
                       "As soon as it's slightly in profit because I fear losing.", "I rarely use hard Stop Losses."])
        q9 = st.radio("9. What is your Max Daily Drawdown limit?",
                      ["2% to 3%. Once hit, the platform is closed.", "Around 5%, then I try to be careful.",
                       "I have no limit, I trade until I make it back."])
        q10 = st.radio("10. A trade hits your SL, but immediately reverses into your original direction. Reaction?",
                       ["It's part of the game. I wait for the next setup.",
                        "I re-enter immediately out of frustration.",
                        "I blame market manipulation and increase leverage."])

        st.markdown("---")
        st.subheader("Part 3: Emotional Control & FOMO")
        q11 = st.radio("11. You are on a 5-trade losing streak due to bad slippage. Your mindset?",
                       ["Take a break, review the journal, wait for better market conditions.",
                        "Slightly angry, but I keep trading my edge.",
                        "Furious. I double my size on the next trade to recover."])
        q12 = st.radio("12. You see a massive 15% momentum candle print WITHOUT you. FOMO strikes.",
                       ["I do nothing. Chasing is how you die.", "I wait for a minor pullback and jump in.",
                        "I market-buy immediately before it goes higher."])
        q13 = st.radio("13. You hit your weekly profit target on Tuesday morning.",
                       ["I stop trading for the week or cut my risk to 0.25%.", "I keep trading normally.",
                        "I increase my risk because I'm playing with 'house money'."])
        q14 = st.radio("14. Your portfolio is currently in a 12% drawdown.",
                       ["Normal business. My strategy's max historical DD is 15%.",
                        "I am losing sleep and constantly checking my phone.",
                        "I abandon my strategy and look for a new indicator on YouTube."])
        q15 = st.radio("15. Social media: You see a 19-year-old on Twitter make your yearly salary in one trade.",
                       ["I mute them. It's irrelevant to my edge.",
                        "I feel inadequate and try to force a big trade today.",
                        "I buy their course and change my strategy."])

        st.markdown("---")
        st.subheader("Part 4: Routine & Discipline")
        q16 = st.radio("16. Do you maintain a detailed trading journal?",
                       ["Yes, I log emotions, screenshots, and mistakes daily.",
                        "Only when I win or do something cool.", "No, my broker history is my journal."])
        q17 = st.radio("17. Pre-market routine:",
                       ["Review calendar (CPI, NFP), mark key levels, prepare mentally.",
                        "Just turn on the screens and look for movement.", "Trade directly from my phone in bed."])
        q18 = st.radio("18. Reaction to major news events (e.g., FED Rate Decision):",
                       ["I am flat (no positions) during the spike.",
                        "I widen my SL so I don't get stopped out by volatility.",
                        "I gamble and enter a heavy position 1 minute before."])
        q19 = st.radio("19. How does your physical health/sleep affect your trading?",
                       ["I don't trade if I slept badly or am highly stressed.", "I trade anyway, caffeine fixes it.",
                        "I use trading to escape real-life stress."])
        q20 = st.radio("20. Define a 'successful' trading day:",
                       ["Following my rules perfectly, regardless of PnL.", "Making money.",
                        "Making a lot of money and posting it."])
        q21 = st.radio("21. True or False: 'If I just had more capital, I would be a profitable trader.'",
                       ["False. Capital magnifies bad habits.", "True. I could use less leverage.",
                        "True. I just need one big account to make it."])

    # Save responses
    st.session_state.responses.update({
        'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'q5': q5, 'q6': q6, 'q7': q7, 'q8': q8, 'q9': q9, 'q10': q10,
        'q11': q11, 'q12': q12, 'q13': q13, 'q14': q14, 'q15': q15, 'q16': q16, 'q17': q17, 'q18': q18, 'q19': q19,
        'q20': q20, 'q21': q21
    })

    col_b1, col_b2 = st.columns([1, 5])
    with col_b1:
        st.button("⬅️ Back", on_click=prev_step)
    with col_b2:
        st.button("Run Year-Long Simulation ➔", on_click=next_step)

# ==============================================================================
# STEP 5: RESULTS & SIMULATION DASHBOARD
# ==============================================================================
elif st.session_state.step == 4 + 1:
    st.title("📊 Step 4: Post-Simulation Quantitative Dashboard")

    resp = st.session_state.responses

    # --- SCORING ALGORITHM ---
    score = 100
    # Punish bad habits severely
    if "Accept the -5%" not in resp['q6']: score -= 15
    if "Yes, position sizing" not in resp['q7']: score -= 20
    if "predefined structural point" not in resp['q8']: score -= 10
    if "I have no limit" in resp['q9']: score -= 25
    if "re-enter immediately" in resp['q10'] or "blame market" in resp['q10']: score -= 15
    if "double my size" in resp['q11']: score -= 30
    if "market-buy immediately" in resp['q12']: score -= 15
    if "abandon my strategy" in resp['q14']: score -= 20
    if "No, my broker history" in resp['q16']: score -= 10
    if "gamble" in resp['q18']: score -= 20
    if "False. Capital magnifies" not in resp['q21']: score -= 15

    score = max(0, score)

    # --- SIMULATION ENGINE (1 Year, 3 Regimes) ---
    np.random.seed(42)  # For reproducibility in UI, but logic is dynamic
    days_in_year = 252

    capital = resp['initial_capital']
    monthly_injection = resp['monthly_injection']
    tax_rate = resp['tax_rate'] / 100
    tax_monthly = "Monthly" in resp['tax_frequency']

    portfolio_nominal = [capital]
    dates = pd.date_range(start='2023-01-01', periods=days_in_year, freq='B')

    total_tax_paid = 0.0
    monthly_profits = 0.0
    yearly_profits = 0.0

    # Trader stats
    win_prob_base = 0.55 if score > 75 else (0.45 if score > 45 else 0.35)

    for i in range(1, days_in_year):
        # Determine Regime
        if i < 84:
            regime, regime_mod = "Bull", 1.2
        elif i < 168:
            regime, regime_mod = "Chop", 0.7
        else:
            regime, regime_mod = "Bear", 0.9

        # Determine if trade happens today (approx 1 trade every 2 days)
        if random.random() < 0.5:
            # Trade happens
            risk_amount = capital * 0.01  # Strict 1% risk rule
            fee = risk_amount * 0.10  # 0.1% fee modeled on risk margin

            # Win or Loss?
            if random.random() < (win_prob_base * regime_mod):
                # WIN
                rr = random.uniform(1.5, 3.0) if score > 60 else random.uniform(0.8, 1.5)
                profit = (risk_amount * rr) - fee
                capital += profit
                monthly_profits += profit
                yearly_profits += profit
            else:
                # LOSS (Includes mechanics: slippage & gaps)
                slippage = risk_amount * random.uniform(0.05, 0.15)
                # 10% chance of a brutal weekend gap if they trade weekends/swings
                is_gap = random.random() < 0.10

                if is_gap and score < 80:  # Good traders cut early, bad traders hope
                    gap_multiplier = random.uniform(2.0, 5.0)  # Gap blows past -2% SL
                    loss = (risk_amount * gap_multiplier) + slippage + fee
                else:
                    loss = risk_amount + slippage + fee

                capital -= loss
                monthly_profits -= loss
                yearly_profits -= loss

        # End of Month Logic (Every ~21 trading days)
        if i % 21 == 0:
            capital += monthly_injection
            if tax_monthly and monthly_profits > 0:
                tax_deduction = monthly_profits * tax_rate
                capital -= tax_deduction
                total_tax_paid += tax_deduction
            monthly_profits = 0.0  # Reset month

        portfolio_nominal.append(capital)

    # End of Year Tax Logic
    if not tax_monthly and yearly_profits > 0:
        tax_deduction = yearly_profits * tax_rate
        capital -= tax_deduction
        total_tax_paid += tax_deduction
        portfolio_nominal[-1] = capital  # Update last day

    df = pd.DataFrame({'Date': dates, 'Nominal_Capital': portfolio_nominal})
    df.set_index('Date', inplace=True)

    # Calculate Real (Inflation-Adjusted) values - Assuming 3% annual inflation
    inflation_rate = 0.03
    discount_factors = (1 + inflation_rate) ** (np.arange(days_in_year) / 252)
    df['Real_Capital'] = df['Nominal_Capital'] / discount_factors

    # --- UI: TOGGLES & CHARTS ---
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        show_inflation = st.checkbox("Apply Inflation Adjustment (Real vs Nominal)", value=True)
    with col_t2:
        st.checkbox(f"Taxes Paid Deducted ({tax_rate * 100}% applied)", value=True, disabled=True)
    st.markdown('</div>', unsafe_allow_html=True)

    fig = go.Figure()

    if show_inflation:
        fig.add_trace(go.Scatter(x=df.index, y=df['Real_Capital'], mode='lines', name='Real Capital (Adjusted)',
                                 line=dict(color='#10b981', width=3)))
        fig.add_trace(go.Scatter(x=df.index, y=df['Nominal_Capital'], mode='lines', name='Nominal Capital',
                                 line=dict(color='#64748b', width=1.5, dash='dot')))
    else:
        fig.add_trace(go.Scatter(x=df.index, y=df['Nominal_Capital'], mode='lines', name='Nominal Capital',
                                 line=dict(color='#38bdf8', width=3)))

    # Add Regime Shadings
    fig.add_vrect(x0=df.index[0], x1=df.index[83], fillcolor='rgba(16, 185, 129, 0.1)', layer="below", line_width=0,
                  annotation_text="Regime: Bull", annotation_position="top left")
    fig.add_vrect(x0=df.index[84], x1=df.index[167], fillcolor='rgba(148, 163, 184, 0.1)', layer="below", line_width=0,
                  annotation_text="Regime: Chop/Range", annotation_position="top left")
    fig.add_vrect(x0=df.index[168], x1=df.index[-1], fillcolor='rgba(239, 68, 68, 0.1)', layer="below", line_width=0,
                  annotation_text="Regime: Bear", annotation_position="top left")

    fig.update_layout(title="1-Year Capital Trajectory (Simulating Fees, Gaps & Slippage)", template="plotly_dark",
                      height=450)
    st.plotly_chart(fig, use_container_width=True)

    # --- STATISTICS ---
    net_profit = capital - resp['initial_capital'] - (monthly_injection * 12)
    cum_max = df['Nominal_Capital'].cummax()
    max_dd = ((df['Nominal_Capital'] - cum_max) / cum_max).min() * 100

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Final Capital", f"${capital:,.2f}")
    col_m2.metric("Net Profit (from trading)", f"${net_profit:,.2f}")
    col_m3.metric("Taxes Paid to Gov", f"${total_tax_paid:,.2f}")
    col_m4.metric("Max Drawdown", f"{max_dd:.2f}%")

    # --- AI REPORT ---
    st.markdown('<div class="ai-card">', unsafe_allow_html=True)
    st.subheader("🤖 AI Diagnostic & Reality Check")

    st.warning(
        "**CRITICAL WARNING:** The simulation above represents the **BEST POSSIBLE CONDITIONS** assuming you execute your chosen strategy perfectly according to your psychological profile. Human emotion usually worsens these metrics by 30% to 50% in live trading.")

    if score >= 80:
        st.success(
            f"**Analysis:** Your Behavioral Score is {score}/100. You possess the strict risk management required to survive institutional gaps and slippage. By adhering strictly to 1% risk and cutting losses logically rather than emotionally, you survive the 'Chop' and 'Bear' regimes. Continue your journaling routine.")
    elif score >= 50:
        st.warning(
            f"**Analysis:** Your Behavioral Score is {score}/100. While your strategy is sound, your answers indicate severe vulnerability to FOMO and revenge trading. Notice the sharp drops in the 'Bear' regime? Those are simulated weekend gaps hitting your account because you refuse to accept the initial -2% Stop Loss. Fix your discipline before trading live.")
    else:
        st.error(
            f"**Analysis:** Your Behavioral Score is {score}/100. **High Risk of Complete Financial Ruin.** Your approach to risk management (averaging down, ignoring SLs, heavy leverage) guarantees account destruction. The simulated chart shows you bleeding capital heavily due to slippage and emotional trading. DO NOT trade with real money.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.button("🔄 Restart Simulator", on_click=lambda: st.session_state.update(step=1))