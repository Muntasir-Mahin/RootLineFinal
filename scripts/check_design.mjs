// Verify the authored/generated UI palette and the documented AA token pairs.
import fs from 'node:fs';
import path from 'node:path';
const root = process.cwd();
const palette = {c900:'#06141B',c800:'#11212D',c700:'#253745',c600:'#4A5C6A',c400:'#9BA8AB',c200:'#CCD0CF'};
const allowed = new Set(Object.values(palette).map(color => color.toLowerCase()));
const skip = new Set(['.git','.venv','node_modules','work','media','local_models','__pycache__','docs']);
const extensions = new Set(['.css','.html','.js','.mjs','.svg']);
const failures = [];
function walk(directory) {
  for (const entry of fs.readdirSync(directory, {withFileTypes:true})) {
    if (skip.has(entry.name)) continue;
    const filename = path.join(directory,entry.name);
    if (entry.isDirectory()) { walk(filename); continue; }
    if (!entry.isFile() || !extensions.has(path.extname(filename))) continue;
    fs.readFileSync(filename,'utf8').split('\n').forEach((line,index) => {
      const tokens = [...line.matchAll(/#[\da-f]{3,8}\b/gi)].map(match=>match[0]);
      tokens.push(...[...line.matchAll(/%23([\da-f]{3,8})\b/gi)].map(match=>'#'+match[1]));
      for (const token of tokens) if (!allowed.has(token.toLowerCase())) failures.push(`${path.relative(root,filename)}:${index+1}: ${token}`);
      if (/(?:rgba?|hsla?)\(\s*[\d.]/i.test(line)) failures.push(`${path.relative(root,filename)}:${index+1}: literal non-token colour function`);
      if (/(?::|,)\s*(?:white|black|red|green|blue|yellow|orange|purple|gray|grey)\s*(?=[;},)])/i.test(line)) failures.push(`${path.relative(root,filename)}:${index+1}: named colour`);
    });
  }
}
walk(root);
function luminance(hex) {
  const rgb = [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(v=>v<=0.04045?v/12.92:((v+0.055)/1.055)**2.4);
  return rgb[0]*0.2126+rgb[1]*0.7152+rgb[2]*0.0722;
}
const pairs = [['Dark primary','c200','c900'],['Dark card primary','c200','c800'],['Dark muted','c400','c800'],['Dark hover muted','c400','c700'],['Light primary','c900','c200'],['Light muted','c700','c200']];
const ratios = pairs.map(([role,foreground,background])=>{
 const values=[luminance(palette[foreground]),luminance(palette[background])].sort((a,b)=>a-b);
 const ratio=(values[1]+0.05)/(values[0]+0.05);
 if(ratio<4.5) failures.push(`${role}: ${ratio.toFixed(2)}:1`);
 return {role,foreground:palette[foreground],background:palette[background],ratio:ratio.toFixed(2)+':1',AA:ratio>=4.5};
});
console.table(ratios);
console.log(`Palette violations: ${failures.length}. Additional status colours: none.`);
if (failures.length) { console.error(failures.join('\n')); process.exitCode=1; }
