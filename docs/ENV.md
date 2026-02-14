# ENV

## Explicit venv setup steps
1. `python3.11 -m venv .venv`
2. `source .venv/bin/activate`

## Install steps
3. `python -m pip install --upgrade pip`
4. `python -m pip install -r requirements.txt`

## Run steps
5. `python -m react_investment_research --query "trend for AAPL" --tickers AAPL --period 3mo`

## Test steps
6. `python -m pytest -q`

## Sanity checks
7. `python -c "import sys; print(sys.version)"`
8. `python -m react_investment_research --offline --query "macro proxies"`

## Exact command sequence (non-negotiable)
1. `python3.11 -m venv .venv`
2. `source .venv/bin/activate`
3. `python -m pip install --upgrade pip`
4. `python -m pip install -r requirements.txt`
5. `python -m pytest -q`
6. `python -m react_investment_research --offline --query "smoke test"`
