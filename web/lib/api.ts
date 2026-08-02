import type {
  CoachResponse,
  Course,
  CourseInput,
  CourseSummary,
  ExampleCard,
  ExampleCardInput,
  Mistake,
  MistakeInput,
  Source,
  Workspace,
} from "@/lib/types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL?.trim() || "/backend";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body !== undefined && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `خطای ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail ?? message;
    } catch {
      // Keep the HTTP status message when the response is not JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  async health(): Promise<boolean> {
    try {
      await request<{ status: string }>("/health");
      return true;
    } catch {
      return false;
    }
  },

  async listCourses(): Promise<CourseSummary[]> {
    const payload = await request<{ items: CourseSummary[] }>("/api/courses");
    return payload.items;
  },

  async createCourse(input: CourseInput): Promise<Course> {
    const payload = await request<{ course: Course }>("/api/courses", {
      method: "POST",
      body: JSON.stringify(input),
    });
    return payload.course;
  },

  async getWorkspace(courseId: number): Promise<Workspace> {
    return request<Workspace>(`/api/courses/${courseId}`);
  },

  async updateCourse(courseId: number, input: CourseInput): Promise<Course> {
    const payload = await request<{ course: Course }>(`/api/courses/${courseId}`, {
      method: "PUT",
      body: JSON.stringify(input),
    });
    return payload.course;
  },

  async deleteCourse(courseId: number): Promise<void> {
    return request<void>(`/api/courses/${courseId}`, { method: "DELETE" });
  },

  async uploadSource(courseId: number, file: File): Promise<Source> {
    const body = new FormData();
    body.append("file", file);
    const payload = await request<{ source: Source }>(`/api/courses/${courseId}/sources`, {
      method: "POST",
      body,
    });
    return payload.source;
  },

  async deleteSource(sourceId: number): Promise<void> {
    return request<void>(`/api/sources/${sourceId}`, { method: "DELETE" });
  },

  async createExample(courseId: number, input: ExampleCardInput): Promise<ExampleCard> {
    const payload = await request<{ example_card: ExampleCard }>(
      `/api/courses/${courseId}/example-cards`,
      { method: "POST", body: JSON.stringify(input) },
    );
    return payload.example_card;
  },

  async setExampleStatus(
    courseId: number,
    cardId: number,
    status: "draft" | "confirmed",
  ): Promise<ExampleCard> {
    const payload = await request<{ example_card: ExampleCard }>(
      `/api/courses/${courseId}/example-cards/${cardId}`,
      { method: "PATCH", body: JSON.stringify({ status }) },
    );
    return payload.example_card;
  },

  async deleteExample(courseId: number, cardId: number): Promise<void> {
    return request<void>(`/api/courses/${courseId}/example-cards/${cardId}`, {
      method: "DELETE",
    });
  },

  async createMistake(courseId: number, input: MistakeInput): Promise<Mistake> {
    const payload = await request<{ mistake: Mistake }>(`/api/courses/${courseId}/mistakes`, {
      method: "POST",
      body: JSON.stringify(input),
    });
    return payload.mistake;
  },

  async deleteMistake(courseId: number, mistakeId: number): Promise<void> {
    return request<void>(`/api/courses/${courseId}/mistakes/${mistakeId}`, {
      method: "DELETE",
    });
  },

  async runCoach(courseId: number, mode: string, prompt: string): Promise<CoachResponse> {
    return request<CoachResponse>(`/api/courses/${courseId}/run`, {
      method: "POST",
      body: JSON.stringify({ mode, prompt }),
    });
  },
};
