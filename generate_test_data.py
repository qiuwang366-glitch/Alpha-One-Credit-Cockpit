"""
Generate enhanced test data for Alpha-One Credit Cockpit
Creates multiple bonds per issuer with varying durations for Nelson-Siegel testing
"""

import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)  # For reproducibility

# Define issuers with their characteristics
ISSUERS = {
    # MBS
    "FNMA": {"sector": "MBS", "subsector": "Agency", "name": "Fannie Mae", "base_oas": 45, "base_ftp": 4.20},
    "GNMA": {"sector": "MBS", "subsector": "Agency", "name": "Ginnie Mae", "base_oas": 40, "base_ftp": 4.20},
    "FHLMC": {"sector": "MBS", "subsector": "Agency", "name": "Freddie Mac", "base_oas": 42, "base_ftp": 4.15},
    "JPMMT": {"sector": "MBS", "subsector": "Non-Agency", "name": "JP Morgan Mortgage Trust", "base_oas": 125, "base_ftp": 4.50},
    "CSFB": {"sector": "MBS", "subsector": "Non-Agency", "name": "Credit Suisse First Boston", "base_oas": 140, "base_ftp": 4.50},

    # Technology Corps
    "AAPL": {"sector": "Corps", "subsector": "Technology", "name": "Apple Inc", "base_oas": 50, "base_ftp": 4.25},
    "MSFT": {"sector": "Corps", "subsector": "Technology", "name": "Microsoft Corp", "base_oas": 48, "base_ftp": 4.10},
    "GOOG": {"sector": "Corps", "subsector": "Technology", "name": "Alphabet Inc", "base_oas": 60, "base_ftp": 4.15},
    "NVDA": {"sector": "Corps", "subsector": "Technology", "name": "NVIDIA Corp", "base_oas": 75, "base_ftp": 4.20},
    "AMZN": {"sector": "Corps", "subsector": "Technology", "name": "Amazon.com Inc", "base_oas": 55, "base_ftp": 4.18},
    "META": {"sector": "Corps", "subsector": "Technology", "name": "Meta Platforms Inc", "base_oas": 68, "base_ftp": 4.22},

    # Healthcare Corps
    "JNJ": {"sector": "Corps", "subsector": "Healthcare", "name": "Johnson & Johnson", "base_oas": 40, "base_ftp": 4.00},
    "PFE": {"sector": "Corps", "subsector": "Healthcare", "name": "Pfizer Inc", "base_oas": 65, "base_ftp": 4.15},
    "UNH": {"sector": "Corps", "subsector": "Healthcare", "name": "UnitedHealth Group", "base_oas": 50, "base_ftp": 4.10},
    "ABBV": {"sector": "Corps", "subsector": "Healthcare", "name": "AbbVie Inc", "base_oas": 72, "base_ftp": 4.20},
    "TMO": {"sector": "Corps", "subsector": "Healthcare", "name": "Thermo Fisher Scientific", "base_oas": 58, "base_ftp": 4.12},

    # Consumer Corps
    "WMT": {"sector": "Corps", "subsector": "Consumer", "name": "Walmart Inc", "base_oas": 38, "base_ftp": 4.05},
    "PG": {"sector": "Corps", "subsector": "Consumer", "name": "Procter & Gamble", "base_oas": 32, "base_ftp": 4.00},
    "KO": {"sector": "Corps", "subsector": "Consumer", "name": "Coca-Cola Co", "base_oas": 45, "base_ftp": 4.08},
    "PEP": {"sector": "Corps", "subsector": "Consumer", "name": "PepsiCo Inc", "base_oas": 42, "base_ftp": 4.06},
    "MCD": {"sector": "Corps", "subsector": "Consumer", "name": "McDonald's Corp", "base_oas": 48, "base_ftp": 4.10},

    # Energy Corps
    "XOM": {"sector": "Corps", "subsector": "Energy", "name": "Exxon Mobil", "base_oas": 70, "base_ftp": 4.18},
    "CVX": {"sector": "Corps", "subsector": "Energy", "name": "Chevron Corp", "base_oas": 55, "base_ftp": 4.12},
    "COP": {"sector": "Corps", "subsector": "Energy", "name": "ConocoPhillips", "base_oas": 85, "base_ftp": 4.25},
    "SLB": {"sector": "Corps", "subsector": "Energy", "name": "Schlumberger Ltd", "base_oas": 95, "base_ftp": 4.30},

    # Industrial Corps
    "CAT": {"sector": "Corps", "subsector": "Industrial", "name": "Caterpillar Inc", "base_oas": 52, "base_ftp": 4.15},
    "BA": {"sector": "Corps", "subsector": "Industrial", "name": "Boeing Co", "base_oas": 140, "base_ftp": 4.35},
    "HON": {"sector": "Corps", "subsector": "Industrial", "name": "Honeywell International", "base_oas": 58, "base_ftp": 4.18},
    "GE": {"sector": "Corps", "subsector": "Industrial", "name": "General Electric Co", "base_oas": 78, "base_ftp": 4.25},

    # US Banks
    "JPM": {"sector": "Fins", "subsector": "Banks-US", "name": "JPMorgan Chase", "base_oas": 60, "base_ftp": 4.28},
    "BAC": {"sector": "Fins", "subsector": "Banks-US", "name": "Bank of America", "base_oas": 58, "base_ftp": 4.22},
    "WFC": {"sector": "Fins", "subsector": "Banks-US", "name": "Wells Fargo", "base_oas": 75, "base_ftp": 4.30},
    "C": {"sector": "Fins", "subsector": "Banks-US", "name": "Citigroup Inc", "base_oas": 92, "base_ftp": 4.35},
    "GS": {"sector": "Fins", "subsector": "Banks-US", "name": "Goldman Sachs Group", "base_oas": 85, "base_ftp": 4.32},
    "MS": {"sector": "Fins", "subsector": "Banks-US", "name": "Morgan Stanley", "base_oas": 80, "base_ftp": 4.30},

    # Foreign Banks
    "HSBC": {"sector": "Fins", "subsector": "Banks-Foreign", "name": "HSBC Holdings", "base_oas": 85, "base_ftp": 4.28},
    "BCS": {"sector": "Fins", "subsector": "Banks-Foreign", "name": "Barclays PLC", "base_oas": 90, "base_ftp": 4.32},
    "DB": {"sector": "Fins", "subsector": "Banks-Foreign", "name": "Deutsche Bank AG", "base_oas": 125, "base_ftp": 4.45},
    "RY": {"sector": "Fins", "subsector": "Banks-Foreign", "name": "Royal Bank of Canada", "base_oas": 55, "base_ftp": 4.20},

    # Insurance
    "AIG": {"sector": "Fins", "subsector": "Insurance", "name": "American International Group", "base_oas": 95, "base_ftp": 4.35},
    "MET": {"sector": "Fins", "subsector": "Insurance", "name": "MetLife Inc", "base_oas": 88, "base_ftp": 4.30},
    "PRU": {"sector": "Fins", "subsector": "Insurance", "name": "Prudential Financial", "base_oas": 92, "base_ftp": 4.32},

    # Rates
    "UST": {"sector": "Rates", "subsector": "Treasury", "name": "US Treasury", "base_oas": 0, "base_ftp": 4.00},
    "TIPS": {"sector": "Rates", "subsector": "TIPS", "name": "Treasury Inflation-Protected", "base_oas": -15, "base_ftp": 4.00},

    # EM
    "BRAZIL": {"sector": "EM", "subsector": "Sovereign", "name": "Brazil Sovereign", "base_oas": 220, "base_ftp": 4.80},
    "MEXICO": {"sector": "EM", "subsector": "Sovereign", "name": "Mexico Sovereign", "base_oas": 180, "base_ftp": 4.65},
    "PETRO": {"sector": "EM", "subsector": "Corporate", "name": "Petrobras", "base_oas": 250, "base_ftp": 4.90},

    # ABS
    "FORD": {"sector": "ABS", "subsector": "Auto", "name": "Ford Credit Auto Trust", "base_oas": 85, "base_ftp": 4.35},
    "ALLY": {"sector": "ABS", "subsector": "Auto", "name": "Ally Auto Receivables Trust", "base_oas": 75, "base_ftp": 4.30},
}

