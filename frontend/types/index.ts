export type ProjectExtra = {
  target_platforms?: string[];
  rk_compatibility?: number;
  adaptation_notes?: string[];
  big_event_relevance?: boolean;
  [key: string]: unknown;
};
export type Project = { id:string; url:string; title:string; description:string; summary:string; source_type:string; project_type:string; subtype:string; difficulty:string; hardware_requirements:string[]; software_requirements:string[]; inspired_ideas:string[]; idea_value:number; stars:number; views:number; likes:number; status:string; error?:string; extra:ProjectExtra; tags:{name:string}[]; created_at:string; updated_at:string; external_created_at?:string; external_updated_at?:string };
export type Source = { id:string; name:string; type:string; url:string; query:string; enabled:boolean; collection_prompt:string; refresh_interval:number; last_checked_at?:string; created_at:string; updated_at:string };
export type TaskStatus = {
  active:number;
  failed:number;
  projects:{id:string;title:string;url:string;status:string;error?:string;updated_at:string}[];
  collections:{id:string;status:string;message:string;projects_found:number;projects_added:number;started_at:string;finished_at?:string}[];
};
