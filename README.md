# Balance Sheet Analyst
## Components
- Scraper: written in bash (for naive parallelization of scraping tasks) and python(using BeautifulSoup) to scrape financial documents of any company listed on MoneyControl (which includes all currently listed NSE and BSE companies and many previously listed companies). Latency of 1 second. Links for all companies on MoneyControl are pre-indexed and the documents are fetched only once upon account creation
- Data Augmentation Scripts: to clean up the scraped data and format it into easily processed csv files, and extract useful information (using fuzzy search with fuzzywuzzy) from the Balance Sheets, PL statements, and Cash Flow statements. This also runs once upon account creation and creates the data blocks used for the plots. The data used for the context provided to the LLM is also processed by these scripts. Latency of less than 100ms.
- Website backend: written using Flask with jwt-extensions to provide the capability of using salted JWT tokens for facilitating login. Access tokens for maintaining login status are generated differently and expire in 24 hours, preventing account takeover through token stealing. Numpy and pandas are used for data handling, sqlite3 for the database. Firecrawl is used for providing realtime web-query capabilities to the LLM. Requests package for connecting to APIs and communicating with servers
- Website frontend: written using React and NodeJS for dynamic page generation, Recharts for plotting vectorized, resizable graphs. CSS for the styling. Axios with React utilities for displaying CSV files(and allowing their download as well)

## Architecture & Design Considerations
- Login and Registration: since users are associated with companies, the registration page required entering a companyID (or company name), and only upon approval by an admin would the account be allowed to initialize and allow login and access to all the financial data of the company
- Real-time web query: Firecrawl API with an interrupt is used to allow the LLM to perform function-calling to the real-time scraper to provide better insights
- LLM: Deepseek is used because of its very high context window (128K tokens locally, 32k for the paid API), chain-of-thought performance, and function-calling capabilities. An RTX 6000 Pro running Deepseek-R1-0528 quantized to 4 bits hosted on runpod costs $1.7/hour and can provide 22 tokens/second, however, since this PoC is expected to have intermittent use, it was eventually decided to use the Deepseek API instead. Reasoning model was used instead of the chat model. It has longer thinking time (10s-30s per response depending on the complexity) but produces decent insights from the analysis. Chain-of-Thought also enables it to answer complex, multi-part questions about the financials.
- Deepseek API costs: since it charges $0.28/1M input tokens (cache miss), $0.028/1M input tokens (cache hit) and $0.48/1M output tokens, this was an economical choice. In testing, the system prompt and financial data added to the context nearly always get cache hits, and across a chat with Deepseek with 10 API requests, the usage was: 54k input tokens (cache hit), 14k input tokens (cache miss), and 12k output tokens.
- System prompt and data augmentation: the LLM system prompt was designed to prime the LLM into a basic format of financial analysis, using Dupont Analysis, Altman Z-scores, Fundamental ratios, margins, and liquidity/debt burden metrics. It was also instructed to web-query related information to market expansion, headwinds, and US Fed interest rates. Further consideration was taken to give it the context of free-cash-flow driven growth versus debt-fueled growth, which combined with the financial information and fundamental ratios, prepares it for answering any questions about the health of the finances of the company and its future prospects. In order to prevent confusion, or utilize too much of the context window, the data was processed before being passed to only contain the essentials of what the LLM needed, whilst still containing all the required information
- Many of the relevant financial trends and ratios in the income statements were extracted and used for the context of the LLM to give it the best shot possible at detailed financial analysis
- Plots: in order to give a digestible bird's eye view of the company financials, the following plots were chosen
  
  -- Assets & Liabilities (stacked bar chart) to show the absolute and proportional change in current and non-current assets, and short-term and long-term liabilities
  
  -- Revenue, Gross Profit, Net Profit: to show the variation of revenue, gross margin, and Interest-Depreciation-Tax in one plot
  
  -- Margins and Returns (EBIDTA margin, EBT margin, Net margin, ROA, and ROCE): to augment the previous plot and give a clearer picture of how margins and ROI have varied, helps to better understand if cost-reduction measures are working
  
  -- Expenses Breakdown((stacked area chart): to show the proportional contribution of various costs to total expenditure, and their variation over time. Placed right next to the revenue-and-profit graph, it gives a good picture of the variation in fixed and variable costs. To make it more readable, the smaller components(totaling threshold of 5%) were combined into Others
  
  -- Cash Flow (stacked area chart): once again, chosen to show the proportional contribution of various financial activities on positive and negative cash flow, and helps notice trends(or concerns) better than the raw numbers of revenue, margin and profit
  
  -- Liquidity Ratios: Current Ratio, Quick Ratio, and Debt-to-Equity ratio are standard metrics for measuring the leverage and debt-burden of an enterprise. Combined with the realtime access to central bank interest rates (and news about increases/decreases in the rates), the user (and the LLM) can make well-informed decisions about how healthy a given debt-burden or leverage is for long-term survivability (and debt servicing/re-financing expenses)

# Showcasing the interface

<img width="845" height="676" alt="image" src="https://github.com/user-attachments/assets/ef49bc2d-9e71-4792-8ced-4964e102d119" />
<img width="514" height="616" alt="image" src="https://github.com/user-attachments/assets/9f98e7c8-2579-468f-be00-8fa2619d3360" />
<img width="511" height="494" alt="image" src="https://github.com/user-attachments/assets/240f49c7-a112-4a0f-bd3d-116668351bb4" />
<img width="1895" height="600" alt="image" src="https://github.com/user-attachments/assets/d8cb4b89-9257-4024-b1e7-5e22e7e0fa04" />
<img width="1873" height="933" alt="image" src="https://github.com/user-attachments/assets/9538f5a8-d6c8-4ea9-ae50-c763601f77e7" />
<img width="1280" height="550" alt="image" src="https://github.com/user-attachments/assets/d4c57f0b-4633-44df-876a-0bc7c422f8be" />
<img width="1869" height="924" alt="image" src="https://github.com/user-attachments/assets/0bf7a982-1c2a-4ca1-88b7-49644253c82a" />

<img width="1636" height="953" alt="image" src="https://github.com/user-attachments/assets/e8d1e154-0708-43a7-8aa6-dda1104100d4" />
<img width="1090" height="393" alt="image" src="https://github.com/user-attachments/assets/51816b66-48a2-4386-baa6-96ff58658d0f" />
<img width="1573" height="541" alt="image" src="https://github.com/user-attachments/assets/3587c5d2-8500-4028-ac45-2cbff4c1a76c" />








