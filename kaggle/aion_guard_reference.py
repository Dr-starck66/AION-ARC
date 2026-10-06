AION_GUARD_VERSION = "2.1"

def _aion_bbox(boundary):
    pts = list(boundary or [])
    if not pts:
        return None
    rows = [int(p[0]) for p in pts]
    cols = [int(p[1]) for p in pts]
    return (min(rows), min(cols), max(rows), max(cols))

def aion_probable_hud(node, shape):
    rows, cols = tuple(shape or (0, 0))
    bbox = _aion_bbox(node.get("boundary", []))
    if not bbox or rows <= 0 or cols <= 0:
        return False
    r0, c0, r1, c1 = bbox
    height = r1 - r0 + 1
    width = c1 - c0 + 1
    touches_edge = r0 == 0 or c0 == 0 or r1 == rows - 1 or c1 == cols - 1
    long_edge_strip = (width >= max(8, int(cols * 0.75)) and height <= 3) or (height >= max(8, int(rows * 0.75)) and width <= 3)
    return bool(touches_edge and long_edge_strip)

def aion_frame_signature(frame):
    if frame is None:
        return ()
    seg = getattr(frame, "segmentation", {}) or {}
    shape = getattr(frame, "shape", (0, 0))
    nodes = []
    for node in seg.get("nodes", []):
        if aion_probable_hud(node, shape):
            continue
        bbox = _aion_bbox(node.get("boundary", []))
        dims = None if bbox is None else (bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1)
        nodes.append((
            str(node.get("color", "")),
            str(node.get("hash", "")),
            int(node.get("pixels", 0) or 0),
            dims,
            len(node.get("children", []) or []),
        ))
    return tuple(sorted(nodes))

def aion_evidence(transitions, limit=12):
    rows = []
    for tr in list(transitions or [])[-max(1, int(limit)):]:
        before = aion_frame_signature(getattr(tr, "before_frame", None))
        after = aion_frame_signature(getattr(tr, "after_frame", None))
        result = getattr(tr, "result", {}) or {}
        rows.append({
            "action": str(getattr(tr, "action", "")),
            "gameplay_changed": before != after,
            "board_changed": bool(result.get("board_changed", False)),
            "level_completed": bool(result.get("level_completed", False)),
            "game_over": bool(result.get("game_over", False)),
            "reward": result.get("reward"),
        })
    return rows

def aion_plan_audit(plan, valid_actions, transitions=None, last_action_result=None):
    valid = {str(x).upper() for x in (valid_actions or [])}
    warnings = []
    plan = list(plan or [])
    for i, item in enumerate(plan):
        spec = {"action": item} if isinstance(item, str) else dict(item or {})
        action_name = str(spec.get("action", "")).upper()
        if not action_name:
            warnings.append(f"step {i+1}: missing action")
            continue
        if valid and action_name not in valid:
            warnings.append(f"step {i+1}: {action_name} not currently valid")
        if action_name == "RESET" and "ACTION7" in valid:
            warnings.append(f"step {i+1}: RESET while ACTION7 is available")
    ev = aion_evidence(transitions or [], limit=3)
    if plan and ev:
        first = plan[0] if isinstance(plan[0], str) else str((plan[0] or {}).get("action", ""))
        last = ev[-1]
        if str(first).upper() == str(last.get("action", "")).upper() and not last.get("gameplay_changed") and not bool(last.get("level_completed")):
            warnings.append("first action repeats the latest gameplay-inert probe; justify with force_probe")
    return warnings

def aion_expectation_mismatches(spec, action_result, frame):
    spec = dict(spec or {})
    result = dict(action_result or {})
    mismatches = []
    if "expect_change" in spec:
        actual = bool(result.get("board_changed", False))
        if actual != bool(spec.get("expect_change")):
            mismatches.append(f"expect_change={bool(spec.get('expect_change'))} actual={actual}")
    if "expect_level_completed" in spec:
        actual = bool(result.get("level_completed", False))
        if actual != bool(spec.get("expect_level_completed")):
            mismatches.append(f"expect_level_completed={bool(spec.get('expect_level_completed'))} actual={actual}")
    if "expect_reward_min" in spec:
        reward = result.get("reward")
        try:
            reward_value = float(reward)
            if reward_value < float(spec.get("expect_reward_min")):
                mismatches.append(f"reward {reward_value} < {float(spec.get('expect_reward_min'))}")
        except (TypeError, ValueError):
            mismatches.append("reward unavailable for expect_reward_min")
    required = spec.get("expect_valid_actions_contains")
    if required:
        actual_valid = {str(x).upper() for x in result.get("valid_actions", [])}
        missing = [str(x).upper() for x in required if str(x).upper() not in actual_valid]
        if missing:
            mismatches.append("missing valid actions: " + ",".join(missing))
    if "expect_level" in spec and frame is not None:
        actual_level = int(getattr(frame, "level", -1))
        if actual_level != int(spec.get("expect_level")):
            mismatches.append(f"expect_level={int(spec.get('expect_level'))} actual={actual_level}")
    return mismatches


