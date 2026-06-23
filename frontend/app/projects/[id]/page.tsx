"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { ErrorState } from "@/components/page-state";
import { api } from "@/lib/api";
import type { Project } from "@/types";

export default function Detail() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project>();
  const [error, setError] = useState("");

  useEffect(() => {
    api.project(id).then(setProject).catch(e => setError(e.message));
  }, [id]);

  if (error) return <ErrorState message={error} />;
  if (!project) return <div className="card h-96 animate-pulse" />;

  const score = Number(project.extra?.rk_compatibility ?? 0);
  const platforms = project.extra?.target_platforms ?? [];
  const notes = project.extra?.adaptation_notes ?? [];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="card p-6 lg:p-8">
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge">{project.project_type}</span>
          <span className="badge">{project.subtype}</span>
          {project.extra?.big_event_relevance && <span className="badge">AI event / trend</span>}
          <span className="text-xs text-slate-400">via {project.source_type}</span>
        </div>
        <h1 className="mt-5 text-3xl font-bold lg:text-4xl">{project.title}</h1>
        <p className="mt-4 text-lg leading-8 text-slate-600 dark:text-slate-300">{project.summary || project.description}</p>
        <div className="mt-6 flex flex-wrap gap-2">
          {project.tags.map(t => <span className="rounded-lg bg-slate-100 px-3 py-1.5 text-sm dark:bg-white/5" key={t.name}>#{t.name}</span>)}
        </div>
        <div className="mt-7 flex flex-wrap gap-3">
          <a className="btn-primary" href={project.url} target="_blank" rel="noreferrer">Open original ↗</a>
          <span className="btn-secondary">★ {project.stars.toLocaleString()}</span>
          <span className="btn-secondary">Idea value {project.idea_value.toFixed(1)}/10</span>
          <span className="btn-secondary">{project.difficulty}</span>
        </div>
      </div>

      {project.status === "failed" && <ErrorState message={project.error || "Collection failed"} />}

      <section className="card p-6">
        <h2 className="text-xl font-bold">RK3576 / RK3588 compatibility</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <Metric label="RK fit" value={score ? `${score.toFixed(1)}/10` : "Not scored"} />
          <Metric label="Target boards" value={platforms.length ? platforms.join(", ") : "Evaluate"} />
          <Metric label="Event signal" value={project.extra?.big_event_relevance ? "Yes" : "No"} />
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {notes.length ? notes.map(note => <span className="badge" key={note}>{note}</span>) : <span className="text-sm text-slate-400">No adaptation notes yet.</span>}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Info title="Hardware requirements" items={project.hardware_requirements} />
        <Info title="Software requirements" items={project.software_requirements} />
      </div>

      <section className="card p-6">
        <h2 className="text-xl font-bold">Ideas inspired by this project</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {project.inspired_ideas.length ? project.inspired_ideas.map((idea, i) => (
            <div key={i} className="rounded-xl border border-brand-500/20 bg-brand-500/5 p-4 text-sm leading-6">
              <b className="mr-2 text-brand-500">{String(i + 1).padStart(2, "0")}</b>{idea}
            </div>
          )) : <p className="text-sm text-slate-500">No ideas generated yet.</p>}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-slate-200 p-4 dark:border-white/10"><p className="text-xs uppercase tracking-wide text-slate-400">{label}</p><p className="mt-2 font-semibold">{value}</p></div>;
}

function Info({ title, items }: { title: string; items: string[] }) {
  return <section className="card p-6"><h2 className="font-bold">{title}</h2><div className="mt-3 flex flex-wrap gap-2">{items.length ? items.map(x => <span className="badge" key={x}>{x}</span>) : <span className="text-sm text-slate-400">None detected</span>}</div></section>;
}
