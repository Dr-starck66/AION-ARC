"""AION SCIENTIFIC LOOP Ω — game-agnostic experiment selection and evidence ledger."""
from __future__ import annotations
from dataclasses import dataclass, field
from math import log2
from typing import Any, Callable, Iterable

@dataclass
class Evidence:
    before: Any
    action: Any
    predicted: Any
    observed: Any
    outcome: str
    hypothesis: str

@dataclass
class Candidate:
    name: str
    predict: Callable[[Any, Any], Any]
    alive: bool = True
    support: int = 0
    contradictions: list[int] = field(default_factory=list)

def falsify(candidates: Iterable[Candidate], history: Iterable[tuple[Any,Any,Any]],
            equal: Callable[[Any,Any],bool]=lambda a,b:a==b) -> list[Candidate]:
    hist=list(history)
    out=[]
    for c in candidates:
        c.support=0; c.contradictions.clear(); c.alive=True
        for i,(before,action,after) in enumerate(hist):
            try: got=c.predict(before,action)
            except Exception:
                c.contradictions.append(i); c.alive=False; continue
            if equal(got,after): c.support += 1
            else: c.contradictions.append(i); c.alive=False
        if c.alive: out.append(c)
    return out

def information_gain(actions: Iterable[Any], candidates: Iterable[Candidate], state: Any,
                     key: Callable[[Any],Any]=repr) -> list[tuple[Any,float,int]]:
    """Rank probes by entropy of surviving hypotheses' predicted outcomes."""
    alive=[c for c in candidates if c.alive]
    ranked=[]
    for action in actions:
        counts={}
        for c in alive:
            try: k=key(c.predict(state,action))
            except Exception: k=("EXCEPTION",c.name)
            counts[k]=counts.get(k,0)+1
        total=sum(counts.values())
        entropy=0.0
        if total:
            for n in counts.values():
                p=n/total
                entropy -= p*log2(p)
        ranked.append((action,entropy,len(counts)))
    return sorted(ranked,key=lambda row:(-row[1],-row[2],str(row[0])))

def choose_probe(actions: Iterable[Any], candidates: Iterable[Candidate], state: Any,
                 risk: Callable[[Any],float]=lambda _a:0.0) -> Any | None:
    """Maximize hypothesis separation; use risk only as a tie-break/penalty."""
    ranked=information_gain(actions,candidates,state)
    if not ranked: return None
    scored=[(gain-float(risk(action)),gain,-float(risk(action)),str(action),action)
            for action,gain,_ in ranked]
    return max(scored)[-1]

class TransitionLedger:
    def __init__(self):
        self.rows:list[Evidence]=[]
    def add(self, evidence: Evidence) -> None:
        if evidence.outcome not in {"POSITIVE","NEGATIVE","INFORMATIONAL"}:
            raise ValueError("invalid outcome")
        self.rows.append(evidence)
    def counterexamples(self, hypothesis: str) -> list[Evidence]:
        return [r for r in self.rows if r.hypothesis==hypothesis and r.predicted!=r.observed]
    def promotable(self, hypothesis: str, min_support: int=2) -> bool:
        rows=[r for r in self.rows if r.hypothesis==hypothesis]
        return len(rows)>=min_support and not self.counterexamples(hypothesis)
    def successful_skeleton(self) -> list[Any]:
        """Compress consecutive duplicate actions from positive/informational evidence."""
        actions=[]
        for r in self.rows:
            if r.outcome=="NEGATIVE": continue
            if not actions or actions[-1]!=r.action: actions.append(r.action)
        return actions
