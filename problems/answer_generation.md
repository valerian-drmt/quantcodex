# Answer generation

This document defines how the **Hint**, **Solution** and **Explanation** fields of a problem are written. Everything is written in English.

## 1. Columns

| Column | Role |
|---|---|
| `Type` | Selects the Explanation template: *Puzzle / Problem*, *Technical question* or *Theoretical / applied question*. |
| `Hint` | Points to the first step of the reasoning without giving any result. |
| `Solution` | The final answer only. |
| `Explanation` | The full reasoning, structured according to `Type`. |

## 2. Common rules

**Hint**
- One sentence, at most 25 words, preferably phrased as a question.
- Points to the first section of the Explanation (key observation, method or concept).
- Contains no result, not even an intermediate one.

**Solution**
- The final answer only, without justification.
- Exact value, followed by a numerical approximation when useful: `$\tfrac{2}{3} \approx 0.667$`.
- Follows the format required by the statement exactly ("Answer +1 or −1", "two-digit precision", "yes/no", …).
- For an open question: one sentence.

**Explanation**
- Each section starts with a bold title `\textbf{Title.}`, with a line break between sections.
- 80 to 250 words depending on difficulty.
- The last line leads exactly to the Solution.
- Only the sections of the template are used (no optional sections).

## 3. Templates by type

### Puzzle / Problem — Observation → Modeling → Resolution → Verification

| Section | Content |
|---|---|
| Observation | The lever of the problem (symmetry, invariant, extreme case, what the statement really gives); restate the question in its essence. |
| Modeling | A simplified representation with its notation: table, states, variables, graph, small case. |
| Resolution | Steps inside the model, numbered when the statement contains several pieces of information. |
| Verification | Limit case, small case, simulation or cross-check. |

### Technical question — Method → Computation → Verification

| Section | Content |
|---|---|
| Method | Tool used and general formula, with the reason it applies. |
| Computation | Steps with intermediate values. |
| Verification | Derivative, limit case, order of magnitude, units or a second method. |

### Theoretical / applied question — Formula → Explanation → Answer

| Section | Content |
|---|---|
| Formula | Formal definition or key formula, with variables defined. |
| Explanation | Mechanism in 3 to 5 sentences: why it is true, how the position reacts. |
| Answer | Direct answer to the question; for a multiple-choice question, the correct letter and one line on why the other options are wrong. |

## 4. LaTeX conventions

- Inline math between `$...$`; display math between `$$...$$` only when needed.
- Characters escaped outside math mode: `\$` (currency), `\%`, `\&`, `\#`, `\_`.
- No Unicode math characters (`≤`, `→`, `×`): use `\le`, `\to`, `\times`.
- Decimal point (`0.667`), as in the statements.
- Every cell must compile with `pdflatex` (packages `amsmath`, `amssymb`).

## 5. Quality control

1. **Numerical check.** Every numerical result is recomputed in Python (exact computation, dynamic programming or Monte Carlo simulation) before being written.
2. **Consistency.** The Solution matches the result on the last line of the Explanation.
3. **Format.** Automatic check: balanced `$` delimiters, section titles matching the template, Hint length, ASCII-only text.
4. **Compilation.** All cells are compiled together with `pdflatex`; no error is tolerated.
5. **Flagging.** If a statement is ambiguous or the check does not confirm the expected result, the problem is flagged instead of being filled in by guesswork.

## 6. Examples

**Coin Piles** — *Puzzle / Problem*
- Hint: You cannot tell which coins show heads: what can you control?
- Solution: Take any 20 coins as one pile and flip all of them.
- Explanation:
  - `\textbf{Observation.}` You only control pile sizes and flipping coins; the only information is the total of 20 heads.
  - `\textbf{Modeling.}` A pile $A$ of 20 coins contains $k$ heads ($k$ unknown); pile $B$ contains $20-k$.
  - `\textbf{Resolution.}` After flipping every coin in $A$, it contains $20-k$ heads, the same as $B$, whatever $k$.
  - `\textbf{Verification.}` $k=0$: 20 and 20; $k=20$: 0 and 0.

**Dynamic hedging I** — *Technical question*
- Hint: What is the delta of one whole contract, and what delta must be offset?
- Solution: $-200$
- Explanation:
  - `\textbf{Method.}` Delta hedging means setting the total delta to zero: $\Delta_{\text{shares}} + n\,\Delta_{\text{contract}} = 0$.
  - `\textbf{Computation.}` $\Delta_{\text{shares}} = 800$, $\Delta_{\text{contract}} = 0.40 \times 10 = 4$, so $n = -800/4 = -200$.
  - `\textbf{Verification.}` $200 \times 10 \times 0.40 = 800$: the delta of the calls sold offsets the shares.

**Index dispersion** — *Theoretical / applied question*
- Hint: Besides the volatility of its components, what does an index's volatility depend on?
- Solution: $+1$
- Explanation:
  - `\textbf{Formula.}` $\sigma_I^2 = \sum_i w_i^2\sigma_i^2 + \sum_{i\neq j} w_i w_j \sigma_i \sigma_j \rho_{ij}$.
  - `\textbf{Explanation.}` With individual volatilities fixed, $\sigma_I$ increases with the $\rho_{ij}$; a call has positive vega, so $\partial C/\partial\rho = \text{vega}\cdot\partial\sigma_I/\partial\rho > 0$.
  - `\textbf{Answer.}` A long index call is long correlation: $+1$.

## 7. Production process

1. Answers are written in batches (≈ 40 problems) in `answers/batch_XXX.py` files (dictionary `#` → `(hint, solution, explanation)`).
2. Each batch goes through the quality control of section 5.
3. The merge script writes validated batches into the `Hint`, `Solution` and `Explanation` columns; problems not yet processed stay empty.
