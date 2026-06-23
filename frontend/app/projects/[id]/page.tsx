"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useRouter } from "next/navigation";

import { ErrorState } from "@/components/page-state";
import { api } from "@/lib/api";
import type { Project } from "@/types";

export default function Detail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<Project>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});

  const load = () => api.project(id).then(project => {
    setProject(project);
    setForm(projectToForm(project));
  }).catch(e => setError(e.message));

  useEffect(() => {
    void load();
  }, [id]);

  useEffect(() => {
    if (!project || !["pending", "processing"].includes(project.status)) return;
    const timer = window.setInterval(() => void load(), 3000);
    return () => window.clearInterval(timer);
  }, [project?.status, id]);

  async function regenerate() {
    if (!project || busy) return;
    setBusy("regenerate");
    setError("");
    try {
      const next = await api.regenerateProject(project.id);
      setProject(next);
      setForm(projectToForm(next));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not regenerate project");
    } finally {
      setBusy("");
    }
  }

  async function saveEdit() {
    if (!project || busy) return;
    setBusy("save");
    setError("");
    try {
      const next = await api.updateProject(project.id, {
        title: form.title,
        description: form.description,
        summary: form.summary,
        project_type: form.project_type,
        subtype: form.subtype,
        difficulty: form.difficulty,
        idea_value: Number(form.idea_value || 0),
        tags: splitList(form.tags),
        hardware_requirements: splitList(form.hardware_requirements),
        software_requirements: splitList(form.software_requirements),
        inspired_ideas: splitLines(form.inspired_ideas),
        extra: {
          ...project.extra,
          rk_compatibility: Number(form.rk_compatibility || 0),
          target_platforms: splitList(form.target_platforms),
          adaptation_notes: splitLines(form.adaptation_notes),
          big_event_relevance: form.big_event_relevance === "true",
        },
      });
      setProject(next);
      setForm(projectToForm(next));
      setEditing(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save project");
    } finally {
      setBusy("");
    }
  }

  async function remove() {
    if (!project || busy) return;
    if (!window.confirm(`Delete "${project.title}"? This cannot be undone.`)) return;
    if (!window.confirm("Second confirmation: permanently delete this project and its documents?")) return;
    setBusy("delete");
    setError("");
    try {
      await api.deleteProject(project.id);
      router.push("/projects");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete project");
      setBusy("");
    }
  }

  if (error) return <ErrorState message={error} />;
  if (!project) return <div className="card h-96 animate-pulse" />;

  const score = Number(project.extra?.rk_compatibility ?? 0);
  const platforms = project.extra?.target_platforms ?? [];
  const notes = project.extra?.adaptation_notes ?? [];
  const isEnriching = ["pending", "processing"].includes(project.status);

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
          <span className="btn-secondary">{project.status}</span>
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <button className="btn-secondary" type="button" onClick={regenerate} disabled={!!busy || isEnriching}>{busy === "regenerate" ? "Queued..." : "Regenerate AI info"}</button>
          <button className="btn-secondary" type="button" onClick={() => setEditing(!editing)} disabled={!!busy || isEnriching}>{editing ? "Cancel edit" : "Edit information"}</button>
          <button className="rounded-xl bg-red-500 px-4 py-2 text-sm font-semibold text-white" type="button" onClick={remove} disabled={!!busy}>{busy === "delete" ? "Deleting..." : "Delete project"}</button>
        </div>
      </div>

      {isEnriching && <div className="rounded-xl border border-brand-500/30 bg-brand-500/10 p-4 text-sm text-brand-600">This project is being enriched in the background. You can leave this page; it will refresh automatically.</div>}
      {project.status === "failed" && <ErrorState message={project.error || "Collection failed"} />}
      {editing && <EditPanel form={form} setForm={setForm} save={saveEdit} busy={busy === "save"} />}

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

function projectToForm(project: Project) {
  return {
    title: project.title,
    description: project.description,
    summary: project.summary,
    project_type: project.project_type,
    subtype: project.subtype,
    difficulty: project.difficulty,
    idea_value: String(project.idea_value ?? 0),
    tags: project.tags.map(tag => tag.name).join(", "),
    hardware_requirements: project.hardware_requirements.join(", "),
    software_requirements: project.software_requirements.join(", "),
    inspired_ideas: project.inspired_ideas.join("\n"),
    rk_compatibility: String(project.extra?.rk_compatibility ?? 0),
    target_platforms: (project.extra?.target_platforms ?? []).join(", "),
    adaptation_notes: (project.extra?.adaptation_notes ?? []).join("\n"),
    big_event_relevance: project.extra?.big_event_relevance ? "true" : "false",
  };
}

function splitList(value = "") {
  return value.split(",").map(item => item.trim()).filter(Boolean);
}

function splitLines(value = "") {
  return value.split("\n").map(item => item.trim()).filter(Boolean);
}

function EditPanel({ form, setForm, save, busy }: { form: Record<string, string>; setForm: (next: Record<string, string>) => void; save: () => void; busy: boolean }) {
  const set = (key: string, value: string) => setForm({ ...form, [key]: value });
  return (
    <section className="card space-y-5 p-6">
      <h2 className="text-xl font-bold">Edit project information</h2>
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Title" value={form.title} onChange={value => set("title", value)} />
        <Field label="Project type" value={form.project_type} onChange={value => set("project_type", value)} />
        <Field label="Subtype" value={form.subtype} onChange={value => set("subtype", value)} />
        <Field label="Difficulty" value={form.difficulty} onChange={value => set("difficulty", value)} />
        <Field label="Idea value" type="number" value={form.idea_value} onChange={value => set("idea_value", value)} />
        <Field label="RK fit" type="number" value={form.rk_compatibility} onChange={value => set("rk_compatibility", value)} />
        <Field label="Target boards (comma separated)" value={form.target_platforms} onChange={value => set("target_platforms", value)} />
        <label>
          <span className="label">AI event / trend</span>
          <select className="input" value={form.big_event_relevance} onChange={e => set("big_event_relevance", e.target.value)}>
            <option value="false">No</option>
            <option value="true">Yes</option>
          </select>
        </label>
        <Field label="Tags (comma separated)" value={form.tags} onChange={value => set("tags", value)} />
        <Field label="Hardware requirements" value={form.hardware_requirements} onChange={value => set("hardware_requirements", value)} />
        <Field label="Software requirements" value={form.software_requirements} onChange={value => set("software_requirements", value)} />
      </div>
      <TextArea label="Summary" value={form.summary} onChange={value => set("summary", value)} />
      <TextArea label="Description" value={form.description} onChange={value => set("description", value)} />
      <TextArea label="Inspired ideas (one per line)" value={form.inspired_ideas} onChange={value => set("inspired_ideas", value)} />
      <TextArea label="Adaptation notes (one per line)" value={form.adaptation_notes} onChange={value => set("adaptation_notes", value)} />
      <button className="btn-primary" type="button" onClick={save} disabled={busy}>{busy ? "Saving..." : "Save edits"}</button>
    </section>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value?: string; onChange: (value: string) => void; type?: string }) {
  return <label><span className="label">{label}</span><input className="input" type={type} value={value ?? ""} onChange={e => onChange(e.target.value)} /></label>;
}

function TextArea({ label, value, onChange }: { label: string; value?: string; onChange: (value: string) => void }) {
  return <label><span className="label">{label}</span><textarea className="input min-h-28" value={value ?? ""} onChange={e => onChange(e.target.value)} /></label>;
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-xl border border-slate-200 p-4 dark:border-white/10"><p className="text-xs uppercase tracking-wide text-slate-400">{label}</p><p className="mt-2 font-semibold">{value}</p></div>;
}

function Info({ title, items }: { title: string; items: string[] }) {
  return <section className="card p-6"><h2 className="font-bold">{title}</h2><div className="mt-3 flex flex-wrap gap-2">{items.length ? items.map(x => <span className="badge" key={x}>{x}</span>) : <span className="text-sm text-slate-400">None detected</span>}</div></section>;
}
