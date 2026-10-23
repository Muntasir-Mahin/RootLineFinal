// Verify the authored/generated UI palette and the documented AA token pairs.
import fs from 'node:fs';
import path from 'node:path';
const root = process.cwd();
const palette = {c900:'#06141B',c800:'#11212D',c700:'#253745',c600:'#4A5C6A',c400:'#9BA8AB',c200:'#CCD0CF'};
// Agro accents extend the existing neutrals; every literal stays documented.
Object.assign(palette, {leaf:'#245B3D',deepLeaf:'#19432C',fresh:'#B8D99A',soil:'#78563B',harvest:'#D8AE48',cream:'#F7F4EA',skin:'#B87D52',clay:'#A6533F',tint:'#EDF2E5',paper:'#FDFCF7',line:'#CFD9C8',nightLeaf:'#9DCE9B',nightFresh:'#395D3D',nightSoil:'#C8A27B',nightHarvest:'#E6C568',nightText:'#ECF1E8',nightTint:'#243B2C',nightPaper:'#192B21',nightLine:'#3C5744',nightPage:'#122019'});
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
      const withoutLightTints = line.replace(/color-mix\(in srgb,\s*var\(--c-(?:900|800|700|600|400|200)\)\s+[\d.]+%,\s*white\)/gi, '');
      if (/(?::|,)\s*(?:white|black|red|green|blue|yellow|orange|purple|gray|grey)\s*(?=[;},)])/i.test(withoutLightTints)) failures.push(`${path.relative(root,filename)}:${index+1}: named colour`);
    });
  }
}
walk(root);
function luminance(hex) {
  const rgb = (Array.isArray(hex) ? hex.map(v=>v/255) : [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255)).map(v=>v<=0.04045?v/12.92:((v+0.055)/1.055)**2.4);
  return rgb[0]*0.2126+rgb[1]*0.7152+rgb[2]*0.0722;
}
function tint(hex,weight) {return [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)*weight+255*(1-weight));}
const surfaces={...palette,lightPage:tint(palette.c200,.18),lightCard:tint(palette.c200,.04),lightHover:tint(palette.c200,.32)};
const pairs = [['Dark primary','c200','c900'],['Dark card primary','c200','c800'],['Dark muted','c400','c800'],['Dark hover muted','c400','c700'],['Light primary','c900','lightPage'],['Light muted page','c600','lightPage'],['Light muted card','c600','lightCard'],['Light muted hover','c600','lightHover'],['Light button','c200','c700']];
pairs.push(['Agro light text','c900','cream'],['Agro light card','c900','paper'],['Agro light muted','c600','cream'],['Agro light muted tint','c600','tint'],['Agro light button','cream','leaf'],['Agro light hover button','cream','deepLeaf'],['Agro dark text','c200','nightPage'],['Agro dark card','c200','nightPaper'],['Agro dark muted','c400','nightPaper'],['Agro dark muted hover','c400','nightTint'],['Agro dark button','nightPage','nightLeaf'],['Agro dark hover button','nightPage','fresh']);
const ratios = pairs.map(([role,foreground,background])=>{
 const values=[luminance(surfaces[foreground]),luminance(surfaces[background])].sort((a,b)=>a-b);
 const ratio=(values[1]+0.05)/(values[0]+0.05);
 if(ratio<4.5) failures.push(`${role}: ${ratio.toFixed(2)}:1`);
 return {role,foreground:surfaces[foreground],background:surfaces[background],ratio:ratio.toFixed(2)+':1',AA:ratio>=4.5};
});
console.table(ratios);
console.log(`Palette violations: ${failures.length}. Agro accents are decorative; status meanings retain text and icons.`);
if (failures.length) { console.error(failures.join('\n')); process.exitCode=1; }
