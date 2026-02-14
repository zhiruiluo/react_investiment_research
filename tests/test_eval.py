from react_investment_research.eval import run_eval


def test_eval_runner():
    result = run_eval()
    assert "score" in result
    assert "max_score" in result
    assert "results" in result
    assert result["max_score"] == 16  # 4 cases * 4 points
    assert result["score"] > 0


def test_eval_results_valid_json():
    result = run_eval()
    for res in result["results"]:
        assert "query" in res
        assert "tickers" in res
        assert "summary" in res
        assert "disclaimer" in res
