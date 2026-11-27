// Client-side filtering, search, sorting and pagination for the list pages.
// Rows are rendered server-side as <a class="trow" data-row ...>; this script only shows/hides and reorders them.

type SortKey = 'num' | 'title' | 'level';

const LEVEL_RANK: Record<string, number> = { Easy: 0, Medium: 1, Hard: 2 };

export function initTable(root: HTMLElement): void {
  const body = root.querySelector<HTMLElement>('[data-rows]')!;
  const rows = Array.from(body.querySelectorAll<HTMLElement>('[data-row]'));
  const search = root.querySelector<HTMLInputElement>('[data-search]');
  const empty = root.querySelector<HTMLElement>('[data-empty]');
  const info = root.querySelector<HTMLElement>('[data-info]');
  const pages = root.querySelector<HTMLElement>('[data-pages]');
  const perSelect = root.querySelector<HTMLSelectElement>('[data-per]');
  const facetButtons = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-facet]'));
  const sortButtons = Array.from(root.querySelectorAll<HTMLButtonElement>('[data-sort]'));

  const state = {
    q: '',
    facets: {} as Record<string, Set<string>>,
    page: 0,
    per: Number(perSelect?.value ?? root.dataset.per ?? 10),
    sort: (root.dataset.sort as SortKey) ?? 'num',
    dir: Number(root.dataset.dir ?? 1),
  };

  const matches = (row: HTMLElement) => {
    if (state.q && !(row.dataset.search ?? '').includes(state.q)) return false;
    return Object.entries(state.facets).every(([facet, values]) => values.size === 0 || values.has(row.dataset[facet] ?? ''));
  };

  const compare = (a: HTMLElement, b: HTMLElement) => {
    const ta = a.dataset.title ?? '', tb = b.dataset.title ?? '';
    if (state.sort === 'title') return state.dir * ta.localeCompare(tb);
    if (state.sort === 'level') return state.dir * (LEVEL_RANK[a.dataset.difficulty ?? ''] - LEVEL_RANK[b.dataset.difficulty ?? '']) || ta.localeCompare(tb);
    return state.dir * (Number(a.dataset.num) - Number(b.dataset.num));
  };

  const pageButton = (label: string, target: number, opts: { current?: boolean; disabled?: boolean; aria?: string } = {}) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    if (opts.aria) b.setAttribute('aria-label', opts.aria);
    if (opts.current) b.setAttribute('aria-current', 'page');
    b.disabled = !!opts.disabled;
    b.addEventListener('click', () => { state.page = target; render(); });
    return b;
  };

  function render() {
    const visible = rows.filter(matches).sort(compare);
    const count = Math.max(1, Math.ceil(visible.length / state.per));
    state.page = Math.min(state.page, count - 1);
    const start = state.page * state.per;
    const shown = new Set(visible.slice(start, start + state.per));

    for (const row of rows) row.hidden = !shown.has(row);
    for (const row of visible) body.appendChild(row);
    if (empty) empty.hidden = visible.length > 0;
    if (info) info.textContent = visible.length ? `Results ${start + 1}–${Math.min(visible.length, start + state.per)} of ${visible.length}` : 'Results: 0';

    for (const b of sortButtons) {
      const key = b.dataset.sort as SortKey;
      b.textContent = (b.dataset.label ?? '') + (key === state.sort ? (state.dir > 0 ? ' ↑' : ' ↓') : '');
    }

    if (pages) {
      pages.replaceChildren();
      const p = state.page;
      pages.append(
        pageButton('«', 0, { disabled: p === 0, aria: 'First page' }),
        pageButton('‹', p - 1, { disabled: p === 0, aria: 'Previous page' }),
      );
      let last = -1;
      for (let i = 0; i < count; i++) {
        const near = Math.abs(i - p) <= 1 || i === 0 || i === count - 1 || (p <= 2 && i <= 3) || (p >= count - 3 && i >= count - 4);
        if (!near) continue;
        if (last >= 0 && i - last > 1) {
          const gap = document.createElement('span');
          gap.className = 'gap';
          gap.textContent = '…';
          pages.append(gap);
        }
        pages.append(pageButton(String(i + 1), i, { current: i === p }));
        last = i;
      }
      pages.append(
        pageButton('›', p + 1, { disabled: p >= count - 1, aria: 'Next page' }),
        pageButton('»', count - 1, { disabled: p >= count - 1, aria: 'Last page' }),
      );
    }
  }

  search?.addEventListener('input', () => { state.q = search.value.trim().toLowerCase(); state.page = 0; render(); });
  perSelect?.addEventListener('change', () => { state.per = Number(perSelect.value); state.page = 0; render(); });
  for (const b of facetButtons) {
    b.addEventListener('click', () => {
      const facet = b.dataset.facet!, value = b.dataset.value!;
      const set = (state.facets[facet] ??= new Set());
      if (set.has(value)) set.delete(value); else set.add(value);
      b.setAttribute('aria-pressed', String(set.has(value)));
      state.page = 0;
      render();
    });
  }
  for (const b of sortButtons) {
    b.addEventListener('click', () => {
      const key = b.dataset.sort as SortKey;
      state.dir = state.sort === key ? -state.dir : 1;
      state.sort = key;
      state.page = 0;
      render();
    });
  }
  root.querySelector('[data-reset]')?.addEventListener('click', () => {
    state.q = '';
    state.facets = {};
    state.page = 0;
    if (search) search.value = '';
    facetButtons.forEach((b) => b.setAttribute('aria-pressed', 'false'));
    render();
  });

  render();
}
