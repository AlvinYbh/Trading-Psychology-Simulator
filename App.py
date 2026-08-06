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
        background-color: #0f172a; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #38bdf8; font-size: 1.1em;
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
    {"iso_alpha": "BRA", "country": "Brazil", "region": "South America", "tax_rate": 15.0},
    {"iso_alpha": "ZAF", "country": "South Africa", "region": "Africa", "tax_rate": 18.0}
])

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'responses' not in st.session_state:
    st.session_state.responses = {}


def next_step(): st.session_state.step += 1


def prev_step(): st.session_state.step -= 1


def run_simulation(resp, score, days_in_year=252):
    initial_capital = resp['initial_capital']
    monthly_injection = resp['monthly_injection']
    tax_rate = resp['tax_rate'] / 100
    tax_frequency = resp['tax_frequency']
    reset_strategy = resp.get('reset_strategy', 'Compound everything (Carry all profits and losses)')

    # Using 2020 as the benchmark year to showcase Bull, Bear, and Volatile regimes
    dates = pd.date_range(start='2020-01-01', periods=days_in_year, freq='B')

    total_invested = initial_capital
    current_capital = initial_capital
    base_capital = initial_capital
    month_start_capital = initial_capital
    total_taxes_paid = 0.0

    plot_dates = []
    plot_caps_nominal = []
    plot_caps_monthly_zoom = []
    month_boundaries = []

    wins = 0
    total_trades = 0
    peak_capital = current_capital
    max_loss_pct = 0.0

    win_prob_base = 0.55 if score > 75 else (0.45 if score > 45 else 0.35)

    np.random.seed(42)
    random.seed(42)

    for day in range(days_in_year):
        current_date = dates[day]

        # 3 Distinct Market Regimes Setup
        if day < 84:
            # Bull Market (Jan - April)
            regime_mod = 1.2
        elif day < 168:
            # Bear Market (May - August)
            regime_mod = 0.55
        else:
            # Volatile / Choppy Market (Sept - Dec)
            regime_mod = 0.85

        if random.random() < 0.5:
            total_trades += 1
            risk_amount = current_capital * 0.01
            fee = risk_amount * 0.10

            if random.random() < (win_prob_base * regime_mod):
                wins += 1
                rr = random.uniform(1.5, 3.0) if score > 60 else random.uniform(0.8, 1.5)
                profit = (risk_amount * rr) - fee
                current_capital += profit
            else:
                slippage = risk_amount * random.uniform(0.05, 0.15)
                is_gap = random.random() < 0.10

                if is_gap and score < 80:
                    gap_multiplier = random.uniform(2.0, 5.0)
                    loss = (risk_amount * gap_multiplier) + slippage + fee
                else:
                    loss = risk_amount + slippage + fee

                current_capital -= loss

        if current_capital > peak_capital:
            peak_capital = current_capital
        drawdown = ((peak_capital - current_capital) / peak_capital) * 100
        if drawdown > max_loss_pct:
            max_loss_pct = drawdown

        plot_dates.append(current_date)
        plot_caps_nominal.append(current_capital)

        # Monthly Zoom Logic: Resets to injected amount at the start of each month
        zoom_value = (current_capital - month_start_capital) + monthly_injection
        plot_caps_monthly_zoom.append(zoom_value)

        if (day + 1) % 21 == 0:
            monthly_profit = current_capital - base_capital

            if "Monthly" in tax_frequency:
                if monthly_profit > 0:
                    tax = monthly_profit * tax_rate
                    total_taxes_paid += tax
                    current_capital -= tax
                    monthly_profit -= tax

                if "Strict Reset" in reset_strategy:
                    if current_capital < base_capital:
                        total_invested += (base_capital - current_capital)
                    current_capital = base_capital
                elif "Withdraw profits only" in reset_strategy:
                    if current_capital > base_capital:
                        current_capital = base_capital

            current_capital += monthly_injection
            total_invested += monthly_injection
            base_capital = current_capital
            month_start_capital = current_capital

            if day != days_in_year - 1:
                plot_dates.append(current_date + pd.Timedelta(hours=12))
                plot_caps_nominal.append(np.nan)
                plot_caps_monthly_zoom.append(np.nan)
                month_boundaries.append(current_date + pd.Timedelta(hours=12))

    if "Annually" in tax_frequency:
        total_net_profit = current_capital - total_invested
        if total_net_profit > 0:
            tax = total_net_profit * tax_rate
            total_taxes_paid += tax
            current_capital -= tax

    final_after_tax = current_capital
    final_before_tax = final_after_tax + total_taxes_paid

    df = pd.DataFrame({
        'Date': plot_dates,
        'Nominal_Capital': plot_caps_nominal,
        'Monthly_Zoom': plot_caps_monthly_zoom
    })
    df.set_index('Date', inplace=True)

    inflation_rate = 0.03

    valid_dates_mask = df['Nominal_Capital'].notna()
    days_elapsed = (df.index.to_series()[valid_dates_mask] - df.index[0]).dt.days
    discount_factors = (1 + inflation_rate) ** (days_elapsed / 365.25)

    df['Real_Capital'] = np.nan
    df.loc[valid_dates_mask, 'Real_Capital'] = df.loc[valid_dates_mask, 'Nominal_Capital'] / discount_factors.values

    yearly_profits = final_before_tax - total_invested

    # Store regime transition dates for the graph
    regime_dates = [dates[0], dates[83], dates[167], dates[-1]]

    return df, month_boundaries, regime_dates, total_invested, final_before_tax, final_after_tax, total_taxes_paid, max_loss_pct, wins, total_trades, yearly_profits