# Duration ranges for different maturities
DURATIONS = {
    "2Y": (1.5, 2.2),
    "3Y": (2.5, 3.2),
    "5Y": (4.0, 5.2),
    "7Y": (5.8, 6.8),
    "10Y": (7.5, 9.5),
    "15Y": (10.0, 12.5),
    "20Y": (12.0, 15.0),
    "30Y": (14.0, 18.0),
}

MATURITY_YEARS = {
    "2Y": 2026,
    "3Y": 2027,
    "5Y": 2029,
    "7Y": 2031,
    "10Y": 2034,
    "15Y": 2039,
    "20Y": 2044,
    "30Y": 2054,
}

ACCOUNTING_TYPES = ["AFS", "HTM", "Fair Value"]

def generate_bonds():
    """Generate synthetic bond data."""
    bonds = []

    for ticker, info in ISSUERS.items():
        sector = info["sector"]
        subsector = info["subsector"]
        name = info["name"]
        base_oas = info["base_oas"]
        base_ftp = info["base_ftp"]

        # Generate 6-8 bonds per issuer with different maturities
        num_bonds = np.random.randint(6, 9)
        maturities = np.random.choice(list(DURATIONS.keys()), size=num_bonds, replace=True)

        for i, maturity in enumerate(maturities):
            # Duration
            dur_min, dur_max = DURATIONS[maturity]
            duration = np.random.uniform(dur_min, dur_max)

            # OAS varies around base with some noise
            oas = base_oas + np.random.normal(0, 10)
            oas = max(oas, -50)  # Floor at -50bp

            # FTP
            ftp = base_ftp / 100

            # Calculate yield using a simple term structure
            # Base rate increases with duration
            base_rate = 0.035 + 0.0015 * duration  # 3.5% + 15bp per year of duration

            # Add OAS spread
            spread = oas / 10000  # Convert bps to decimal

            # Add some random noise
            noise = np.random.normal(0, 0.001)

            yield_rate = base_rate + spread + noise

            # Notional - larger for shorter duration, high quality
            if duration < 3:
                notional = np.random.uniform(15, 50) * 1e6
            elif duration < 7:
                notional = np.random.uniform(10, 35) * 1e6
            else:
                notional = np.random.uniform(5, 25) * 1e6

            # Accounting type - mostly AFS, some HTM, few Fair Value
            accounting_weights = [0.65, 0.25, 0.10]
            accounting = np.random.choice(ACCOUNTING_TYPES, p=accounting_weights)

            # Create bond entry
            year = MATURITY_YEARS[maturity]
            coupon = yield_rate * 100 * np.random.uniform(0.85, 1.05)  # Coupon near but not exactly at yield

            bond = {
                "分类1": sector,
                "分类2": subsector,
                "TICKER": f"{ticker} {coupon:.2f} {str(year)[-2:]}",
                "债券名称": f"{name} {coupon:.2f}% {year}",
                "AccSection": accounting,
                "Nominal（USD）": f"{notional:,.0f}",
                "Duration": f"{duration:.2f}",
                "EffectiveYield": f"{yield_rate*100:.2f}%",
                "OAS": f"{oas:.0f}",
                "FTP Rate": f"{ftp*100:.2f}%",
            }

            bonds.append(bond)

    return bonds

def main():
    """Generate and save test data."""
    print("Generating enhanced test data...")

    bonds = generate_bonds()
    df = pd.DataFrame(bonds)

    # Sort by sector and ticker
    df = df.sort_values(["分类1", "TICKER"])

    # Save to CSV
    output_path = Path(__file__).parent / "data" / "portfolio.csv"
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"✅ Generated {len(df)} bonds")
    print(f"✅ Saved to: {output_path}")

    # Print summary statistics
    print("\n📊 Summary by Sector:")
    print(df.groupby("分类1").size())

    print("\n📊 Unique Issuers:")
    print(f"Total: {len(ISSUERS)}")

    print("\n📊 Duration Distribution:")
    print(df["Duration"].astype(float).describe())

if __name__ == "__main__":
    main()