def aion_prediction_match(expected, observed):
    """Recursive partial matcher for falsifiable predictions."""
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            return False
        return all(k in observed and aion_prediction_match(v, observed[k]) for k, v in expected.items())
    if isinstance(expected, (list, tuple)):
        if not isinstance(observed, (list, tuple)) or len(expected) != len(observed):
            return False
        return all(aion_prediction_match(a, b) for a, b in zip(expected, observed))
    return expected == observed

def aion_information_gain(actions_or_predictions, hypotheses=None, state=None, risk=None):
    """Rank probes by hypothesis disagreement; supports precomputed outcomes or executable hypotheses."""
    import math
    if hypotheses is None and isinstance(actions_or_predictions, dict):
        predictions = dict(actions_or_predictions)
    else:
        predictions = {}
        for action_name in list(actions_or_predictions or []):
            vals = []
            for hypothesis in list(hypotheses or []):
                try:
                    vals.append(hypothesis.predict(state, action_name))
                except Exception as exc:
                    vals.append(("ERROR", type(exc).__name__))
            predictions[str(action_name)] = vals

    ranked = []
    for action_name, outcomes in predictions.items():
        vals = list(outcomes or [])
        counts = {}
        for value in vals:
            key = repr(value)
            counts[key] = counts.get(key, 0) + 1
        total = float(len(vals) or 1)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log(p, 2)
        penalty = float(risk(action_name)) if callable(risk) else 0.0
        ranked.append({"action": str(action_name), "information_gain": entropy, "risk": penalty, "utility": entropy - penalty})
    ranked.sort(key=lambda row: (-row["utility"], -row["information_gain"], row["action"]))
    if hypotheses is None and isinstance(actions_or_predictions, dict):
        return [(row["action"], row["information_gain"]) for row in ranked]
    return ranked

def aion_choose_probe(actions, hypotheses, state, risk=None):
    ranked = aion_information_gain(actions, hypotheses, state, risk=risk)
    return ranked[0]["action"] if ranked else None

def aion_state_graph(transitions, limit=80):
    """ASTRA SEMANTIC FLOW Ω: compact state/action graph with conflicts and loops."""
    rows = list(transitions or [])[-max(1, int(limit)):]
    edges = {}
    states = set()
    terminals = []
    for i, tr in enumerate(rows):
        before = aion_frame_signature(getattr(tr, "before_frame", None))
        after = aion_frame_signature(getattr(tr, "after_frame", None))
        states.add(before)
        states.add(after)
        action_name = str(getattr(tr, "action", ""))
        edges.setdefault((before, action_name), set()).add(after)
        result = getattr(tr, "result", {}) or {}
        if any(bool(result.get(k)) for k in ("level_completed", "game_over", "run_complete", "done")):
            terminals.append((i, action_name))
    conflicts = [
        {"action": action, "outcomes": len(outcomes)}
        for (_before, action), outcomes in edges.items()
        if len(outcomes) > 1
    ]
    self_loops = sum(1 for (before, _action), outcomes in edges.items() if before in outcomes)
    return {
        "states": len(states),
        "edges": len(edges),
        "conflicts": conflicts,
        "self_loops": self_loops,
        "terminals": terminals,
    }


def aion_compact_memory(transitions, limit=120):
    """ASTRA NO-REPEAT + continual memory: retain causal evidence, contradictions and progress, not raw chatter."""
    rows = list(transitions or [])[-max(1, int(limit)):]
    memory = {
        "confirmed_effects": {},
        "inert_actions": {},
        "contradictions": [],
        "progress_actions": [],
        "terminal_actions": [],
    }
    outcomes = {}
    for idx, tr in enumerate(rows):
        action_name = str(getattr(tr, "action", "")).upper()
        before = aion_frame_signature(getattr(tr, "before_frame", None))
        after = aion_frame_signature(getattr(tr, "after_frame", None))
        result = dict(getattr(tr, "result", {}) or {})
        changed = before != after
        key = (repr(before), action_name)
        outcomes.setdefault(key, set()).add(repr(after))
        if changed:
            memory["confirmed_effects"][action_name] = memory["confirmed_effects"].get(action_name, 0) + 1
        else:
            memory["inert_actions"][action_name] = memory["inert_actions"].get(action_name, 0) + 1
        if result.get("level_completed") or result.get("reward"):
            memory["progress_actions"].append((idx, action_name))
        if result.get("game_over") or result.get("run_complete") or result.get("done"):
            memory["terminal_actions"].append((idx, action_name))
    for (_state, action_name), next_states in outcomes.items():
        if len(next_states) > 1:
            memory["contradictions"].append({"action": action_name, "distinct_outcomes": len(next_states)})
    memory["confirmed_effects"] = dict(sorted(memory["confirmed_effects"].items(), key=lambda kv: (-kv[1], kv[0])))
    memory["inert_actions"] = dict(sorted(memory["inert_actions"].items(), key=lambda kv: (-kv[1], kv[0])))
    return memory

