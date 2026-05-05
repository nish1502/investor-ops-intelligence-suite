import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const rootDir = process.cwd();
    const projectRoot = path.join(rootDir, '..');
    const m2File = path.join(projectRoot, 'indmoney-pulse', 'output', 'v5_fee_explanation.json');
    
    if (fs.existsSync(m2File)) {
      const data = JSON.parse(fs.readFileSync(m2File, 'utf8'));
      const explanation = data.explanation || "";
      const bullets = explanation.split('\n')
        .filter((line: string) => line.trim().startsWith('-'))
        .map((line: string) => line.trim().replace(/^-\s*/, ''))
        .slice(0, 3);
        
      return NextResponse.json({
        bullets,
        sources: data.source_links || []
      });
    }
    
    return NextResponse.json({ bullets: [], sources: [] });
  } catch (error) {
    console.error('M2 API error:', error);
    return NextResponse.json({ error: 'Failed to load M2 data' }, { status: 500 });
  }
}
