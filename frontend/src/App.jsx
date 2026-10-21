import { useCallback, useEffect, useRef, useState } from 'react';
import { analyzeGrid, getExplanation, getHint, listPuzzles, loadPuzzle } from './api.js';

const EMPTY_ANALYSIS = null;
const sameUnit = (row, column, selected) => selected && (
  row === selected[0] || column === selected[1]
  || (Math.floor(row / 3) === Math.floor(selected[0] / 3)
    && Math.floor(column / 3) === Math.floor(selected[1] / 3))
);

const cellId = (cell) => cell.join(',');
const gridKey = (grid) => grid.map((row) => row.join('')).join('');
const unitName = (unit) => `${unit.kind === 'box' ? 'Box' : unit.kind[0].toUpperCase() + unit.kind.slice(1)} ${unit.index + 1}`;

function evidenceAreaCells(deduction) {
  if (!deduction) return new Set();
  const cells = new Set();
  if (deduction.technique === 'hidden_single') {
    const { kind, index } = deduction.unit;
    for (let row = 0; row < 9; row += 1) {
      for (let column = 0; column < 9; column += 1) {
        const matches = kind === 'row' ? row === index
          : kind === 'column' ? column === index
            : Math.floor(row / 3) * 3 + Math.floor(column / 3) === index;
        if (matches) cells.add(`${row},${column}`);
      }
    }
  } else {
    const [targetRow, targetColumn] = deduction.target;
    for (let row = 0; row < 9; row += 1) {
      for (let column = 0; column < 9; column += 1) {
        if (row === targetRow || column === targetColumn
          || (Math.floor(row / 3) === Math.floor(targetRow / 3)
            && Math.floor(column / 3) === Math.floor(targetColumn / 3))) {
          cells.add(`${row},${column}`);
        }
      }
    }
  }
  return cells;
}

function areaDescription(deduction) {
  return deduction.technique === 'hidden_single'
    ? unitName(deduction.unit)
    : 'Relevant row · column · box';
}

function techniqueDescription(deduction) {
  return deduction.technique === 'naked_single'
    ? 'Naked single'
    : `Hidden single in ${unitName(deduction.unit).toLowerCase()}`;
}

function hintNudge(deduction) {
  return deduction.technique === 'naked_single'
    ? 'There is a cell with only one possible digit.'
    : 'A digit has only one possible position in a unit.';
}

function formatCell([row, column]) {
  return `R${row + 1}C${column + 1}`;
}

function EvidenceSummary({ deduction }) {
  if (deduction.technique === 'naked_single') {
    return <div className="evidence-summary">
      <p>One candidate remains in the highlighted cell. These existing values block the alternatives:</p>
      <ul>{deduction.blockers.map((blocker) => <li key={`${cellId(blocker.cell)}-${blocker.digit}`}>
        <strong>{blocker.digit}</strong> at {formatCell(blocker.cell)} · {blocker.shared_units.join(' + ')}
      </li>)}</ul>
    </div>;
  }
  return <div className="evidence-summary">
    <p>The only eligible position is {formatCell(deduction.target)} in {unitName(deduction.unit)}. Other empty positions are blocked:</p>
    <ul>{deduction.excluded_positions.map((position) => <li key={cellId(position.cell)}>
      <strong>{formatCell(position.cell)}</strong> — {position.blockers.map((blocker) => `${blocker.digit} at ${formatCell(blocker.cell)} (${blocker.shared_units.join(' + ')})`).join(', ')}
    </li>)}</ul>
  </div>;
}

