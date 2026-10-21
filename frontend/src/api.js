async function request(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export const listPuzzles = () => request('/api/puzzles');
export const loadPuzzle = (id) => request(`/api/puzzles/${id}`);
export const analyzeGrid = (puzzleId, grid) => request('/api/analysis', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ puzzle_id: puzzleId, grid }),
});

export const getHint = (puzzleId, grid) => request('/api/hints', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ puzzle_id: puzzleId, grid }),
});

export const getExplanation = (puzzleId, grid) => request('/api/hints/explanation', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ puzzle_id: puzzleId, grid }),
});
