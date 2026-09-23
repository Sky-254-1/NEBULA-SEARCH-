const fs = require('fs');
const path = require('path');

// Find the correct log file
const tempDir = path.join(process.env.LOCALAPPDATA || 'C:\\Users\\KMP LIB\\AppData\\Local', 'Temp', 'cline');
const files = fs.readdirSync(tempDir).filter(f => f.startsWith('large-output-') && f.endsWith('.log'));
// Use the one with the right timestamp (1785225987342)
const target = files.find(f => f.includes('1785225987342'));
if (!target) {
  console.error('Could not find log file');
  process.exit(1);
}
const logPath = path.join(tempDir, target);
const text = fs.readFileSync(logPath, 'utf8');
const lines = text.split('\n');

// Parse failures: lines starting with "  x" followed by profile and test name
const fails = {};

for (const line of lines) {
  const m = line.match(/^\s*x\s+\d+\s+\[(chromium|mobile-chrome|tablet)\]\s+(›.*)$/);
  if (m) {
    const profile = m[1];
    const testName = m[2].trim();
    if (!fails[testName]) fails[testName] = {};
    fails[testName][profile] = true;
  }
}

const names = Object.keys(fails).sort();
console.log(`\n=== DISTINCT FAILING TESTS: ${names.length} ===\n`);

// Group by profile overlap
const all3 = [];
const chromiumOnly = [];
const mobileOnly = [];
const tabletOnly = [];
const twoProfiles = [];

for (const n of names) {
  const p = Object.keys(fails[n]);
  if (p.length === 3) all3.push(n);
  else if (p.length === 2) twoProfiles.push({name: n, profiles: p.join(',')});
  else if (p[0] === 'chromium') chromiumOnly.push(n);
  else if (p[0] === 'mobile-chrome') mobileOnly.push(n);
  else if (p[0] === 'tablet') tabletOnly.push(n);
}

console.log(`Fail on ALL 3 profiles (shared root cause): ${all3.length}`);
all3.forEach(n => console.log(`  ${n}`));

console.log(`\nFail on 2 profiles: ${twoProfiles.length}`);
twoProfiles.forEach(({name, profiles}) => console.log(`  [${profiles}] ${name}`));

console.log(`\nFail on chromium only: ${chromiumOnly.length}`);
chromiumOnly.forEach(n => console.log(`  ${n}`));

console.log(`\nFail on mobile-chrome only: ${mobileOnly.length}`);
mobileOnly.forEach(n => console.log(`  ${n}`));

console.log(`\nFail on tablet only: ${tabletOnly.length}`);
tabletOnly.forEach(n => console.log(`  ${n}`));