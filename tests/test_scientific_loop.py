from astra_arc.scientific_loop import Candidate, Evidence, TransitionLedger, falsify, information_gain, choose_probe

def test_falsify_kills_wrong_model():
    good=Candidate("good",lambda s,a:s+a)
    bad=Candidate("bad",lambda s,a:s)
    alive=falsify([good,bad],[(0,1,1),(1,2,3)])
    assert [c.name for c in alive]==["good"]
    assert bad.contradictions==[0,1]

def test_information_gain_prefers_disagreement():
    a=Candidate("a",lambda s,x: s if x=="boring" else s+1)
    b=Candidate("b",lambda s,x: s if x=="boring" else s+2)
    ranked=information_gain(["boring","probe"],[a,b],0)
    assert ranked[0][0]=="probe" and ranked[0][1] > ranked[1][1]
    assert choose_probe(["boring","probe"],[a,b],0)=="probe"

def test_risk_can_reject_dangerous_probe():
    a=Candidate("a",lambda s,x: x)
    b=Candidate("b",lambda s,x: x if x=="safe" else "other")
    assert choose_probe(["safe","risky"],[a,b],0,risk=lambda x:2.0 if x=="risky" else 0.0)=="safe"

def test_ledger_requires_no_counterexample():
    l=TransitionLedger()
    l.add(Evidence(0,"R",1,1,"INFORMATIONAL","move"))
    l.add(Evidence(1,"R",2,2,"POSITIVE","move"))
    assert l.promotable("move")
    l.add(Evidence(2,"R",3,9,"NEGATIVE","move"))
    assert not l.promotable("move")
    assert len(l.counterexamples("move"))==1
