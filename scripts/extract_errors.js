const fs = require('fs');
const path = require('path');

const tempDir = path.join(process.env.LOCALAPPDATA || 'C:\\Users\\KMP LIB\\AppData\\Local', 'Temp', 'cline');
const files = fs.readdirSync(tempDir).filter(f => f.startsWith('large-output-') && f.endsWith('.log'));
const target = files.find(f => f.includes('1785225987342'));
if (!target) { console.error('Log not found'); process.exit(1); }

const text = fs.readFileSync(path.join(tempDir, target), 'utf8');
const lines = text.split('\n');

// Find error messages near failure lines
let inError = false;
let errorBuffer = [];
let currentTest = '';

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  
  // Detect failure line
  const failMatch = line.match(/^\s*x\s+\d+\s+\[(chromium|mobile-chrome|tablet)\]\s+(›.*)$/);
  if (failMatch) {
    currentTest = failMatch[2].trim();
    inError = true;
    errorBuffer = [];
    continue;
  }
  
  // Detect "ok" line (end of error block)
  if (line.match(/^\s+ok\s+\d+/) && inError) {
    if (errorBuffer.length > 0) {
      console.log(`\n=== ${currentTest} ===`);
      console.log(errorBuffer.join('\n'));
    }
    inError = false;
    errorBuffer = [];
    currentTest = '';
  }
  
  // Collect error lines
  if (inError && line.includes('Error:')) {
    errorBuffer.push(line.trim());
  }
  if (inError && line.includes('expect(')) {
    errorBuffer.push(line.trim());
  }
  if (inError && line.includes('Received:')) {
    errorBuffer.push(line.trim());
  }
  if (inError && line.includes('Call log:')) {
    errorBuffer.push(line.trim());
  }
}

// Also print the summary section at the end
const summaryStart = text.lastIndexOf('  61 failed');
if (summaryStart > 0) {
  console.log('\n\n=== FAILURE SUMMARY (from end of output) ===');
  console.log(text.substring(summaryStart, summaryStart + 3000));
}