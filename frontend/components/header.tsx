"use client";
import { ThemeToggle } from "./theme-provider";import Link from "next/link";import { useState } from "react";import { useRouter } from "next/navigation";
export function Header(){const [q,setQ]=useState("");const router=useRouter();return <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/80 px-4 backdrop-blur dark:border-white/10 dark:bg-ink/80 lg:px-8"><Link href="/dashboard" className="font-bold lg:hidden">Idea Collector</Link><form className="mx-auto w-full max-w-xl" onSubmit={e=>{e.preventDefault();router.push(`/projects?q=${encodeURIComponent(q)}`)}}><input className="input py-2" placeholder="Search projects, models, ideas..." value={q} onChange={e=>setQ(e.target.value)}/></form><ThemeToggle/></header>}

