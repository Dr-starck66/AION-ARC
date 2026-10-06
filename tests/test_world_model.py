from astra_arc.world_model import *

def test_falsification():
    good=Hypothesis("plus",lambda s,a:s+a)
    hist=[Transition(0,1,1),Transition(1,2,3)]
    assert good.retrodict(hist) and good.may_plan()
    bad=Hypothesis("minus",lambda s,a:s-a)
    assert not bad.retrodict(hist)
    assert bad.confidence == Confidence.QUARANTINED

def test_search():
    p=bfs_plan(0,[1,2],lambda s,a:s+a,lambda s:s==5,max_nodes=20,max_depth=5)
    assert p is not None and sum(p)==5

def test_prediction_abort():
    calls=[]
    def step(a):
        calls.append(a); return len(calls)
    r=execute_verified([1,1,1],[1,99,3],step)
    assert r["status"]=="QUARANTINED"
    assert len(calls)==2

def test_checkpoint():
    cp=checkpoint({"x":[1,2,3]})
    assert verify_checkpoint(cp)
