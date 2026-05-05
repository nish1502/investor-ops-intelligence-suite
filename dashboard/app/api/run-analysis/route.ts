import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";

// Simple in-memory state for the pipeline
let pipelineState = {
  isRunning: false,
  lastRun: null as string | null,
  status: "idle",
  error: null as string | null
};

export async function GET() {
  return NextResponse.json(pipelineState);
}

export async function POST() {
  if (pipelineState.isRunning) {
    return NextResponse.json({ status: "running" }, { status: 409 });
  }

  const rootDir = process.cwd();
  const backendDir = path.join(rootDir, "..", "indmoney-pulse", "backend");
  const triggerScript = path.join(backendDir, "trigger_pulse.py");

  console.log(">>> 🚀 Starting Background Python Pipeline:", triggerScript);

  pipelineState.isRunning = true;
  pipelineState.status = "running";
  pipelineState.error = null;

  // Start process in background
  const pythonProcess = spawn("python3", [triggerScript], { cwd: backendDir });

  pythonProcess.stdout.on("data", (data) => {
    console.log(`[Python Stdout]: ${data}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`[Python Stderr]: ${data}`);
  });

  pythonProcess.on("close", (code) => {
    pipelineState.isRunning = false;
    pipelineState.lastRun = new Date().toISOString();
    
    if (code === 0) {
      console.log(">>> ✅ Background Pipeline Completed Successfully");
      pipelineState.status = "success";
      
      // Sync files
      try {
        const outputSourceDir = path.join(backendDir, "output");
        const publicDestDir = path.join(rootDir, "public", "output");
        const projectDestDir = path.join(rootDir, "..", "indmoney-pulse", "output");
        
        const ensureDir = (dir: string) => {
          if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        };

        ensureDir(publicDestDir);
        ensureDir(projectDestDir);

        const filesToSync = ["v3_trends.json", "v3_weekly_pulse.md", "v5_fee_explanation.json"];
        filesToSync.forEach(file => {
          const src = path.join(outputSourceDir, file);
          const pubDest = path.join(publicDestDir, file);
          const projDest = path.join(projectDestDir, file);
          
          if (fs.existsSync(src)) {
            fs.copyFileSync(src, pubDest);
            // Only try to sync to peer if it's accessible (fails gracefully in Vercel)
            try {
              if (fs.existsSync(path.dirname(projDest))) {
                fs.copyFileSync(src, projDest);
              }
            } catch (err) {
              console.warn(`Could not sync to peer directory: ${projDest}`);
            }
          }
        });
      } catch (e) {
        console.error("Sync failed:", e);
      }
    } else {
      console.error(`>>> ❌ Background Pipeline Failed with code ${code}`);
      pipelineState.status = "error";
      pipelineState.error = `Process exited with code ${code}`;
    }
  });

  return NextResponse.json({ status: "started" });
}
