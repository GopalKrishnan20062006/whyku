import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App.jsx';
import { analyzeGrid, getExplanation, getHint, listPuzzles, loadPuzzle } from './api.js';

vi.mock('./api.js', () => ({
  analyzeGrid: vi.fn(),
  getExplanation: vi.fn(),
  getHint: vi.fn(),
  listPuzzles: vi.fn(),
  loadPuzzle: vi.fn(),
}));

const initialGrid = [
  [5, 3, 0, 0, 7, 0, 0, 0, 0],
  [6, 0, 0, 1, 9, 5, 0, 0, 0],
  [0, 9, 8, 0, 0, 0, 0, 6, 0],
  [8, 0, 0, 0, 6, 0, 0, 0, 3],
  [4, 0, 0, 8, 0, 3, 0, 0, 1],
  [7, 0, 0, 0, 2, 0, 0, 0, 6],
  [0, 6, 0, 0, 0, 0, 2, 8, 0],
  [0, 0, 0, 4, 1, 9, 0, 0, 5],
  [0, 0, 0, 0, 8, 0, 0, 7, 9],
];
const analysis = (overrides = {}) => ({
  candidates: initialGrid.map((row, r) => row.map((value, c) => value ? [] : (r === 0 && c === 2 ? [1, 2, 4] : [2, 3]))),
  rule_conflicts: [], solution_mismatch_cells: [], is_full: false, is_solved: false,
  hints_enabled: true, hint_block_reason: null, ...overrides,
});
const puzzleList = [{ puzzle_id: 'whyku-01', name: 'Quick Start', level: 'Gentle', techniques: ['Naked singles'] }];
const nakedDeduction = {
  technique: 'naked_single', target: [4, 4], digit: 5, unit: null,
  candidate_digits: [5], eligible_cells: [],
  blockers: [
    { cell: [0, 4], digit: 7, shared_units: ['column'] },
    { cell: [1, 4], digit: 9, shared_units: ['column'] },
    { cell: [3, 4], digit: 6, shared_units: ['column', 'box'] },
    { cell: [4, 0], digit: 4, shared_units: ['row'] },
    { cell: [4, 3], digit: 8, shared_units: ['row', 'box'] },
    { cell: [4, 5], digit: 3, shared_units: ['row', 'box'] },
    { cell: [4, 8], digit: 1, shared_units: ['row'] },
    { cell: [5, 4], digit: 2, shared_units: ['column', 'box'] },
  ],
  excluded_positions: [],
};
const hiddenDeduction = {
  technique: 'hidden_single', target: [0, 2], digit: 4,
  unit: { kind: 'row', index: 0 }, candidate_digits: [1, 2, 4],
  eligible_cells: [[0, 2]], blockers: [],
  excluded_positions: [{ cell: [0, 3], blockers: [{ cell: [0, 1], digit: 3, shared_units: ['row'] }] }],
};
const loadedPuzzle = (grid = initialGrid) => ({
  ...puzzleList[0], grid: grid.map((row) => [...row]), analysis: analysis(),
});

async function openApp() {
  render(<App />);
  await screen.findByRole('grid', { name: /quick start board/i });
}

