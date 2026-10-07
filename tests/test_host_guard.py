from astra_arc.host_guard import StepExpectation, execute_plan_prefix

def _obs(x): return x["state"]
def _legal(x): return x.get("legal", [])
def _level(x): return x.get("level")
def _terminal(x): return x.get("terminal", False)

def test_host_guard_passes_verified_prefix():
    stream=iter([
        {"state":1,"legal":["A"],"level":1},
        {"state":2,"legal":["A"],"level":1},
    ])
    out=execute_plan_prefix(
        [StepExpectation("A",1,{"A"}),StepExpectation("A",2,{"A"})],
        lambda _a:next(stream),_obs,_legal,_level,_terminal)
    assert out.status=="PASS" and out.executed==2

def test_host_guard_stops_prediction_mismatch():
    calls=[]
    def step(a):
        calls.append(a); return {"state":99,"legal":["A"],"level":1}
    out=execute_plan_prefix([StepExpectation("A",1),StepExpectation("A",2)],step,_obs,_legal,_level,_terminal)
    assert out.status=="QUARANTINED" and out.reason=="predicted_state_mismatch" and len(calls)==1

def test_host_guard_stops_legal_action_drift():
    stream=iter([{"state":1,"legal":["B"],"level":1}])
    out=execute_plan_prefix([StepExpectation("A",1,{"A"})],lambda _a:next(stream),_obs,_legal,_level,_terminal)
    assert out.reason=="legal_actions_changed"

def test_host_guard_stops_cycle_before_remaining_plan():
    calls=[]
    vals=iter([
        {"state":1,"legal":["A"],"level":1},
        {"state":1,"legal":["A"],"level":1},
        {"state":2,"legal":["A"],"level":1},
    ])
    def step(a): calls.append(a); return next(vals)
    out=execute_plan_prefix([StepExpectation("A"),StepExpectation("A"),StepExpectation("A")],step,_obs,_legal,_level,_terminal)
    assert out.reason=="unexpected_cycle" and len(calls)==2


def test_host_guard_stops_unexpected_level_change():
    stream=iter([
        {"state":1,"legal":["A"],"level":1},
        {"state":2,"legal":["A"],"level":2},
    ])
    out=execute_plan_prefix(
        [StepExpectation("A"),StepExpectation("A")],
        lambda _a:next(stream),_obs,_legal,_level,_terminal)
    assert out.reason=="unexpected_level_change" and out.executed==2

def test_host_guard_stops_unexpected_terminal():
    stream=iter([{"state":1,"legal":["A"],"level":1,"terminal":True}])
    out=execute_plan_prefix(
        [StepExpectation("A")],
        lambda _a:next(stream),_obs,_legal,_level,_terminal)
    assert out.reason=="unexpected_terminal"
