import { CourseWorkspace } from "@/components/course-workspace";

export default async function CoursePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <CourseWorkspace courseId={Number(id)} />;
}