describe('playable grid', () => {
  afterEach(cleanup);
  beforeEach(() => {
    vi.clearAllMocks();
    listPuzzles.mockResolvedValue(puzzleList);
    loadPuzzle.mockResolvedValue(loadedPuzzle());
    analyzeGrid.mockResolvedValue(analysis());
    getHint.mockResolvedValue({ status: 'available', deduction: nakedDeduction, analysis: analysis() });
    getExplanation.mockResolvedValue({
      status: 'available', deduction: nakedDeduction,
      explanation: 'This cell has only one remaining candidate. Every other digit is blocked by its peers.',
      source: 'template', clause_ids: ['naked.cell_has_one_candidate', 'naked.peers_rule_out_others'],
    });
  });

  it('locks givens and renders server candidates', async () => {
    const user = userEvent.setup();
    await openApp();
    const grid = screen.getByRole('grid');
    const given = within(grid).getByRole('gridcell', { name: /row 1, column 1, 5, given/i });
    expect(given).toHaveClass('given');
    expect(within(grid).getByRole('gridcell', { name: /row 1, column 3, empty/i })).toHaveTextContent('1');
    expect(within(grid).getByRole('gridcell', { name: /row 1, column 3, empty/i })).toHaveTextContent('4');
    await user.click(given);
    await user.keyboard('8');
    expect(given).toHaveTextContent('5');
    expect(analyzeGrid).not.toHaveBeenCalled();
  });

  it('erases an editable entry and displays the refreshed backend candidates', async () => {
    const user = userEvent.setup();
    analyzeGrid
      .mockResolvedValueOnce(analysis())
      .mockResolvedValueOnce(analysis());
    await openApp();
    const grid = screen.getByRole('grid');
    const target = within(grid).getByRole('gridcell', { name: /row 1, column 3, empty/i });
    await user.click(target);
    await user.click(screen.getByRole('button', { name: '4' }));
    await waitFor(() => expect(target).toHaveTextContent('4'));
    await user.click(screen.getByRole('button', { name: /erase selected cell/i }));
    await waitFor(() => expect(target).toHaveAccessibleName(/empty/i));
    expect(target).toHaveTextContent('1');
    expect(target).toHaveTextContent('4');
    expect(analyzeGrid).toHaveBeenCalledTimes(2);
  });

  it('switches puzzles to a fresh board', async () => {
    const user = userEvent.setup();
    const second = { ...puzzleList[0], puzzle_id: 'whyku-02', name: 'More Space' };
    listPuzzles.mockResolvedValue([puzzleList[0], second]);
    loadPuzzle.mockImplementation(async (id) => ({
      ...loadedPuzzle(), puzzle_id: id, name: id === 'whyku-02' ? 'More Space' : 'Quick Start',
    }));
    await openApp();
    await user.selectOptions(screen.getByRole('combobox', { name: /choose puzzle/i }), 'whyku-02');
    expect(await screen.findByRole('grid', { name: /more space board/i })).toBeInTheDocument();
    expect(loadPuzzle).toHaveBeenCalledWith('whyku-02');
  });

  it('keeps the selected editable cell selected after keyboard entry and refreshes backend candidates', async () => {
    const user = userEvent.setup();
    await openApp();
    const grid = screen.getByRole('grid');
    const target = within(grid).getByRole('gridcell', { name: /row 1, column 3, empty/i });
    await user.click(target);
    await user.keyboard('8');
    await waitFor(() => expect(analyzeGrid).toHaveBeenCalledWith('whyku-01', expect.arrayContaining([expect.any(Array)])));
    expect(target).toHaveAttribute('aria-selected', 'true');
    expect(target).toHaveTextContent('8');
    const submitted = analyzeGrid.mock.calls.at(-1)[1];
    expect(submitted[0][2]).toBe(8);
  });

  it('renders a backend solution-mismatch warning without computing correctness in the UI', async () => {
    const user = userEvent.setup();
    analyzeGrid.mockResolvedValue(analysis({
      hints_enabled: false,
      hint_block_reason: 'solution_mismatch',
      solution_mismatch_cells: [[0, 2]],
    }));
    await openApp();
    await user.click(within(screen.getByRole('grid')).getByRole('gridcell', { name: /row 1, column 3, empty/i }));
    await user.keyboard('1');
    expect(await screen.findByText('Correct or erase the flagged entry before requesting a hint.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /get hint/i })).toBeDisabled();
    expect(getHint).not.toHaveBeenCalled();
    expect(getExplanation).not.toHaveBeenCalled();
    expect(within(screen.getByRole('grid')).getByRole('gridcell', { name: /row 1, column 3, 1/i })).toHaveClass('mismatch');
  });

  it('reveals the same naked-single record through all five levels, then applies it', async () => {
    const user = userEvent.setup();
    await openApp();
    await user.click(screen.getByRole('button', { name: /get hint/i }));
    expect(await screen.findByText('There is a cell with only one possible digit.')).toBeInTheDocument();
    const target = within(screen.getByRole('grid')).getByRole('gridcell', { name: /row 5, column 5, empty/i });
    expect(target).not.toHaveClass('hint-target');
    expect(target.textContent).toBe('');

    await user.click(screen.getByRole('button', { name: /next hint/i }));
    expect(screen.getByText('Relevant row · column · box')).toBeInTheDocument();
    expect(target).not.toHaveClass('hint-target');

    await user.click(screen.getByRole('button', { name: /next hint/i }));
    expect(screen.getByRole('heading', { name: 'Naked single' })).toBeInTheDocument();
    expect(target).toHaveClass('hint-target');
    expect(target).toHaveTextContent('•');
    expect(target).not.toHaveTextContent('5');

    await user.click(screen.getByRole('button', { name: /next hint/i }));
    expect(await screen.findByText(/This cell has only one remaining candidate/)).toBeInTheDocument();
    expect(screen.getByText('Offline template')).toBeInTheDocument();
    expect(screen.getByText(/R1C5/)).toBeInTheDocument();
    expect(getExplanation).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: /reveal the digit/i }));
    expect(target).toHaveTextContent('5');
    await user.click(screen.getByRole('button', { name: /enter 5 in the grid/i }));
    await waitFor(() => expect(analyzeGrid.mock.calls.at(-1)[1][4][4]).toBe(5));
    expect(screen.queryByText('Offline template')).not.toBeInTheDocument();
    expect(target).toHaveAttribute('aria-selected', 'true');
    await waitFor(() => expect(getHint.mock.calls.at(-1)[1][4][4]).toBe(5));
  });

  it('renders hidden-single unit positions and exclusions from the server record', async () => {
    const user = userEvent.setup();
    getHint.mockResolvedValue({ status: 'available', deduction: hiddenDeduction, analysis: analysis() });
    await openApp();
    await user.click(screen.getByRole('button', { name: /get hint/i }));
    await user.click(screen.getByRole('button', { name: /next hint/i }));
    expect(screen.getByText('Row 1')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /next hint/i }));
    expect(screen.getByRole('heading', { name: 'Hidden single in row 1' })).toBeInTheDocument();
    const grid = screen.getByRole('grid');
    expect(within(grid).getByRole('gridcell', { name: /row 1, column 3, empty/i })).toHaveClass('hint-target', 'hint-candidate-position');
    expect(within(grid).getByRole('gridcell', { name: /row 1, column 4, empty/i })).toHaveClass('hint-excluded-position');
    expect(within(grid).getByRole('gridcell', { name: /row 1, column 3, empty/i })).toHaveTextContent('•');
    expect(within(grid).getByRole('gridcell', { name: /row 1, column 3, empty/i })).not.toHaveTextContent('4');
  });

  it('ignores an older analysis response after a newer edit', async () => {
    const user = userEvent.setup();
    let resolveOld;
    analyzeGrid
      .mockImplementationOnce(() => new Promise((resolve) => { resolveOld = resolve; }))
      .mockResolvedValueOnce(analysis({
        candidates: initialGrid.map((row) => row.map(() => [9])),
      }));
    await openApp();
    const grid = screen.getByRole('grid');
    await user.click(within(grid).getByRole('gridcell', { name: /row 1, column 3, empty/i }));
    await user.keyboard('1');
    await user.keyboard('2');
    await waitFor(() => expect(analyzeGrid).toHaveBeenCalledTimes(2));
    resolveOld(analysis({ candidates: initialGrid.map((row) => row.map(() => [7])) }));
    await waitFor(() => expect(within(screen.getByRole('grid')).getByRole('gridcell', { name: /row 1, column 4, empty/i })).toHaveTextContent('9'));
    expect(within(screen.getByRole('grid')).getByRole('gridcell', { name: /row 1, column 4, empty/i })).not.toHaveTextContent('7');
  });
});
