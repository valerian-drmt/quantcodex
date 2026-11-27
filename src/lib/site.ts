// Site-wide settings. Change your links here only.
export const SITE = {
  name: 'QuantCodex',
  author: 'Valérian Darmenté',
  github: 'https://github.com/valerian-drmt',
  linkedin: 'https://www.linkedin.com/in/val%C3%A9rian-darment%C3%A9/',
  repo: 'https://github.com/valerian-drmt/quantcodex',
  description:
    'A codex for quantitative finance: solve quant problems and brainteasers, look up the theory in Jupyter notebooks, and model probability games and game theory step by step.',
};

/** Prefix a site path with the deploy base ("/quantcodex"). */
export function url(path = ''): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}/${path.replace(/^\//, '')}`;
}