def aion_ablation_profile(profile="balanced"):
    """Fail-open experiment profiles: keep the Duck baseline measurable against ASTRA additions."""
    profiles = {
        "duck_baseline": {
            "prediction_gate": False, "rollback": False, "no_repeat": False,
            "compact_memory": False, "world_model": False,
        },
        "guarded": {
            "prediction_gate": True, "rollback": True, "no_repeat": True,
            "compact_memory": False, "world_model": False,
        },
        "memory": {
            "prediction_gate": True, "rollback": True, "no_repeat": True,
            "compact_memory": True, "world_model": False,
        },
        "balanced": {
            "prediction_gate": True, "rollback": True, "no_repeat": True,
            "compact_memory": True, "world_model": True,
        },
    }
    name = str(profile or "balanced").strip().lower()
    if name not in profiles:
        raise ValueError("unknown AION ablation profile: " + name)
    return dict(profiles[name])


def aion_action_efficiency(transitions, recent_window=12):
    """ASTRA ACTION-EFFICIENCY Ω: diagnose waste that directly hurts ARC-AGI-3 score."""
    rows = list(transitions or [])
    evidence = aion_evidence(rows, limit=max(1, len(rows)))
    total = len(evidence)
    inert = sum(1 for row in evidence if not row.get("gameplay_changed") and not row.get("level_completed"))
    progress = sum(1 for row in evidence if row.get("level_completed") or row.get("reward"))
    recent = evidence[-max(1, int(recent_window)):]
    recent_inert = sum(1 for row in recent if not row.get("gameplay_changed") and not row.get("level_completed"))
    repeated = 0
    for prev, cur in zip(recent, recent[1:]):
        if cur.get("action") == prev.get("action") and not cur.get("gameplay_changed"):
            repeated += 1
    return {
        "actions": total,
        "progress_events": progress,
        "inert_actions": inert,
        "inert_rate": (inert / total) if total else 0.0,
        "recent_inert_rate": (recent_inert / len(recent)) if recent else 0.0,
        "repeated_inert_pairs": repeated,
        "needs_model_escalation": bool(len(recent) >= 8 and recent_inert / len(recent) >= 0.5),
    }


def aion_probe_budget(transitions, max_inert=3, window=8):
    """Fail closed when exploration is burning actions without semantic information."""
    ev = aion_evidence(transitions or [], limit=max(1, int(window)))
    inert = [r for r in ev if not r.get("gameplay_changed") and not r.get("level_completed")]
    return {
        "remaining": max(0, int(max_inert) - len(inert)),
        "exhausted": len(inert) >= int(max_inert),
        "observed_inert": len(inert),
        "window": len(ev),
    }


def aion_shortest_plan(start, is_goal, expand, max_nodes=5000, max_depth=64):
    """Shortest-path planner: once a model is verified, stop probing and minimize live actions."""
    from collections import deque
    q = deque([(start, [])])
    seen = {repr(start)}
    expanded = 0
    while q and expanded < int(max_nodes):
        state, plan = q.popleft()
        expanded += 1
        if is_goal(state):
            return {"status": "FOUND", "plan": plan, "actions": len(plan), "expanded": expanded}
        if len(plan) >= int(max_depth):
            continue
        for action_name, nxt in expand(state):
            key = repr(nxt)
            if key in seen:
                continue
            seen.add(key)
            q.append((nxt, plan + [action_name]))
    return {"status": "BOUNDED" if q else "EXHAUSTED", "plan": None, "actions": None, "expanded": expanded}


def aion_efficiency_gate(candidate_action, transitions, hypotheses=None, state=None, risk=None):
    """Choose whether a live probe earns its action cost."""
    budget = aion_probe_budget(transitions)
    efficiency = aion_action_efficiency(transitions)
    if hypotheses:
        ranked = aion_information_gain([candidate_action], hypotheses, state, risk=risk)
        utility = ranked[0]["utility"] if ranked else 0.0
    else:
        utility = None
    blocked = bool(budget["exhausted"] and (utility is None or utility <= 0.0))
    return {
        "allowed": not blocked,
        "reason": "probe budget exhausted; build/verify/search world model" if blocked else "allowed",
        "probe_budget": budget,
        "efficiency": efficiency,
        "information_utility": utility,
    }