st.progress(st.session_state.step / 5)

if st.session_state.step == 1:
    st.title("🛡️ Institutional Trading & Behavioral Simulator")

    st.markdown("""
    <div class="ui-card">
        <h3 style="color: #60a5fa;">Mission & Reality Check</h3>
        <p>This simulator is built to shatter the "fairy tale" illusions of trading. Financial ruin impacts not just the trader, but their entire family and community.</p>
        <p>You will face realistic market mechanics: <strong>0.1% fees, slippage, and brutal weekend market gaps that destroy Stop Losses.</strong> Before risking real capital, discover if your psychology can survive. Future Outlook: This framework is part of an ongoing independent research initiative, with upcoming upgrades integrating advanced university-level quantitative models and an integration of a trained AI.</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("I understand the risks. Proceed ➔", on_click=next_step)

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

        event = st.plotly_chart(fig_map, on_select="rerun", selection_mode="points", use_container_width=True)

    with col2:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
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

elif st.session_state.step == 3:
    st.title("💰 Step 2: Capital & Taxation Logistics")
    st.write("Set your capital injection and tax withdrawal schedule for the 1-year simulation.")

    st.markdown('<div class="ui-card">', unsafe_allow_html=True)

    st.session_state.responses['initial_capital'] = st.number_input("Starting Capital ($)", min_value=100, value=10000,
                                                                    step=1000)

    tax_freq = st.radio(
        "When do you declare and withdraw money for taxes/living?",
        ["Monthly (Taxes/withdrawals deducted at the end of each month)",
         "Annually (Compound all year, deduct taxes on year-end net profit)"]
    )
    st.session_state.responses['tax_frequency'] = tax_freq

    if "Monthly" in tax_freq:
        st.session_state.responses['reset_strategy'] = st.radio(
            "End of Month Capital Reset Strategy:",
            [
                "Strict Reset (Withdraw profits & refill losses to always start at base capital)",
                "Withdraw profits only (Start at base capital on wins, but carry losses forward)",
                "Compound everything (Carry all profits and losses, only pay taxes)"
            ]
        )
    else:
        st.session_state.responses['reset_strategy'] = "Compound everything (Carry all profits and losses)"

    st.session_state.responses['monthly_injection'] = st.number_input(
        "Monthly Capital Injection / DCA ($) added to account:", min_value=0, value=0, step=100)

    st.markdown('</div>', unsafe_allow_html=True)

    col_b1, col_b2 = st.columns([1, 5])
    with col_b1:
        st.button("⬅️ Back", on_click=prev_step)
    with col_b2:
        st.button("Proceed to Assessment ➔", on_click=next_step)

elif st.session_state.step == 4:
    st.title("🧠 Step 3: Deep Behavioral Assessment")
    st.write(
        "Be completely honest. The AI will cross-reference your answers to simulate your real win rate and drawdown.")

    with st.container():
        st.subheader("Part 1: Strategy & Logistics")
        q1 = st.selectbox("1. Primary MA Strategy:",
                          ["SMA 20/50", "SMA 50/200", "EMA 20/50", "EMA 50/200", "A moving average I created"])
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

elif st.session_state.step == 4 + 1:
    st.title("📊 Step 4: Post-Simulation Quantitative Dashboard")

    resp = st.session_state.responses

    score = 100
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

    df, month_boundaries, regime_dates, total_invested, final_before_tax, final_after_tax, total_taxes_paid, max_loss_pct, wins, total_trades, yearly_profits = run_simulation(
        resp, score)

    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        graph_view = st.selectbox(
            "Graph View Style:",
            ["Cumulative (Full Year Trajectory)", "Monthly Zoom (Resets to injection amount)"]
        )
    with col_g2:
        show_inflation = st.checkbox("Apply Inflation Adjustment (Real vs Nominal curves)", value=True)
    st.markdown('</div>', unsafe_allow_html=True)

    fig = go.Figure()

    if graph_view == "Monthly Zoom (Resets to injection amount)":
        fig.add_trace(go.Scatter(x=df.index, y=df['Monthly_Zoom'], mode='lines', name='Monthly PnL Movement',
                                 line=dict(color='#eab308', width=3), connectgaps=False))
        fig.update_layout(title="Monthly Segmented Trajectory (Volatility Zoom)")
    else:
        if show_inflation:
            fig.add_trace(go.Scatter(x=df.index, y=df['Real_Capital'], mode='lines', name='Real Capital (Adjusted)',
                                     line=dict(color='#10b981', width=3), connectgaps=False))
            fig.add_trace(go.Scatter(x=df.index, y=df['Nominal_Capital'], mode='lines', name='Nominal Capital',
                                     line=dict(color='#64748b', width=1.5, dash='dot'), connectgaps=False))
        else:
            fig.add_trace(go.Scatter(x=df.index, y=df['Nominal_Capital'], mode='lines', name='Nominal Capital',
                                     line=dict(color='#38bdf8', width=3), connectgaps=False))
        fig.update_layout(title="1-Year Cumulative Capital Trajectory (Benchmark: 2020 Market Regimes)")

    # Adding Market Regimes Visual Segmentation
    fig.add_vrect(x0=regime_dates[0], x1=regime_dates[1], fillcolor="green", opacity=0.1, layer="below", line_width=0,
                  annotation_text="Bull Market", annotation_position="top left", annotation_font_color="green")
    fig.add_vrect(x0=regime_dates[1], x1=regime_dates[2], fillcolor="red", opacity=0.1, layer="below", line_width=0,
                  annotation_text="Bear Market", annotation_position="top left", annotation_font_color="red")
    fig.add_vrect(x0=regime_dates[2], x1=regime_dates[3], fillcolor="orange", opacity=0.1, layer="below", line_width=0,
                  annotation_text="Volatile / Chop", annotation_position="top left", annotation_font_color="orange")

    for boundary in month_boundaries:
        fig.add_vline(x=boundary, line_dash="dash", line_color="rgba(255,255,255,0.15)", line_width=1)

    fig.update_xaxes(dtick="M1", tickformat="%B", tickangle=0)
    fig.update_layout(template="plotly_dark", height=450, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    capital_view = st.selectbox(
        "Select Capital Output View:",
        ["Total Invested Amount", "Final Capital (Before Taxes)", "Final Capital (After Taxes)"]
    )

    if capital_view == "Total Invested Amount":
        col1, col2, col3 = st.columns(3)
        col2.metric(capital_view, f"${total_invested:,.2f}")

    elif capital_view == "Final Capital (Before Taxes)":
        col1, col2 = st.columns(2)
        col1.metric(capital_view, f"${final_before_tax:,.2f}")
        col2.metric("Largest Loss", f"{max_loss_pct:.2f}%")

    elif capital_view == "Final Capital (After Taxes)":
        col1, col2, col3 = st.columns(3)
        col1.metric(capital_view, f"${final_after_tax:,.2f}")

        if total_taxes_paid > 0:
            col2.metric("Taxes Deducted", f"${total_taxes_paid:,.2f}")
        else:
            col2.metric("Taxes Deducted", "Not applied (No profit)")

        col3.metric("Largest Loss", f"{max_loss_pct:.2f}%")

    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    show_metrics = st.selectbox("Display Advanced Trading Metrics?", ["No", "Yes"])
    if show_metrics == "Yes":
        st.markdown("### Simplified Performance Metrics")

        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        win_eval = "Good" if win_rate > 50 else "Needs Improvement"

        avg_profit = yearly_profits / total_trades if total_trades > 0 else 0
        exp_eval = "Good" if avg_profit > 0 else "Bad"

        recovery_factor = abs(yearly_profits / (
                    abs(max_loss_pct) * total_invested / 100)) if max_loss_pct != 0 and total_invested > 0 else 0
        rec_eval = "Good" if recovery_factor > 1.5 else "Bad"

        st.markdown(f'<div class="metric-box"><b>Trade Success Rate:</b> {win_rate:.1f}% ({win_eval})</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-box"><b>Average Expected Profit per Trade:</b> ${avg_profit:.2f} ({exp_eval})</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-box"><b>Ability to Recover Losses:</b> {recovery_factor:.2f} ({rec_eval})</div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

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
