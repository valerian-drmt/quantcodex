// Typed access to the JSON produced by scripts/build_content.py
import problemsData from '../data/problems.json';
import notebooksData from '../data/notebooks.json';

export type Difficulty = 'Easy' | 'Medium' | 'Hard';

export interface Problem {
  id: number;
  slug: string;
  title: string;
  category: string;
  difficulty: Difficulty;
  excerpt: string;
  statement: string;
  hint: string;
  answer: string;
  explanation: string;
  updated: string;
}

export interface NotebookSection {
  id: string;
  title: string;
  html: string;
}

export interface Notebook {
  slug: string;
  path: string;
  title: string;
  summary: string;
  domain: string;
  cells: number;
  updated: string;
  sections: NotebookSection[];
}

export const problems = problemsData as Problem[];

// Numbered by order of addition (oldest = 1), listed newest first.
export const notebooks = (notebooksData as Notebook[]).map((nb, i, all) => ({ ...nb, num: all.length - i }));
