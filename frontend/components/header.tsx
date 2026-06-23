"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { TaskStatus } from "@/types";

import { ThemeToggle } from "./theme-provider";

export function Header() {
  const [q, setQ] = useState("");
  const router = useRouter();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/80 px-4 backdrop-blur dark:border-white/10 dark:bg-ink/80 lg:px-8">
      <Link href="/dashboard" className="font-bold lg:hidden">Idea Collector</Link>
      <form className="mx-auto w-full max-w-xl" onSubmit={e => { e.preventDefault(); router.push(`/projects?q=${encodeURIComponent(q)}`); }}>
        <input className="input py-2" placeholder="Search projects, models, ideas..." value={q} onChange={e => setQ(e.target.value)} />
      </form>
      <TaskMonitor />
      <ThemeToggle />
    </header>
  );
}

function TaskMonitor() {
  const [open, setOpen] = useState(false);
  const [tasks, setTasks] = useState<TaskStatus>();

  const load = () => api.tasks().then(setTasks).catch(() => undefined);

  useEffect(() => {
    void load();
    const timer = window.setInterval(load, tasks?.active ? 3000 : 8000);
    return () => window.clearInterval(timer);
  }, [tasks?.active]);

  const active = tasks?.active ?? 0;
  const failed = tasks?.failed ?? 0;

  return (
    <div className="relative">
      <button className="btn-secondary relative py-2 text-xs" type="button" onClick={() => setOpen(!open)}>
        Tasks
        {active > 0 && <span className="ml-2 rounded-full bg-brand-500 px-2 py-0.5 text-white">{active}</span>}
        {!active && failed > 0 && <span className="ml-2 rounded-full bg-red-500 px-2 py-0.5 text-white">{failed}</span>}
      </button>
      {open && (
        <div className="absolute right-0 mt-3 w-[min(92vw,32rem)] rounded-2xl border border-slate-200 bg-white p-4 shadow-2xl dark:border-white/10 dark:bg-panel">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold">Task progress</h3>
              <p className="text-xs text-slate-500">{active ? `${active} active task${active === 1 ? "" : "s"}` : "No active tasks"}</p>
            </div>
            <button className="text-xs font-semibold text-brand-500" onClick={() => void load()}>Refresh</button>
          </div>
          <div className="mt-4 max-h-[28rem] space-y-4 overflow-auto">
            <TaskSection title="Project imports" empty="No recent project tasks" count={tasks?.projects.length ?? 0}>
              {tasks?.projects.map(project => (
                <Link href={`/projects/${project.id}`} key={project.id} className="block rounded-xl border border-slate-100 p-3 text-sm hover:border-brand-500 dark:border-white/10">
                  <div className="flex items-center justify-between gap-3">
                    <b className="truncate">{project.title}</b>
                    <StatusBadge status={project.status} />
                  </div>
                  <p className="mt-1 truncate text-xs text-slate-400">{project.error || project.url}</p>
                </Link>
              ))}
            </TaskSection>
            <TaskSection title="Source collections" empty="No recent source collection jobs" count={tasks?.collections.length ?? 0}>
              {tasks?.collections.map(job => (
                <div key={job.id} className="rounded-xl border border-slate-100 p-3 text-sm dark:border-white/10">
                  <div className="flex items-center justify-between gap-3">
                    <b>Collection job</b>
                    <StatusBadge status={job.status} />
                  </div>
                  <p className="mt-1 text-xs text-slate-400">{job.message || `${job.projects_added}/${job.projects_found} projects added`}</p>
                </div>
              ))}
            </TaskSection>
          </div>
        </div>
      )}
    </div>
  );
}

function TaskSection({ title, empty, count, children }: { title: string; empty: string; count: number; children?: React.ReactNode }) {
  return (
    <section>
      <h4 className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-400">{title}</h4>
      <div className="space-y-2">{count ? children : <p className="rounded-xl bg-slate-50 p-3 text-xs text-slate-400 dark:bg-white/5">{empty}</p>}</div>
    </section>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color = status === "failed" ? "bg-red-500/10 text-red-500" : status === "ready" || status === "complete" ? "bg-emerald-500/10 text-emerald-600" : "bg-brand-500/10 text-brand-500";
  return <span className={`shrink-0 rounded-full px-2 py-1 text-xs font-semibold ${color}`}>{status}</span>;
}
