"use client";
import { useEffect, useState } from "react";
export function ThemeToggle(){const [dark,setDark]=useState(false);useEffect(()=>{const d=localStorage.theme==="dark"||(!("theme" in localStorage)&&matchMedia("(prefers-color-scheme: dark)").matches);setDark(d);document.documentElement.classList.toggle("dark",d)},[]);function toggle(){const n=!dark;setDark(n);document.documentElement.classList.toggle("dark",n);localStorage.theme=n?"dark":"light"}return <button className="btn-secondary h-10 w-10 px-0" onClick={toggle} aria-label="Toggle theme">{dark?"☀":"☾"}</button>}

