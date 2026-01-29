# Bitcoin Mining Farm Business Model

## Introduction
This document describes a comprehensive business model for a Bitcoin mining farm located in Neuquén, Argentina. The model considers real industry variables, including network difficulty, Bitcoin price changes, operational costs, and various economic scenarios. The farm starts at 3 MW capacity, with planned expansions to 10 MW and 40 MW. The time horizon covers 6 months to become operational and 8 years of operation. The goal is to provide an analytical tool to evaluate the financial viability of this Bitcoin mining operation, incorporating historical data, hypothetical scenarios, and sensitivity analysis.

## Model Objectives
- Evaluate the profitability of the mining farm under different scenarios: historical (based on past data), optimal, break-even, and pessimistic.
- Calculate key financial metrics such as ROI, cash flow projections, and COGS (Cost of Goods Sold).
- Analyze sensitivity to changes in critical variables, including automated analysis for multiple factors.
- Provide projections based on historical data, hypothetical scenarios, and real-time data integration.
- Include financing costs as a variable, discount rate based on WACC, and taxes as a configurable percentage (default 0%).
- Model hardware depreciation, periodic replacements, and variable energy efficiency (simplified).
- Incorporate risks such as hardware failures (as % downtime), but exclude cyberattacks and regulatory changes.
- Support modular design for future expansions and include comparison with other investments (e.g., ETFs, stocks), though not a priority.

## Key Model Variables
### Technical Variables
- **Network Difficulty**: Automatic adjustment every 2016 blocks (approx. 2 weeks). Data sourced from APIs like Blockchain.com or CoinMarketCap.
- **Total Network Hashrate**: Measured in TH/s or EH/s. Suggested sources: Whattomine, TradingView, Binance, CoinGecko, hashrate.no, Braiins (https://learn.braiins.com/en/profitability-calculator).
- **Hardware Efficiency**: TH/s per watt, cost per TH/s. Hardware is variable and user-configurable (e.g., ASIC like Antminer S19 or generic). Includes depreciation and replacements.
- **Block Rate**: Average time between blocks (10 minutes).
- **Energy Efficiency**: Variable by ambient temperature, but simplified model.

### Economic Variables
- **Bitcoin Price (BTC)**: In USD, with historical volatility handled via historical data + hypothetical scenarios.
- **Block Reward**: Currently 3.12 BTC, with halving every 4 years.
- **Energy Costs**: $/kWh, including local Argentine rates (Neuquén-specific, user-configurable variable).
- **Hardware Costs**: Initial cost per miner, depreciation (linear over 2-3 years), and replacements. User-configurable.
- **Operational Costs**: Maintenance, cooling, personnel. Includes local costs as variables.
- **Financing Costs**: Loans and interest as a variable.
- **Taxes**: Configurable percentage on profits or cryptocurrencies (default 0%).

### External Variables
- **Inflation and Interest Rates**: For discounting cash flows, based on WACC.
- **Regulations**: Not modeled as risks, per user preference.
- **Competition**: Changes in the hardware market.
- **Risks**: Hardware failures modeled as % downtime; no cyberattacks or regulatory changes.

## Modeling Scenarios
### Historical Scenario
- Based on past data for BTC prices, difficulty, and market conditions.

### Optimal Scenario
- Sustained increase in BTC price.
- Improvements in hardware efficiency and minimal downtime.

### Break-Even Scenario
- Conditions where costs equal revenue, achieving zero profit.

### Pessimistic Scenario
- Decline in BTC price and increase in difficulty.
- Rise in energy costs and higher downtime.

### Sensitivity Scenario
- Automated impact analysis of variations in BTC price (±20%), difficulty (±10%), energy costs (±15%), hardware efficiency, and downtime (%).

## Financial Calculations
### Revenue
- Estimated daily reward: Based on own hashrate / total hashrate * block reward * 144 (blocks/day) in BTC.
- USD value: BTC reward * BTC price.
- Adjustments for downtime (% due to hardware failures).
- All revenues calculated and reported in both BTC and USD.

### Costs
- Energy: Daily consumption * $/kWh rate (local, variable) in USD.
- Hardware: Linear depreciation over useful life (2-3 years), replacements in USD.
- Operational: Fixed and variable, including local costs in USD.
- Financing: Interest on loans as variable in USD.
- Taxes: Percentage on profits in USD.
- Costs primarily in USD, with BTC equivalent where applicable.

### Metrics
- **ROI**: (Total profits / Initial investment) * 100, calculated in both USD and BTC.
- **Cash Flow Projections**: Monthly/yearly projections over 8 years in both USD and BTC.
- **COGS (Cost of Goods Sold)**: Detailed breakdown of operational costs in USD.
- **NPV**: Sum of discounted cash flows (WACC-based) in both USD and BTC.
- **Payback Period**: Time to recover initial investment in USD.
- **IRR**: Internal rate of return, applicable to USD cash flows.

## Risks and Mitigation
- **Price Volatility**: Handled via historical data and hypothetical scenarios.
- **Difficulty Increase**: Hardware upgrades and replacements.
- **Energy Costs**: Local rates as variables; potential for long-term contracts.
- **Hardware Failures**: Modeled as % downtime; mitigation through replacements.
- **No Cyberattacks or Regulatory Changes**: Excluded per user preference.

## Program Functionality
The program is a simulation tool written in Python that:
1. **Data Input**: Allows entering initial parameters (investment, location in Neuquén, hardware type/variables, expansions to 10 MW/40 MW).
2. **Real Data Retrieval**: Integrates real-time APIs for current difficulty, BTC price, etc. (e.g., Blockchain.com, CoinMarketCap, CoinGecko, Braiins).
3. **Calculations**: Runs simulations from 6 months operational to 8 years, including expansions.
4. **Output**: Generates reports with projection charts, scenarios, metrics in both USD and BTC, and Excel export.
5. **Interface**: Web dashboard for visualization, with Excel export capability.
6. **Modular Design**: Supports future expansions and additions.

### Architecture
- **Modules**: Data (historical + real-time APIs), Calculations (ROI, cash flows, COGS), Visualization (charts, dashboards).
- **Dependencies**: Libraries for APIs (requests), analysis (pandas, numpy), charts (matplotlib, plotly for web), web interface (Flask/Django).
- **Execution**: Locally executable for now, with cloud migration planned.

## Implementation and Development
- **Phase 1**: Data collection from public sources and API integration.
- **Phase 2**: Development of calculation core with variable hardware and local costs.
- **Phase 3**: Integration of scenarios, sensitivity analysis, and expansions.
- **Phase 4**: Testing and validation with historical data.
- **Phase 5**: Documentation, web dashboard, and Excel export.

## Conclusions
This model provides a tailored foundation for investment decisions in the Neuquén-based Bitcoin mining farm, considering the specified scale, expansions, and user preferences. It is recommended to update regularly with real data and adjust variables as needed. All aspects are fully documented.