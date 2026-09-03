from sample.simulation.episode import Episode


def test_submission_against_starter():
    ep = Episode(agent1=".out/submission.py", agent2="starter", debug=False)
    res = ep.run()
    assert res.status_challenger == "DONE"
    assert res.score_challenger > res.score_baseline