export function SudokuBoard({ puzzle, analysis, selected, onSelect, onEnter, onErase, hint }) {
  const cellRefs = useRef([]);
  const candidates = analysis?.candidates ?? [];
  const conflicts = new Set((analysis?.rule_conflicts ?? []).map((item) => item.cell.join(',')));
  const mismatches = new Set((analysis?.solution_mismatch_cells ?? []).map((cell) => cell.join(',')));
  const deduction = hint?.deduction;
  const hintLevel = hint?.level ?? 0;
  const areaCells = evidenceAreaCells(deduction);
  const targetId = deduction ? cellId(deduction.target) : null;
  const blockerIds = new Set((deduction?.blockers ?? []).map((blocker) => cellId(blocker.cell)));
  const eliminatedDigits = new Set((deduction?.blockers ?? []).map((blocker) => blocker.digit));
  const excludedIds = new Set((deduction?.excluded_positions ?? []).map((item) => cellId(item.cell)));
  const eligibleIds = new Set((deduction?.eligible_cells ?? []).map(cellId));

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
      const id = `${row},${column}`;
      const isTarget = id === targetId;
      const isArea = areaCells.has(id);
      const isEvidence = hintLevel >= 3;
      const maskedAreaCandidates = hintLevel === 1 || (hintLevel === 2 && isArea);
      const cellClass = [
        'sudoku-cell',
        puzzle.initial_grid[row][column] ? 'given' : value ? 'entered' : '',
        sameUnit(row, column, selected) ? 'related' : '',
        isSelected ? 'selected' : '',
        conflicts.has(`${row},${column}`) ? 'conflict' : '',
        mismatches.has(`${row},${column}`) ? 'mismatch' : '',
        hintLevel >= 2 && isArea ? 'hint-area' : '',
        isEvidence && isTarget ? 'hint-target' : '',
        isEvidence && blockerIds.has(id) ? 'hint-blocker' : '',
        isEvidence && eligibleIds.has(id) ? 'hint-candidate-position' : '',
        isEvidence && excludedIds.has(id) ? 'hint-excluded-position' : '',
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
          : hintLevel === 5 && isTarget
            ? <span className="hint-reveal-digit" aria-label={`Revealed digit ${deduction.digit}`}>{deduction.digit}</span>
            : isEvidence && deduction.technique === 'hidden_single' && (eligibleIds.has(id) || excludedIds.has(id))
              ? <span className={`hidden-candidate-marker ${eligibleIds.has(id) ? 'eligible' : 'excluded'}`} aria-label={eligibleIds.has(id) ? 'Only possible position for masked digit' : 'Position ruled out for masked digit'}>•</span>
              : <span className="candidate-marks" aria-label={maskedAreaCandidates ? 'Candidates temporarily masked' : `Candidates ${marks.join(', ')}`}>
                {Array.from({ length: 9 }, (_, digit) => {
                  const mark = marks.includes(digit + 1);
                  const maskNakedTarget = hintLevel >= 3 && deduction?.technique === 'naked_single' && isTarget;
                  const survivorHere = maskNakedTarget && digit + 1 === deduction.digit;
                  const eliminateHere = maskNakedTarget && eliminatedDigits.has(digit + 1);
                  return <span key={digit} className={eliminateHere ? 'eliminated-candidate' : survivorHere ? 'masked-candidate' : ''}>
                    {maskedAreaCandidates ? '' : eliminateHere ? digit + 1 : survivorHere ? '•' : mark ? digit + 1 : ''}
                  </span>;
                })}
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
  const hintRequestId = useRef(0);
  const [hint, setHint] = useState(null);
  const [preparedHint, setPreparedHint] = useState(null);

  const refreshAnalysis = useCallback(async (puzzleId, grid) => {
    const currentRequest = ++requestId.current;
    setAnalysis(null);
    setPreparedHint(null);
    setLoading(true);
    try {
      const result = await analyzeGrid(puzzleId, grid);
      if (requestId.current !== currentRequest) return;
      setAnalysis(result);
      if (result.hints_enabled) {
        const nextHint = await getHint(puzzleId, grid);
        if (requestId.current === currentRequest && nextHint.status === 'available' && nextHint.deduction) {
          setPreparedHint({ puzzleId, gridKey: gridKey(grid), ...nextHint });
        }
      }
    } catch (requestError) {
      if (requestId.current === currentRequest) setError(requestError.message);
    } finally {
      if (requestId.current === currentRequest) setLoading(false);
    }
  }, []);

  const selectPuzzle = useCallback(async (id) => {
    const currentRequest = ++requestId.current;
    hintRequestId.current += 1;
    setHint(null);
    setPreparedHint(null);
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
    hintRequestId.current += 1;
    setHint(null);
    setPreparedHint(null);
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
    hintRequestId.current += 1;
    setHint(null);
    setPreparedHint(null);
    grid[row][column] = 0;
    setGame((current) => ({ ...current, grid }));
    setSelected([row, column]);
    setError('');
    refreshAnalysis(game.puzzle_id, grid);
  }, [game, refreshAnalysis]);

  const requestHint = useCallback(async () => {
    if (!game || !analysis?.hints_enabled || loading) return;
    const currentGridKey = gridKey(game.grid);
    if (preparedHint?.puzzleId === game.puzzle_id && preparedHint.gridKey === currentGridKey) {
      setHint({ deduction: preparedHint.deduction, level: 1, explanation: null, source: null, loadingExplanation: false });
      return;
    }
    const currentRequest = ++hintRequestId.current;
    setHint(null);
    setError('');
    try {
      const result = await getHint(game.puzzle_id, game.grid);
      if (hintRequestId.current !== currentRequest) return;
      setAnalysis(result.analysis);
      if (result.status === 'available' && result.deduction) {
        setHint({ deduction: result.deduction, level: 1, explanation: null, source: null, loadingExplanation: false });
      } else if (result.message) {
        setError(result.message);
      }
    } catch (requestError) {
      if (hintRequestId.current === currentRequest) setError(requestError.message);
    }
  }, [game, analysis, loading, preparedHint]);

  const advanceHint = useCallback(async () => {
    if (!hint) return;
    if (hint.level < 3) {
      setHint((current) => ({ ...current, level: current.level + 1 }));
      return;
    }
    if (hint.level === 3) {
      const currentRequest = hintRequestId.current;
      setHint((current) => ({ ...current, loadingExplanation: true }));
      try {
        const result = await getExplanation(game.puzzle_id, game.grid);
        if (hintRequestId.current !== currentRequest) return;
        if (result.status === 'available' && result.explanation) {
          setHint((current) => ({
            ...current,
            level: 4,
            explanation: result.explanation,
            source: result.source,
            loadingExplanation: false,
          }));
        } else {
          setHint((current) => ({ ...current, loadingExplanation: false }));
          if (result.message) setError(result.message);
        }
      } catch (requestError) {
        if (hintRequestId.current === currentRequest) {
          setHint((current) => ({ ...current, loadingExplanation: false }));
          setError(requestError.message);
        }
      }
      return;
    }
    if (hint.level === 4) setHint((current) => ({ ...current, level: 5 }));
  }, [hint, game]);

  const dismissHint = useCallback(() => {
    hintRequestId.current += 1;
    setHint(null);
  }, []);

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

        {game && <SudokuBoard puzzle={game} analysis={analysis} selected={selected} onSelect={(row, column) => setSelected([row, column])} onEnter={enterDigit} onErase={eraseDigit} hint={hint} />}

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
          <button className="hint-button" type="button" onClick={requestHint} disabled={!analysis?.hints_enabled || loading || Boolean(hint)}>
            <span>Get Hint</span><span aria-hidden="true">↗</span>
          </button>
          {hint
            ? <div className="hint-ladder" aria-live="polite">
                <div className="ladder-heading"><span className="eyebrow">HINT · {hint.level} OF 5</span><button type="button" className="text-button" onClick={dismissHint}>Dismiss</button></div>
                <div className="ladder-progress" aria-label={`Hint level ${hint.level} of 5`}><span style={{ width: `${hint.level * 20}%` }} /></div>
                {hint.level === 1 && <><h3>A gentle nudge</h3><p>{hintNudge(hint.deduction)}</p></>}
                {hint.level === 2 && <><h3>Look in this area</h3><p className="hint-area-name">{areaDescription(hint.deduction)}</p><p>The board shading marks the relevant unit or units.</p></>}
                {hint.level === 3 && <><h3>{techniqueDescription(hint.deduction)}</h3><p>Compare the highlighted candidates and evidence cells. The digit remains hidden.</p></>}
                {hint.level === 4 && <><h3>Why this move works</h3><span className={`source-badge ${hint.source}`}>{hint.source === 'gemini' ? 'Gemini · approved clauses' : 'Offline template'}</span><p className="explanation-text">{hint.explanation}</p><EvidenceSummary deduction={hint.deduction} /></>}
                {hint.level === 3 && error && <p className="status warning">{error} You can try the explanation again.</p>}
                {hint.level === 5 && <><h3>Reveal</h3><p>Cell R{hint.deduction.target[0] + 1}C{hint.deduction.target[1] + 1} can take <strong>{hint.deduction.digit}</strong>.</p><button className="apply-hint-button" onClick={() => enterDigit(...hint.deduction.target, hint.deduction.digit)}>Enter {hint.deduction.digit} in the grid</button></>}
                <div className="ladder-actions">
                  {hint.level > 1 && <button type="button" className="secondary-button" onClick={() => setHint((current) => ({ ...current, level: current.level - 1 }))} disabled={hint.loadingExplanation}>Back</button>}
                  {hint.level < 5 && <button type="button" className="next-button" onClick={advanceHint} disabled={hint.loadingExplanation}>{hint.loadingExplanation ? 'Checking explanation…' : hint.level === 4 ? 'Reveal the digit' : 'Next hint'} <span aria-hidden="true">→</span></button>}
                  <button type="button" className="text-button return-button" onClick={dismissHint}>Back to puzzle</button>
                </div>
              </div>
            : analysis?.hint_block_reason === 'solution_mismatch'
            ? <p className="status warning">Correct or erase the flagged entry before requesting a hint.</p>
            : analysis?.hint_block_reason === 'rule_conflict'
              ? <p className="status warning">Resolve the highlighted rule conflict before requesting a hint.</p>
              : loading
                ? <p className="status">Updating candidates…</p>
                : analysis?.is_solved
                  ? <p className="status success">Puzzle solved. You worked it out!</p>
                  : error
                    ? <p className="status warning">{error}</p>
                    : analysis?.hint_block_reason === 'no_supported_single'
                      ? <p className="status">No naked or hidden single is available right now. This puzzle may need a technique Whyku does not support yet.</p>
                      : analysis?.hint_block_reason === 'completed'
                        ? <p className="status success">Puzzle solved. You worked it out!</p>
                        : <p className="status">{currentPuzzle?.level ?? 'Loading puzzle'} · You're doing great.</p>}
        </div>
        <div className="notebook-note"><span>✎</span><p>Every puzzle is a chance to see a little more clearly.</p></div>
      </aside>
    </section>
    <footer className="page-footer"><span>WHYKU · LOGIC, MADE VISIBLE</span><span>Five thoughtful puzzles · One move at a time</span></footer>
  </main>;
}
