const fs = require('fs');
const path = require('path');

const tempDir = path.join(process.env.LOCALAPPDATA || 'C:\\Users\\KMP LIB\\AppData\\Local', 'Temp', 'cline');
const files = fs.readdirSync(tempDir).filter(f => f.startsWith('large-output-') && f.endsWith('.log'));
const target = files.find(f => f.includes('1785225987342'));
if (!target) { console.error('Log not found'); process.exit(1); }

const text = fs.readFileSync(path.join(tempDir, target), 'utf8');
const lines = text.split('\n');

// Collect all error snippets around failure markers
let collecting = false;
let collected = [];
let testName = '';

for (let i = 0; i < lines.length; i++) {
  const line = lines[i];
  
  // Start collecting at an "x" failure line
  const failMatch = line.match(/^\s*x\s+\d+\s+\[(chromium|mobile-chrome|tablet)\]\s+(›.*)$/);
  if (failMatch) {
    // Flush previous
    if (collected.length > 0 && testName) {
      console.log(`\n### ${testName.replace(/â€¢|â€”|â”€/g,'>')}`);
      const unique = [...new Set(collected)];
      unique.slice(0, 3).forEach(e => console.log(`  ${e.replace(/â€¢|â€”|â”€/g,'>')}`));
    }
    testName = failMatch[2].trim();
    collected = [];
    collecting = true;
    continue;
  }
  
  if (collecting) {
    if (line.includes('Error:') || line.includes('expect(') || line.includes('Received:') || line.includes('AttributeError') || line.includes('ResponseValidationError') || line.includes('ValidationError') || line.includes('toBeTruthy') || line.includes('toBeFalsy')) {
      collected.push(line.trim());
    }
    // Stop collecting when we see next test start or "ok"
    if (line.match(/^\s+ok\s+\d+/) || (line.match(/^\s+\d+\s+\[/) && !line.includes('Error') && !line.includes('expect'))) {
      if (collected.length > 0 && testName) {
        console.log(`\n### ${testName.replace(/â€¢|â€”|â”€/g,'>')}`);
        const unique = [...new Set(collected)];
        unique.slice(0, 3).forEach(e => console.log(`  ${e.replace(/â€¢|â€”|â”€/g,'>')}`));
      }
      collecting = false;
      collected = [];
      testName = '';
    }
  }
}