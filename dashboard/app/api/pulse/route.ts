import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const rootDir = process.cwd();
    
    // Check both local public/output and peer indmoney-pulse/output
    const publicOutputDir = path.join(rootDir, 'public', 'output');
    const peerOutputDir = path.join(rootDir, '..', 'indmoney-pulse', 'output');
    
    let pulseDir = publicOutputDir;
    
    // In Vercel, public/output is safer. Locally, peer might be more up-to-date.
    if (!fs.existsSync(pulseDir) && fs.existsSync(peerOutputDir)) {
      pulseDir = peerOutputDir;
    }
    
    // Cloud Safety: Ensure we don't crash if directory is missing
    if (!fs.existsSync(pulseDir)) {
      console.log('>>> Pulse directory not found, returning empty data');
      return NextResponse.json({ trends: {}, actionIdeas: [] });
    }

    const trendsPath = path.join(pulseDir, 'v3_trends.json');
    const reportPath = path.join(pulseDir, 'v3_weekly_pulse.md');
    
    let trends: Record<string, any> = {};
    if (fs.existsSync(trendsPath)) {
      trends = JSON.parse(fs.readFileSync(trendsPath, 'utf8'));
    }
    
    let actionIdeas: any[] = [];
    if (fs.existsSync(reportPath)) {
      const content = fs.readFileSync(reportPath, 'utf8');
      const actionSection = content.split('### Action Ideas')[1];
      if (actionSection) {
        actionIdeas = actionSection.trim().split('\n')
          .filter(line => line.trim() && line.match(/^\d+\./))
          .map(line => {
            // Regex to match: 1. **[PRIORITY]** Title: Description
            const match = line.match(/^\d+\.\s*(?:\*\*)?\[(.*?)\].*?\s*(?:\*\*)?\s*(.*?):\s*(.*)$/);
            
            if (match) {
              return {
                priority: match[1].replace(/\*/g, '').trim(),
                title: match[2].replace(/\*/g, '').trim(),
                desc: match[3].trim()
              };
            }
            
            // Fallback for different formats
            const priority = line.includes('[') ? line.split('[')[1].split(']')[0] : 'MEDIUM';
            const parts = line.split(': ');
            const titlePart = parts[0].split(']')[1] || parts[0];
            
            return {
              priority: priority.replace(/\*/g, '').trim(),
              title: titlePart.replace(/[*#\-\d\.]/g, '').trim(),
              desc: (parts[1] || '').trim()
            };
          });
      }
    }
    
    return NextResponse.json({ trends, actionIdeas });
  } catch (error) {
    console.error('Pulse API error:', error);
    return NextResponse.json({ error: 'Failed to load pulse data' }, { status: 500 });
  }
}
