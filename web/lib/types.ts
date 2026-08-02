export type Course = {
  id: number;
  name: string;
  professor: string;
  term: string;
  exam_date: string;
  target_grade: number | null;
  daily_minutes: number;
  exam_scope: string;
  notes: string;
  created_at: string;
  updated_at: string;
};

export type CourseSummary = Course & {
  source_count: number;
  run_count: number;
  mistake_count: number;
  example_count: number;
};

export type Source = {
  id: number;
  course_id: number;
  filename: string;
  source_type: string;
  character_count: number;
  created_at: string;
  chunk_count?: number;
};

export type ExampleCard = {
  id: number;
  course_id: number;
  title: string;
  topic: string;
  question: string;
  solution: string;
  method_name: string;
  source_kind: string;
  source_reference: string;
  notes: string;
  status: "draft" | "confirmed";
  created_at: string;
  updated_at: string;
};

export type Mistake = {
  id: number;
  course_id: number;
  topic: string;
  category: string;
  description: string;
  prevention: string;
  severity: "low" | "medium" | "high";
  created_at: string;
};

export type Run = {
  id: number;
  course_id: number;
  mode: string;
  user_input: string;
  output: string;
  provider: string;
  evidence: Evidence[];
  created_at: string;
};

export type Evidence = {
  source_number?: number;
  filename: string;
  chunk_index: number | null;
  content?: string;
  score?: number;
  evidence_kind?: string;
};

export type Workspace = {
  course: Course;
  sources: Source[];
  example_cards: ExampleCard[];
  runs: Run[];
  mistakes: Mistake[];
  model_enabled: boolean;
};

export type CourseInput = {
  name: string;
  professor: string;
  term: string;
  exam_date: string;
  target_grade: number | null;
  daily_minutes: number;
  exam_scope: string;
  notes: string;
};

export type ExampleCardInput = {
  title: string;
  topic: string;
  question: string;
  solution: string;
  method_name: string;
  source_kind: string;
  source_reference: string;
  notes: string;
  status: "draft" | "confirmed";
};

export type MistakeInput = {
  topic: string;
  category: string;
  description: string;
  prevention: string;
  severity: "low" | "medium" | "high";
};

export type CoachResponse = {
  output: string;
  provider: string;
  evidence: Evidence[];
  structured_output?: Record<string, unknown> | null;
  schema?: string | null;
  validation_error?: string | null;
  validation_status?: "valid" | "recovered" | "invalid_fallback" | "not_applicable";
  repair_attempted?: boolean;
};
