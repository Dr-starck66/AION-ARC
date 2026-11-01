/**
 * ASTRA AION-ARC Ω — reproducible real-public-game evidence.
 * Two public demos only: LS20 public-mechanics-guided and TU93 visual BFS.
 * Does NOT run the 27B Kaggle challenger, test hidden games, or predict a Kaggle score.
 * Requires Node.js >= 18 with network; no secrets, no paid services, no npm packages.
 * Captures positive and negative results without rewriting official scores.
 */

const API = 'https://three.arcprize.org';
const REPO = 'https://github.com/Dr-starck66/AION-ARC';
const JSON_HEADERS = { accept: 'application/json', 'content-type': 'application/json' };
const keyRes = await fetch(`${API}/api/games/anonkey`, { headers: JSON_HEADERS });
if (!keyRes.ok) throw new Error(`ARC anonymous key HTTP ${keyRes.status}`);
const { api_key: apiKey } = await keyRes.json();
if (!apiKey) throw new Error('ARC anonymous API key missing');
const jar = new Map();
const checkResponse = (url, response, data) => {
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status} ${JSON.stringify(data).slice(0, 400)}`);
  return data;
};
async function request(path, payload = undefined) {
  const cookie = [...jar].map(([k, v]) => `${k}=${v}`).join('; ');
  const url = `${API}${path}`;
  const response = await fetch(url, {
    method: payload === undefined ? 'GET' : 'POST',
    headers: { ...JSON_HEADERS, 'X-API-Key': apiKey, ...(cookie ? { cookie } : {}) },
    body: payload === undefined ? undefined : JSON.stringify(payload),
    signal: AbortSignal.timeout(15000),
  });
  for (const setCookie of response.headers.getSetCookie()) {
    const match = setCookie.match(/^([^=;]+)=([^;]*)/);
    if (match) jar.set(match[1], match[2]);
  }
  let data;
  try { data = await response.json(); }
  catch { data = { error: 'non-JSON-response' }; }
  return checkResponse(path, response, data);
}
function center(coords) {
  const xs = coords.map(([x]) => x), ys = coords.map(([, y]) => y);
  return [Math.round((Math.min(...xs) + Math.max(...xs)) / 2),
          Math.round((Math.min(...ys) + Math.max(...ys)) / 2)];
}
/** Visual grid-graph BFS from initial pixels. No saved path or game replay. */
function planTu93(frame) {
  const pixels = frame?.[0];
  if (!pixels || pixels.length !== 64 || pixels[0].length !== 64) throw new Error('TU93 frame shape invalid');
  const player = [], target = [];
  for (let y = 0; y < 54; y++) for (let x = 0; x < 64; x++) {
    if (pixels[y][x] === 9) player.push([x, y]);
    if (pixels[y][x] === 14) target.push([x, y]);
  }
  if (!player.length || !target.length) throw new Error('TU93 player or target not detected');
  const start = center(player), goal = center(target);
  const dirs = [[0, -6, 1], [0, 6, 2], [-6, 0, 3], [6, 0, 4]];
  const padColors = new Set([0, 4, 9, 14]);
  const queue = [[...start, []]], visited = new Set([start.join(',')]);
  let expanded = 0;
  while (queue.length) {
    const [px, py, history] = queue.shift();
    expanded++;
    if (px === goal[0] && py === goal[1]) {
      if (!history.length || history.length > 45) throw new Error('TU93 unreasonable plan length');
      return { actions: history, evidence: { start, goal, expanded, visited: visited.size } };
    }
    for (const [dx, dy, action] of dirs) {
      const nx = px + dx, ny = py + dy, state = `${nx},${ny}`;
      if (nx < 3 || ny < 3 || nx >= 61 || ny >= 54 || visited.has(state)) continue;
      if (!padColors.has(pixels[ny][nx]) || pixels[py + dy / 2][px + dx / 2] !== 2) continue;
      visited.add(state);
      queue.push([nx, ny, [...history, action]]);
    }
  }
  throw new Error(`TU93 graph exhausted without a route (${expanded} nodes)`);
}
const trials = [
  {
    id: 'ls20',
    controller: 'public-mechanics-guided route, not generalization',
    // Public demo's key-rotation tile, then door. Not applicable to hidden tasks.
    getPlan: () => ({ actions: [1,1,1,1,3,3,3,2,1,4,4,4,1,1,1], evidence: { source: 'public LS20 mechanics guide' } }),
  },
  { id: 'tu93', controller: 'pixel-observation graph BFS, no stored action route', getPlan: planTu93 },
];
const card = await request('/api/scorecard/open', {
  tags: ['astra-aion-arc', 'public-two-game-proof', 'non-kaggle'], source_url: REPO,
});
if (!card.card_id) throw new Error('No ARC scorecard ID received');
const outputs = [];
for (const trial of trials) {
  const metadata = await request(`/api/games/${trial.id}`);
  const gameId = metadata.game_id;
  const initial = await request('/api/cmd/RESET', { card_id: card.card_id, game_id: trial.id });
  if (!initial.guid || !initial.frame || !Array.isArray(initial.available_actions)) {
    throw new Error(`${trial.id}: real initial frame missing`);
  }
  const { actions, evidence } = trial.getPlan(initial.frame);
  let current = initial, executed = 0, accepted = 0;
  const transitions = [];
  for (const action of actions) {
    if (!current.available_actions.includes(action)) throw new Error(`${trial.id}: illegal action ${action}`);
    const before = current.levels_completed;
    current = await request(`/api/cmd/ACTION${action}`, {
      card_id: card.card_id, game_id: gameId, guid: initial.guid,
    });
    executed++;
    accepted++;
    transitions.push({ action, levels_before: before, levels_after: current.levels_completed,
      state_after: current.state });
    if (current.levels_completed > 0 || current.state === 'WIN' || current.state === 'GAME_OVER') break;
  }
  const intermediate = await request(`/api/scorecard/${card.card_id}`);
  const env = intermediate.environments?.find(x => x.id === gameId);
  if (!env || env.actions !== accepted) throw new Error(`${trial.id}: scorecard action count mismatch`);
  const positive = (env.score ?? 0) > 0 && env.levels_completed > 0;
  outputs.push({ game_id: gameId, controller: trial.controller, controller_evidence: evidence,
    planned_actions: actions.length, actions_accepted: accepted, levels_completed: env.levels_completed,
    score_game: env.score, per_level_scores: env.runs?.[0]?.level_scores,
    per_level_actions: env.runs?.[0]?.level_actions, transport: 'official ARC API, all commands HTTP 200',
    status: positive ? 'PASS-positive-real-game' : 'FAIL-no-positive-game-score', transitions });
}
const observed = await request(`/api/scorecard/${card.card_id}`);
if (observed.environments?.length !== 2) throw new Error('Scorecard should include exactly two public games');
console.log(JSON.stringify({ schema: 'astra-arc3-real-public/1', at_utc: new Date().toISOString(),
  project: 'AION-ARC', source_url: REPO, scorecard_id: card.card_id,
  public_games: 2, total_actions: observed.total_actions, scorecard_mean_of_two: observed.score,
  status: outputs.every(x => x.status.startsWith('PASS')) ? 'PASS-two-public-levels' : 'PARTIAL',
  limits: ['Not a Kaggle submission', 'Not tested on private/hidden tasks',
    'LS20 route informed by published public-game rules',
    'TU93 BFS uses a known public pixel schema, not a general world model',
    'A two-game score is not a 25-game/55-game aggregate'],
  outputs }, null, 2));