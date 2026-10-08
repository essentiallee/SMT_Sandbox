### Overview
I am making a sandbox in the style of the course simmodeltwin.net. There should be more information in the agents.md about what this specifically means, but in short it is a web-based simulation that contains some data, some rule for how to apply that data, a clock for running the rule forward in time, and some sliders that will let us change the variables and assumptions in the dataset.

### Objectives
Title: "NEA to NYC Zoning: A Speculative Simulation for Cultural Funding from 2022 to 2025"
The simulation progresses annually from federal fiscal year 2022 to 2025, covering neighborhoods across all five New York City boroughs. Beginning with the observed FY2022 funding distributino among eligible, named NYC organizational recipients under NEA assistnace listings. Organizations enter eligibility from the first recorded award and so on...Each subsequent year uses the observed net funding total for the eligible pool as its budget: 70% preserved according to the previous simulated year's funding shares, and making 30% available for redistribution. Variable for priority allocation is for neighborhoods below $25,000 in annual funding, with minimum allocation of $10,000; smaller, protected allocations must be "topped up" or reduced to zero within the budget.

### The Run
Using the Pareto frontier as the simulating model, it compares funding trajectories for year-to-year funding continuity and more neighborhood-years meeting the $25,000 threshold. So, the protected funding share starts at 70% starting value, ranging from 0 - 100% with 10% point in each step; annual neighborhood threshold starts at $25,000, with testable range in $10,000 - $50,000; and minimum positive allocation starting value at $10,000, and is fixed initially. Neighborhoods are defined across Brookly, Bronx, Manhattan, Queens, and Staten Island. All neighborhoods remain visible, although only those containing eligible organizations can receive redistributed funding for now (it will attempt to expand in the future). Zoning amendments appear according to their recorded effective dates, independently of simulated funding decisions. 
Below is the Rule in Chart:
| Fiscal Year | Effect |
|---|---|
| **2022 — Start** | Map the funding distribution across all five boroughs. Preserve historical starting point without imposing the simulated minimum grant. |
| **2023 — First redistribution** | Distribute 70% of the eligible annual budget according to simulated 2022 funding shares. Test alternative allocations of the remaining 30%, prioritizing neighborhoods below $25,000. |
| **2024 — Carry decisions forward** | Repeat using simulated 2023 funding shares and the eligible FY2024 budget. while including newly recorded eligible organizations accroding to data. |
| **2025 — Final allocation and evaluation** | Repeat using simulated 2024 shares. Compare complete trajectories for funding continuity and neighborhood coverage, identifying the non-dominated alternatives. |

### Data
The path in local server is the 'original', unprocessed data, containing needed data from 2022 to 2025
Census data '/Users/jaehyunlee/Desktop/GSAPP/02. 2026_FALL/04. Simulation/02. Data/sandbox_data/Original/census'
NEA grant data: '/Users/jaehyunlee/Desktop/GSAPP/02. 2026_FALL/04. Simulation/02. Data/sandbox_data/Original/PrimeAwardsTransactionsAndSubawards_2026-10-08_H03M17S36137785'
Zoning data: '/Users/jaehyunlee/Desktop/GSAPP/02. 2026_FALL/04. Simulation/02. Data/sandbox_data/Original/zoning related' 
geocode the locations to the organizations allocated according to the census data to the grant data, then allow defining the five boroughts using NTAs. Before designing the resulting sandbox, export the cleaned up data files in '/Users/jaehyunlee/Desktop/GSAPP/02. 2026_FALL/04. Simulation/02. Data/sandbox_data/Processed'

### The Interactive & Design
All text is written in Space Mono bold and regular. All text should range in font from 11pt to 8pt, in respect to hierarchy of information. All text is in hex code #d2d2d2.
Background is in hexcode #ffffff, and no every lineweight for design ranges in 0.5 to 0.1, in resepct to hierarchy.
The website is in 1980x1080 and devided in 3 interactive columns on the screen: left hand corner writes the title, the objective, and the rule for using the website with the sources at the bottom (the informaion can be read by scrolling down the left column, isolated from the others); in the middle is the representation of the map, can be zoomed in, and able to be dragged using center scroll of the mouse, to see the detail of the neighborhoods, and represented with colors (selected from #ff82be, #b082ff, #82fffd, #b8ff82, #616161, does not have to use them all) being able to layer with transparency ranging from 25% to 75% in respect to the year-to-year testing and variable changes; the right column has the time slider to redributable funding slider, and a resulting numbers being changed in the bottom of the sliders, and numbers being represented on the map with changes.
The bounding boxes for the left and right-side of column is white background with slight glass morph on the background, and no hard-edges.

let me know if you have any questions or anything is unclear