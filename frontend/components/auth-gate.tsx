"use client";

import { FormEvent, useEffect, useState } from "react";

import { api, getApiToken, setApiToken } from "@/lib/api";


export function AuthGate({children}:{children:React.ReactNode}){
 const [state,setState]=useState<"checking"|"locked"|"ready">("checking");
 const [token,setToken]=useState("");
 const [error,setError]=useState("");
 const [busy,setBusy]=useState(false);
 useEffect(()=>{
  const lock=()=>setState("locked");
  window.addEventListener("collector:unauthorized",lock);
  api.authStatus().then(async ({required})=>{
   if(!required){setState("ready");return}
   if(!getApiToken()){setState("locked");return}
   try{await api.verifyAuth();setState("ready")}catch{setState("locked")}
  }).catch(e=>{setError(e.message);setState("locked")});
  return()=>window.removeEventListener("collector:unauthorized",lock);
 },[]);
 async function unlock(event:FormEvent){event.preventDefault();setBusy(true);setError("");setApiToken(token.trim());try{await api.verifyAuth();setState("ready")}catch(e){setApiToken("");setError(e instanceof Error?e.message:"Authentication failed")}finally{setBusy(false)}}
 if(state==="checking")return <div className="grid min-h-screen place-items-center bg-slate-50 dark:bg-ink"><div className="h-10 w-10 animate-spin rounded-full border-2 border-brand-500 border-t-transparent"/></div>;
 if(state==="locked")return <main className="grid min-h-screen place-items-center bg-slate-50 p-4 dark:bg-ink"><form className="card w-full max-w-md p-7" onSubmit={unlock}><div className="mb-6 grid h-12 w-12 place-items-center rounded-2xl bg-brand-500 text-xl text-white">AI</div><h1 className="text-2xl font-bold">Unlock Idea Collector</h1><p className="mt-2 text-sm leading-6 text-slate-500">Enter the <code>APP_API_KEY</code> configured on the server. It stays in this browser.</p><label className="mt-6 block"><span className="label">API key</span><input autoFocus className="input" type="password" value={token} onChange={e=>setToken(e.target.value)} placeholder="Server API key"/></label>{error&&<p className="mt-3 text-sm text-red-500">{error}</p>}<button className="btn-primary mt-5 w-full" disabled={!token.trim()||busy}>{busy?"Checking...":"Unlock"}</button></form></main>;
 return <>{children}</>;
}
