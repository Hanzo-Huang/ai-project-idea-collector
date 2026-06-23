import Link from "next/link";

import type { Project } from "@/types";

function rkScore(project: Project) {
  const value = Number(project.extra?.rk_compatibility ?? 0);
  return Number.isFinite(value) ? value : 0;
}

export function ProjectCard({ project }: { project: Project }) {
  const score = rkScore(project);
  const platforms = project.extra?.target_platforms ?? [];

  return (
    <Link href={`/projects/${project.id}`} className="card group flex min-h-64 flex-col p-5 transition hover:-translate-y-1 hover:border-brand-500/50 hover:shadow-glow">
      <div className="mb-4 flex items-center justify-between gap-3">
        <span className="badge">{project.project_type}</span>
        <span className="text-xs text-slate-400">{project.source_type}</span>
      </div>
      <h3 className="line-clamp-2 text-lg font-bold group-hover:text-brand-500">{project.title}</h3>
      <p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-500 dark:text-slate-400">{project.summary || project.description || "Analysis in progress..."}</p>
      <div className="mt-4 flex flex-wrap gap-1.5">
        {score > 0 && <span className="rounded-md bg-brand-500/10 px-2 py-1 text-xs font-semibold text-brand-500">RK fit {score.toFixed(1)}/10</span>}
        {project.extra?.big_event_relevance && <span className="rounded-md bg-amber-500/10 px-2 py-1 text-xs font-semibold text-amber-500">AI event</span>}
        {platforms.slice(0, 2).map(platform => <span key={platform} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-500 dark:bg-white/5">{platform}</span>)}
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {project.tags?.slice(0, 4).map(t => <span key={t.name} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-500 dark:bg-white/5">#{t.name}</span>)}
      </div>
      <div className="mt-auto flex items-center justify-between pt-5 text-xs text-slate-400">
        <span>★ {project.stars.toLocaleString()}</span>
        <span>Idea value <b className="text-brand-500">{project.idea_value.toFixed(1)}</b></span>
      </div>
    </Link>
  );
}
