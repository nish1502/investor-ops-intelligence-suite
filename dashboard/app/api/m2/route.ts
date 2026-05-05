import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const rootDir = process.cwd();
    const publicM2File = path.join(rootDir, 'public', 'output', 'v5_fee_explanation.json');
    const peerM2File = path.join(rootDir, '..', 'indmoney-pulse', 'output', 'v5_fee_explanation.json');
    
    let m2File = publicM2File;
    if (!fs.existsSync(m2File) && fs.existsSync(peerM2File)) {
      m2File = peerM2File;
    }
    
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
