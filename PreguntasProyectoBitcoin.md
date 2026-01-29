# Questions to Refine the Bitcoin Mining Farm Business Model

To develop a complete and accurate model, I need more details about your specific requirements. Below is a list of questions organized by categories. Please answer those you deem relevant to adjust the project.

## Project Scope and Scale
1. What approximate size of mining farm are you considering? (e.g., total hashrate in TH/s, number of miners, initial investment in USD)
R: 3 megawatts
2. Where do you plan to locate the farm? (country, region) This affects energy costs, regulations, and climate for cooling.
R: Argentina. Neuquen.
3. What is the time horizon for the model? (e.g., 1 year, 3 years, 5 years)
R: 6 months to be operative and 8 years running.
4. Do you want to include future expansion or just analysis of a fixed setup?
R: Yes, 2nd stage to 10 MW, 3rd stage to 40 MW


## Technical Variables and Hardware
5. What specific type of hardware are you considering? (e.g., ASIC like Antminer S19, or generic)
R: The hardware must be variable and I must be able to change it at will. Therefore, every option must be considered.
6. Do you want to model hardware depreciation and periodic replacements?
R: Yes
7. Will you include variable energy efficiency (e.g., by ambient temperature)?
R: Yes but must be very simple.
8. What data source will you use for network difficulty and global hashrate? (e.g., APIs like Blockchain.com, CoinMarketCap)
R: You can suggest what you consider more useful

## Economic and Financial Variables
9. What financial metrics are a priority? (ROI, NPV, IRR, payback, cash flow projections)
R: ROI, Cashflow projections and COGR
10. How will you handle BTC price volatility? (static scenarios, Monte Carlo, historical data)
R: Historical data + Hipotetical scenarios
11. Will you include financing costs (loans, interest)?
R: Yes as a variable
12. What discount rate will you use for NPV? (based on WACC or specific)
R: Based on WACC
13. Will you consider taxes on profits or cryptocurrencies?
R: Add it as a % variable that could be 0

## Scenarios and Analysis
14. What specific scenarios do you want to model besides base, optimal, and pessimistic? (e.g., halving, regulations, competition)
R: Historical (Based on passed data), optimal, break even and pessimistic
15. Do you want automated sensitivity analysis for multiple variables?
R: Yes
16. Will you include risks such as hardware failures, cyberattacks, or regulatory changes?
R: Yes but as a % variable. For example, during the year we consider X% downtime due to hardware falures. No cyberatacks nor regulatory changes.

## Technical Implementation
17. What programming language do you prefer for the program? (Python recommended for ease in data analysis)
R: Python is fine
18. What type of interface do you want? (CLI, web dashboard, Excel export)
R: Web dashboard with possibility of excel export
19. Do you need real-time API integration for updated data?
R: Yes, very important.
20. Do you want visualizations (projection charts, dashboards)?
R: Yes
21. Should the program be executable locally or in the cloud?
R: For the moment locally is fine. It will be migrated to the cloud in the future

## Data and Sources
22. Do you have access to specific historical data? (BTC prices, difficulty)
R: Yes, data is publically available.
23. What APIs or data sources do you know and want to use? (e.g., CoinGecko, Glassnode)
R: I don't have the APIs but sources are several: Whattomine, TradingView, Binance, Coingecko, hashrate.no, Braiins - https://learn.braiins.com/en/profitability-calculator.
24. Do you want the model to include local cost data (energy, hardware)?
R: Yes, those should be variables that user can change.

## Experience and Preferences
25. What is your level of experience in BTC mining or financial modeling?
R: Expert in mining. Junior in financial modeling 
26. Is there a budget for development or tools?
R: No
27. Do you want the model to be modular for future expansions?
R: Yes
28. Are there any legal or ethical restrictions to consider?
R: No.

## Other
29. Do you want to include comparison with other investments (e.g., vs. ETFs, stocks)?
R: Yes but is not a priority
30. Do you need detailed technical documentation or just the functional model?
R: Yes, all must be documented.


Answer these questions so I can adjust the model and program to your exact needs. If there's anything else you want to add, let me know!