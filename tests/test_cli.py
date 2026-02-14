import json
from unittest.mock import patch

from react_investment_research.cli import main


def test_cli_offline_mode(capsys):
    with patch("sys.argv", ["prog", "--offline", "--query", "test", "--tickers", "AAPL"]):
        main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["query"] == "test"
        assert output["tickers"] == ["AAPL"]
        assert output["disclaimer"] == "Research summary, not financial advice."


def test_cli_with_llm_flag(capsys):
    with patch("sys.argv", ["prog", "--use-llm", "--query", "test", "--offline"]):
        main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "query" in output
        assert output["tickers"] == ["SPY", "QQQ", "TLT", "GLD"]


def test_cli_period_validation(capsys):
    with patch("sys.argv", ["prog", "--offline", "--query", "test", "--tickers", "AAPL", "--period", "invalid"]):
        main()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "Invalid period" in output["limitations"][0]
