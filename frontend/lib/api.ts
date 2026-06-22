import type { Project, Source } from "@/types";
const API = process.env.NEXT_PUBLIC_API_URL || "/backend-api";
const TOKEN_KEY="collector_api_key";
export function getApiToken(){return typeof window==="undefined"?"":localStorage.getItem(TOKEN_KEY)||""}
export function setApiToken(token:string){if(typeof window!=="undefined"){if(token)localStorage.setItem(TOKEN_KEY,token);else localStorage.removeItem(TOKEN_KEY)}}
function errorMessage(body:unknown,status:number){if(body&&typeof body==="object"&&"detail" in body){const detail=(body as {detail:unknown}).detail;if(typeof detail==="string")return detail;if(Array.isArray(detail))return detail.map(item=>item&&typeof item==="object"&&"msg" in item?String(item.msg):String(item)).join("; ")}return `Request failed (${status})`}
async function request<T>(path:string, init?:RequestInit):Promise<T>{const token=getApiToken();const response=await fetch(`${API}${path}`,{...init,headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`}:{ }),...init?.headers},cache:"no-store"});if(!response.ok){const body=await response.json().catch(()=>({}));if(response.status===401&&typeof window!=="undefined")window.dispatchEvent(new Event("collector:unauthorized"));throw new Error(errorMessage(body,response.status))}return response.status===204?undefined as T:response.json()}
export const api={
 authStatus:()=>request<{required:boolean}>("/auth/status"),verifyAuth:()=>request<{authenticated:boolean}>("/auth/verify"),
 projects:(params="")=>request<{items:Project[];total:number;page:number;page_size:number}>(`/projects${params}`), project:(id:string)=>request<Project>(`/projects/${id}`), addProject:(url:string)=>request<Project>("/projects",{method:"POST",body:JSON.stringify({url})}),
 sources:()=>request<Source[]>("/sources"), addSource:(data:Partial<Source>)=>request<Source>("/sources",{method:"POST",body:JSON.stringify(data)}), updateSource:(id:string,data:Partial<Source>)=>request<Source>(`/sources/${id}`,{method:"PATCH",body:JSON.stringify(data)}), collectSource:(id:string)=>request<{found:number;added:number}>(`/sources/${id}/collect`,{method:"POST"}),
 settings:()=>request<Record<string,unknown>>("/settings"), saveSettings:(data:Record<string,unknown>)=>request<Record<string,unknown>>("/settings",{method:"PUT",body:JSON.stringify(data)}), stats:()=>request<any>("/dashboard/stats"), chat:(message:string,history:{role:string;content:string}[])=>request<{answer:string;citations:{id:string;title:string;url:string}[]}>("/chat",{method:"POST",body:JSON.stringify({message,history})})
};
