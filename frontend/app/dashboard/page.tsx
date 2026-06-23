"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ErrorState } from "@/components/page-state";
import { api } from "@/lib/api";

export default function Dashboard() {
  const router = useRouter();
  const [data, setData] = useState<any>();
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = () => api.stats().then(setData).catch(e => setError(e.message));

  useEffect(() => {
    void load();
  }, []);

  async function add() {
    setBusy(true);
    setError("");
    try {
      const project = await api.addProject(url);
      setUrl("");
      void load();
      router.push(`/projects/${project.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not queue project");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-brand-600 via-violet-600 to-cyan-500 p-6 text-white shadow-glow lg:p-10">
        <p className="text-sm font-semibold uppercase tracking-widest text-white/70">Knowledge to inspiration</p>
        <h1 className="mt-2 max-w-2xl text-3xl font-bold lg:text-5xl">Find your next RK AI project idea.</h1>
        <p className="mt-3 max-w-xl text-white/75">Paste a URL and I will queue it immediately, then fetch metadata and AI analysis in the background.</p>
        <form className="mt-7 flex max-w-2xl flex-col gap-2 rounded-2xl bg-white/15 p-2 backdrop-blur sm:flex-row" onSubmit={e => { e.preventDefault(); void add(); }}>
          <input type="url" required className="min-w-0 flex-1 rounded-xl bg-white px-4 py-3 text-sm text-slate-900 outline-none" placeholder="Paste a GitHub repo or any project URL" value={url} onChange={e => setUrl(e.target.value)} />
          <button className="btn bg-ink text-white" disabled={!url || busy}>{busy ? "Queueing..." : "Queue project"}</button>
        </form>
      </section>

      {error && <ErrorState message={error} />}

      <section className="grid gap-4 sm:grid-cols-3">
        {[["Collected projects", data?.projects ?? "—"], ["Active sources", data?.active_sources ?? "—"], ["Average idea value", data?.average_idea_value ?? "—"]].map(([label, value]) => (
          <div className="card p-5" key={label}>
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-3xl font-bold">{value}</p>
          </div>
        ))}
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Recently collected</h2>
            <p className="text-sm text-slate-500">Fresh additions across your sources</p>
          </div>
          <Link href="/projects" className="text-sm font-semibold text-brand-500">View all →</Link>
        </div>
        <div className="card overflow-hidden">
          {data?.recent?.length ? data.recent.map((p: any) => (
            <Link href={`/projects/${p.id}`} key={p.id} className="flex items-center gap-4 border-b border-slate-100 p-4 last:border-0 hover:bg-slate-50 dark:border-white/5 dark:hover:bg-white/[.03]">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-500/10 text-sm font-bold text-brand-500">{p.title.slice(0, 2).toUpperCase()}</span>
              <span className="min-w-0 flex-1">
                <b className="block truncate text-sm">{p.title}</b>
                <small className="block truncate text-slate-400">{p.summary || p.status || "Processing"}</small>
              </span>
              <span className="badge hidden sm:inline-flex">{p.type}</span>
              <span className="text-sm font-semibold text-brand-500">{Number(p.idea_value || 0).toFixed(1)}</span>
            </Link>
          )) : <p className="p-12 text-center text-sm text-slate-500">Your newest projects will appear here.</p>}
        </div>
      </section>
    </div>
  );
}
