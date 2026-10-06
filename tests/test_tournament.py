import unittest
from astra_arc.tournament import Model, survivors, information_gain, choose_discriminating_probe, robust_action, tournament

class TournamentTests(unittest.TestCase):
    def test_falsification_removes_wrong_model(self):
        good=Model("good",lambda s,a:s+a)
        bad=Model("bad",lambda s,a:s)
        live=survivors([good,bad],[(0,1,1),(1,2,3)])
        self.assertEqual([m.name for m in live],["good"])
        self.assertFalse(bad.alive)

    def test_probe_maximizes_disagreement(self):
        m1=Model("m1",lambda s,a:s if a=="noop" else s+1)
        m2=Model("m2",lambda s,a:s if a=="noop" else s+2)
        for m in (m1,m2): m.alive=True
        self.assertEqual(information_gain([m1,m2],0,"noop"),0.0)
        self.assertGreater(information_gain([m1,m2],0,"probe"),0.0)
        self.assertEqual(choose_discriminating_probe(["noop","probe"],[m1,m2],0),"probe")

    def test_robust_action_uses_worst_case(self):
        m1=Model("m1",lambda s,a: 10 if a=="safe" else 100)
        m2=Model("m2",lambda s,a: 10 if a=="safe" else -5)
        out=robust_action(["safe","risky"],[m1,m2],0,score=float)
        self.assertEqual(out["action"],"safe")
        self.assertTrue(out["best"]["consensus"])

    def test_tournament_prefers_consensus_plan(self):
        m1=Model("m1",lambda s,a: s+1 if a=="go" else s)
        m2=Model("m2",lambda s,a: s+1 if a=="go" else s)
        out=tournament([m1,m2],[],["go","noop"],0,score=float)
        self.assertEqual(out["status"],"CONSENSUS_PLAN")
        self.assertEqual(out["action"],"go")

    def test_tournament_requests_probe_when_models_disagree(self):
        m1=Model("m1",lambda s,a:s if a=="noop" else 1)
        m2=Model("m2",lambda s,a:s if a=="noop" else 2)
        out=tournament([m1,m2],[],["noop","probe"],0)
        self.assertEqual(out["status"],"PROBE")
        self.assertEqual(out["action"],"probe")

if __name__=="__main__":
    unittest.main()
