import { useCallback, useEffect, useRef, useState } from 'react';
import { analyzeGrid, listPuzzles, loadPuzzle } from './api.js';

const EMPTY_ANALYSIS = null;
const sameUnit = (row, column, selected) => selected && (
  row === selected[0] || column === selected[1]
  || (Math.floor(row / 3) === Math.floor(selected[0] / 3)
    && Math.floor(column / 3) === Math.floor(selected[1] / 3))
);

export function SudokuBoard({ puzzle, analysis, selected, onSelect, onEnter, onErase }) {
  const cellRefs = useRef([]);
  const candidates = analysis?.candidates ?? [];
  const conflicts = new Set((analysis?.rule_conflicts ?? []).map((item) => item.cell.join(',')));
  const mismatches = new Set((analysis?.solution_mismatch_cells ?? []).map((cell) => cell.join(',')));

  useEffect(() => {
    const handleKey = (event) => {
      if (!selected) return;
      const [row, column] = selected;
      if (/^[1-9]$/.test(event.key)) {
        event.preventDefault();
        onEnter(row, column, Number(event.key));
      } else if (event.key === 'Backspace' || event.key === 'Delete' || event.key === '0') {
        event.preventDefault();
        onErase(row, column);
      } else {
        const shifts = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
        if (shifts[event.key]) {
          event.preventDefault();
          const [dr, dc] = shifts[event.key];
          const nextRow = Math.max(0, Math.min(8, row + dr));
          const nextColumn = Math.max(0, Math.min(8, column + dc));
          onSelect(nextRow, nextColumn);
          cellRefs.current[nextRow * 9 + nextColumn]?.focus();
        }
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [selected, onEnter, onErase, onSelect]);

  return <div className="sudoku-grid" role="grid" aria-label={`${puzzle?.name ?? 'Sudoku'} board`}>
    {Array.from({ length: 81 }, (_, index) => {
      const row = Math.floor(index / 9);
      const column = index % 9;
      const value = puzzle.grid[row][column];
      const isSelected = selected?.[0] === row && selected?.[1] === column;
      const cellClass = [
        'sudoku-cell',
        puzzle.initial_grid[row][column] ? 'given' : value ? 'entered' : '',
        sameUnit(row, column, selected) ? 'related' : '',
        isSelected ? 'selected' : '',
        conflicts.has(`${row},${column}`) ? 'conflict' : '',
        mismatches.has(`${row},${column}`) ? 'mismatch' : '',
        (column + 1) % 3 === 0 && column < 8 ? 'box-right' : '',
        (row + 1) % 3 === 0 && row < 8 ? 'box-bottom' : '',
      ].filter(Boolean).join(' ');
      const marks = value === 0 ? (candidates[row]?.[column] ?? []) : [];
      return <button
        key={index}
        ref={(element) => { cellRefs.current[index] = element; }}
        className={cellClass}
        type="button"
        role="gridcell"
        aria-label={`Row ${row + 1}, column ${column + 1}${value ? `, ${value}` : ', empty'}${puzzle.initial_grid[row][column] ? ', given' : ''}`}
        aria-selected={isSelected}
        onClick={() => { onSelect(row, column); cellRefs.current[index]?.focus(); }}
      >
        {value !== 0
          ? <span className="cell-value">{value}</span>
          : <span className="candidate-marks" aria-label={`Candidates ${marks.join(', ')}`}>
            {Array.from({ length: 9 }, (_, digit) => <span key={digit}>{marks.includes(digit + 1) ? digit + 1 : ''}</span>)}
          </span>}
      </button>;
    })}
  </div>;
}

export default function App() {
  const [puzzles, setPuzzles] = useState([]);
  const [game, setGame] = useState(null);
  const [analysis, setAnalysis] = useState(EMPTY_ANALYSIS);
  const [selected, setSelected] = useState([0, 0]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const requestId = useRef(0);

  const refreshAnalysis = useCallback(async (puzzleId, grid) => {
    const currentRequest = ++requestId.current;
    setAnalysis(null);
    setLoading(true);
    try {
      const result = await analyzeGrid(puzzleId, grid);
      if (requestId.current === currentRequest) setAnalysis(result);
    } catch (requestError) {
      if (requestId.current === currentRequest) setError(requestError.message);
    } finally {
      if (requestId.current === currentRequest) setLoading(false);
    }
  }, []);

  const selectPuzzle = useCallback(async (id) => {
    const currentRequest = ++requestId.current;
    setLoading(true);
    setError('');
    setAnalysis(null);
    try {
      const loaded = await loadPuzzle(id);
      if (requestId.current !== currentRequest) return;
      setGame({ ...loaded, initial_grid: loaded.grid.map((row) => [...row]) });
      setAnalysis(loaded.analysis);
      setSelected([0, 0]);
    } catch (requestError) {
      if (requestId.current === currentRequest) setError(requestError.message);
    } finally {
      if (requestId.current === currentRequest) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let alive = true;
    listPuzzles().then(async (items) => {
      if (!alive) return;
      setPuzzles(items);
      await selectPuzzle(items[0].puzzle_id);
    }).catch((requestError) => alive && setError(requestError.message));
    return () => { alive = false; requestId.current += 1; };
  }, [selectPuzzle]);

  const enterDigit = useCallback((row, column, digit) => {
    if (!game || game.initial_grid[row][column] !== 0) return;
    const grid = game.grid.map((line) => [...line]);
    grid[row][column] = digit;
    setGame((current) => ({ ...current, grid }));
    setSelected([row, column]);
    setError('');
    refreshAnalysis(game.puzzle_id, grid);
  }, [game, refreshAnalysis]);

  const eraseDigit = useCallback((row, column) => {
    if (!game || game.initial_grid[row][column] !== 0) return;
    const grid = game.grid.map((line) => [...line]);
    if (grid[row][column] === 0) return;
    grid[row][column] = 0;
    setGame((current) => ({ ...current, grid }));
    setSelected([row, column]);
    setError('');
    refreshAnalysis(game.puzzle_id, grid);
  }, [game, refreshAnalysis]);

  const currentPuzzle = puzzles.find(({ puzzle_id: id }) => id === game?.puzzle_id);

  return <main className="app-shell">
    <header className="topbar">
      <a className="brand" href="/" aria-label="Whyku home"><span className="brand-mark">W</span><span>whyku</span></a>
      <p>Understand every move.</p>
      <span className="topbar-note">A puzzle notebook</span>
    </header>

    <section className="workspace" aria-label="Sudoku workspace">
      <div className="board-column">
        <div className="puzzle-heading">
          <div><span className="eyebrow">TODAY'S PRACTICE</span><h1>Make the next move yours.</h1></div>
          <label className="puzzle-select-wrap">
            <span className="sr-only">Choose puzzle</span>
            <select aria-label="Choose puzzle" value={game?.puzzle_id ?? ''} onChange={(event) => selectPuzzle(event.target.value)} disabled={!puzzles.length}>
              {puzzles.map((puzzle) => <option key={puzzle.puzzle_id} value={puzzle.puzzle_id}>{puzzle.name} · {puzzle.level}</option>)}
            </select>
          </label>
        </div>

        {game && <SudokuBoard puzzle={game} analysis={analysis} selected={selected} onSelect={(row, column) => setSelected([row, column])} onEnter={enterDigit} onErase={eraseDigit} />}

        <div className="board-footer">
          <div className="legend"><span><i className="legend-given" /> Given</span><span><i className="legend-entered" /> Your entry</span></div>
          <span>{currentPuzzle?.techniques?.join(' · ')}</span>
        </div>
      </div>

      <aside className="side-panel">
        <div className="panel-topline"><span className="eyebrow">YOUR WORKSPACE</span><span className="pencil-icon">✳</span></div>
        <h2>Take your time.</h2>
        <p className="instruction">Solve at your own pace. Ask for a hint when you get stuck.</p>

        <div className="entry-tools">
          <p className="tool-label">NUMBER ENTRY</p>
          <div className="number-pad" aria-label="Number pad">
            {Array.from({ length: 9 }, (_, index) => <button key={index + 1} type="button" onClick={() => selected && enterDigit(selected[0], selected[1], index + 1)}>{index + 1}</button>)}
            <button className="erase-button" type="button" onClick={() => selected && eraseDigit(selected[0], selected[1])} aria-label="Erase selected cell">⌫</button>
          </div>
          <p className="keyboard-note">Or use your keyboard · arrow keys to move</p>
        </div>

        <div className="hint-action">
          <button className="hint-button" type="button" disabled>
            <span>Get Hint</span><span aria-hidden="true">↗</span>
          </button>
          {analysis?.hint_block_reason === 'solution_mismatch'
            ? <p className="status warning">Correct or erase the flagged entry before requesting a hint.</p>
            : analysis?.hint_block_reason === 'rule_conflict'
              ? <p className="status warning">Resolve the highlighted rule conflict before requesting a hint.</p>
              : loading
                ? <p className="status">Updating candidates…</p>
                : analysis?.is_solved
                  ? <p className="status success">Puzzle solved. You worked it out!</p>
                  : error
                    ? <p className="status warning">{error}</p>
                    : <p className="status">{currentPuzzle?.level ?? 'Loading puzzle'} · Hint ladder coming next.</p>}
        </div>
        <div className="notebook-note"><span>✎</span><p>Every puzzle is a chance to see a little more clearly.</p></div>
      </aside>
    </section>
    <footer className="page-footer"><span>WHYKU · LOGIC, MADE VISIBLE</span><span>Five thoughtful puzzles · One move at a time</span></footer>
  </main>;
}
