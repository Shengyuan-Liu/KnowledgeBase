/** Editable architecture illustration and matching vector preview. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const dir = path.dirname(fileURLToPath(import.meta.url));
const out = path.dirname(dir);
const W = 3840, H = 3310;
const C = { ink: '#29364b', muted: '#708095', blue: '#2878b7', orange: '#b77b30', green: '#388274', purple: '#8060aa', red: '#b45956' };
const F = { blue: '#eef7ff', orange: '#fff7ea', green: '#edf7f1', purple: '#f5f0fa' };
const elements = [];
let serial = 0;
function shape(type, x, y, width, height, strokeColor = C.ink, backgroundColor = 'transparent') {
  const n = ++serial;
  const e = { id: `kb-visual-${n}`, type, x, y, width, height, angle: 0, strokeColor, backgroundColor,
    fillStyle: 'solid', strokeWidth: 2.2, strokeStyle: 'solid', roughness: 1, opacity: 100,
    groupIds: [], frameId: null, roundness: type === 'rectangle' ? { type: 3 } : null,
    seed: n * 7171, version: 1, versionNonce: n * 7919, isDeleted: false, boundElements: [],
    updated: 1790000000000, link: null, locked: false };
  elements.push(e); return e;
}
function rect(x,y,w,h,color=C.ink,fill='transparent') { return shape('rectangle',x,y,w,h,color,fill); }
function oval(x,y,w,h,color=C.ink,fill='transparent') { return shape('ellipse',x,y,w,h,color,fill); }
function text(x,y,w,t,size=27,color=C.ink) {
  const e=shape('text',x,y,w,t.split('\n').length*size*1.3,color);
  Object.assign(e,{text:t,originalText:t,fontSize:size,fontFamily:2,textAlign:'left',verticalAlign:'top',containerId:null,autoResize:false,lineHeight:1.3});
  return e;
}
function line(points,color=C.ink,{arrow=false,dashed=false,fill='transparent',smooth=false}={}) {
  const [x,y]=points[0];
  const e=shape(arrow?'arrow':'line',x,y,Math.max(...points.map(p=>p[0]))-Math.min(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))-Math.min(...points.map(p=>p[1])),color,fill);
  Object.assign(e,{points:points.map(([a,b])=>[a-x,b-y]),startBinding:null,endBinding:null,startArrowhead:null,endArrowhead:arrow?'arrow':null,elbowed:false,strokeStyle:dashed?'dashed':'solid',roundness:smooth?{type:2}:null});
  return e;
}
const arrow=(p,c=C.blue,dashed=false)=>line(p,c,{arrow:true,dashed});
function group(name,draw) { const start=elements.length; draw(); for(const e of elements.slice(start))e.groupIds=[name]; }
function document(x,y,w=95,h=120,color=C.orange) {
  line([[x,y],[x+w-28,y],[x+w,y+28],[x+w,y+h],[x,y+h],[x,y]],color,{fill:'#ffffff'});
  line([[x+w-28,y],[x+w-28,y+28],[x+w,y+28]],color);
  for(let i=0;i<3;i++)line([[x+18,y+52+i*19],[x+w-18,y+52+i*19]],color);
}
function gear(x,y,r=53,color=C.orange) {
  const pts=[]; for(let i=0;i<=64;i++){ const a=i*Math.PI/32;const rr=(i%8<4)?r:r*.8;pts.push([x+r+rr*Math.cos(a),y+r+rr*Math.sin(a)]); }
  line(pts,color,{fill:'#ffffff'});oval(x+r*.62,y+r*.62,r*.76,r*.76,color,'#ffffff');
}
function bubble(x,y,w,h,color=C.blue) {
  rect(x,y,w,h,color,'#ffffff');line([[x+26,y+h],[x+26,y+h+24],[x+60,y+h]],color,{fill:'#ffffff'});
}
function cylinder(x,y,w,h,title,body,color=C.green) {
  group(`db-${title}`,()=>{
    oval(x,y+h-55,w,55,color,F.green);rect(x,y+27,w,h-55,color,F.green);
    line([[x,y+27],[x,y+h-27]],color);line([[x+w,y+27],[x+w,y+h-27]],color);
    oval(x,y,w,55,color,F.green);
    text(x+26,y+68,w-52,title,37,color);text(x+26,y+121,w-52,body,24);
  });
}
function cloud(x,y,w,h,title,body) {
  group(`cloud-${title}`,()=>{
    const curves = [
      [[.15,.94],[.00,.94],[-.02,.49],[.17,.47]],
      [[.17,.47],[.12,.17],[.40,.00],[.54,.27]],
      [[.54,.27],[.67,.03],[.91,.15],[.89,.41]],
      [[.89,.41],[1.07,.40],[1.04,.94],[.85,.94]],
      [[.85,.94],[.65,.94],[.35,.94],[.15,.94]]
    ];
    const pts = curves.flatMap(([a,b,c,d])=>Array.from({length:13},(_,i)=>{
      const t=i/12,u=1-t;
      return [x+w*(u*u*u*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t*t*t*d[0]),
              y+h*(u*u*u*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t*t*t*d[1])];
    }));
    line(pts,C.purple,{fill:'#ffffff',smooth:true});
    text(x+w*.17,y+h*.40,w*.75,title,36,C.purple);text(x+w*.17,y+h*.63,w*.75,body,24);
  });
}
function zone(x,w,title,subtitle,tone) {
  const b=rect(x,245,w,1430,C[tone],F[tone]);b.strokeStyle='dashed';b.strokeWidth=1.3;b.roughness=.4;
  text(x+35,280,w-70,title,51,C[tone]);text(x+37,350,w-70,subtitle,25,C.muted);
}
text(85,48,3600,'KnowledgeBase',68);
text(90,140,3200,'01  THE SYSTEM — follow a document in, then an answer back',35,C.muted);
line([[2780,158],[2860,158]],C.orange,{arrow:true});text(2880,140,280,'Upload / index',26,C.orange);
line([[3230,158],[3310,158]],C.blue,{arrow:true});text(3330,140,370,'Ask / retrieve / answer',26,C.blue);
zone(80,910,'FRONTEND','A browser UI · React + TypeScript','blue');
zone(1190,1620,'BACKEND','One Python process · FastAPI + RAG services','orange');
zone(3030,730,'MODEL PROVIDER','External OpenAI APIs','purple');
// Frontend is a recognizable browser, with its actual three-pane workspace.
group('frontend-browser',()=>{
  rect(155,470,760,520,C.blue,'#ffffff');
  line([[155,530],[915,530]],C.blue);
  for(let i=0;i<3;i++)oval(179+i*28,489,12,12,C.blue,F.blue);
  text(300,484,560,'localhost:8000 / KnowledgeBase',23,C.muted);
  line([[370,548],[370,915]],'#d4e0e8');line([[685,548],[685,915]],'#d4e0e8');
  text(180,556,180,'LIBRARY',25,C.blue);text(395,556,270,'CHAT',25,C.blue);text(709,556,175,'EVIDENCE',25,C.blue);
  document(190,620,68,91);text(183,728,180,'notes.txt',22);text(183,767,180,'● Ready',23,C.green);
  rect(180,846,166,42,C.blue,F.blue);text(192,852,150,'+ Upload TXT',21,C.blue);
  bubble(410,624,225,76);text(428,645,200,'Ask a question…',22);
  bubble(395,746,252,99);text(412,763,230,'Answer with [1]\nand source links',24);
  rect(395,869,252,48,'#c3d6e3');text(412,880,230,'Message…      →',22,C.muted);
  document(738,634,91,126,C.blue);text(707,798,183,'Original text\n+ filename',23);
  text(182,948,710,'LibraryPanel         ChatPanel + AnswerText       EvidencePanel',19,C.muted);
});
text(157,1033,775,'Workspace.tsx',33,C.blue);
text(157,1085,790,'useLibrary  ·  useChat + chatState\napi/files.ts  ·  api/chat.ts  ·  api/client.ts',26);
text(157,1190,790,'Stop → AbortController\nRefresh → restore saved conversation',27);
line([[157,1315],[912,1315]],'#c3d6e3');
text(157,1350,775,'Small browser memory',31,C.blue);
text(157,1405,775,'localStorage keeps only conversation ID.\nMessages and evidence live in the backend.',26);
text(157,1522,785,'UI helpers: Modal · Icon · useMediaQuery\nCSS Modules · tokens.css · types.ts',24,C.muted);
// A server rack marks the HTTP boundary, before the internal service workflows.
group('fastapi-server',()=>{
  rect(1245,500,220,420,C.ink,'#ffffff');
  for(let i=0;i<3;i++){
    rect(1268,531+i*109,173,76,C.ink,'#f8fafc');
    oval(1284,557+i*109,18,18,C.green,F.green);
    line([[1322,558+i*109],[1420,558+i*109]],C.muted);
    line([[1322,580+i*109],[1387,580+i*109]],C.muted);
  }
  text(1268,852,180,'FastAPI',34);
});
arrow([[915,650],[1245,650]],C.orange);text(1002,600,230,'TXT / HTTP',25,C.orange);
arrow([[915,780],[1245,780]],C.blue);text(1002,733,230,'Question',26,C.blue);
arrow([[1245,965],[915,965]],C.blue,true);text(995,992,230,'JSON / SSE',24,C.blue);
text(1244,1027,250,'API routes',30);
text(1244,1082,290,'/api/files\n/api/chat[/stream]\n/api/conversations',22);
text(1244,1200,290,'Pydantic schemas\nvalidate HTTP data.',22,C.muted);
// Ingestion is a document-processing line, not a row of explanatory cards.
text(1570,425,1150,'INGESTION  /  files.py',33,C.orange);
group('upload-pipeline',()=>{
  document(1585,515,92,119);text(1540,665,240,'Validate TXT',27,C.orange);
  gear(1800,520,53);text(1780,665,220,'split_text',27,C.orange);
  for(let i=2;i>=0;i--)document(2055+i*15,518-i*12,95,110);
  text(2025,665,260,'Text chunks',27,C.orange);
});
arrow([[1465,580],[1585,580]],C.orange);arrow([[1690,580],[1790,580]],C.orange);arrow([[1920,580],[2040,580]],C.orange);
arrow([[2200,570],[3070,570]],C.orange);text(2370,505,600,'EmbeddingClient → HTTPS',25,C.orange);
text(1565,735,1150,'UTF-8 .txt  →  2048-char chunks / 256 overlap  →  vectors',24,C.muted);
cloud(3080,455,615,240,'Embeddings','text-embedding-3-small');
text(3100,738,615,'Same embedding model for\ndocuments and questions.',26,C.purple);
// Chat lane: bubble -> lookup lens -> evidence pages -> remote model.
text(1570,815,1150,'QUESTION ANSWERING  /  chat.py',33,C.blue);
group('rag-pipeline',()=>{
  bubble(1575,915,175,90);text(1595,941,160,'Resolve',28,C.blue);
  oval(1865,909,83,83,C.blue,'#ffffff');line([[1934,980],[1980,1026]],C.blue);
  text(1830,1050,240,'Retrieve',28,C.blue);
  document(2110,907,100,123,C.blue);text(2080,1050,255,'Context [1…k]',27,C.blue);
});
arrow([[1465,815],[1518,815],[1518,960],[1575,960]],C.blue);
arrow([[1758,960],[1850,960]],C.blue);arrow([[1983,960],[2098,960]],C.blue);
arrow([[2230,960],[3070,960]],C.blue);text(2345,895,660,'LLMClient / StreamingLLMClient',24,C.blue);
cloud(3080,870,615,260,'Language model','gpt-4.1 · configurable');
text(3100,1170,615,'Rewrite follow-up references.\nGenerate answers from excerpts.\nReturn answer_delta events.',26,C.purple);
text(3100,1395,615,'Provider boundary',32,C.purple);
text(3100,1455,610,'Text leaves this machine for API calls.\nAPI key stays on the backend.\nClients are opened by lifespan.',25);
// Model output passes citation membership checks before persistence.
arrow([[3095,1100],[2860,1100],[2860,1170],[2730,1170]],C.blue,true);
shape('diamond',2550,1095,180,150,C.blue,'#ffffff');text(2589,1131,120,'Cite\ncheck',27,C.blue);
text(2340,1263,450,'Known IDs ≠ supported claims',24,C.muted);
arrow([[2550,1170],[2075,1170],[2075,1405],[2020,1405]],C.blue);text(2160,1120,410,'Save answer + sources',24,C.blue);
arrow([[1640,1290],[1640,1029]],C.green,true);text(1658,1103,335,'Recent history\n(up to 10 messages)',23,C.green);
// Persistence uses traditional database silhouettes, distinct from the server.
cylinder(1545,1290,475,245,'SQLite','files · chunks\nconversations · messages\nanswer_snapshots');
cylinder(2295,1340,440,195,'Chroma','vectors + chunk_id + file_id');
arrow([[1920,1096],[1920,1245],[2490,1245],[2490,1340]],C.blue);
text(2070,1215,230,'Top-k = 5',23,C.blue);
arrow([[3105,650],[2790,650],[2790,1435],[2735,1435]],C.orange,true);
text(2500,710,290,'Store vectors',23,C.orange);
arrow([[1615,636],[1615,705],[1520,705],[1520,1395],[1545,1395]],C.orange);
text(1550,1575,1190,'Ready files only · copied evidence survives deletion · two stores, no shared transaction',23,C.green);
// Lower two views expand mechanisms without repeating the architecture as cards.
line([[85,1790],[3755,1790]],'#d6dfe7');
text(90,1830,1700,'02  INSIDE INGESTION & RETRIEVAL',38,C.orange);
text(90,1888,1700,'Your original data-flow sketch, kept intact.',26,C.muted);
const old=JSON.parse(fs.readFileSync(path.join(dir,'original-ingestion-layout.json'),'utf8'));
for(const [type,x,y,w,h,stroke,bg,content,font,sw,end] of old){
  const e=shape(type,x+120,y+1980,w,h,stroke,bg);e.strokeWidth=sw;e.groupIds=['original-ingestion-sketch'];
  if(type==='text')Object.assign(e,{text:content,originalText:content,fontSize:font,fontFamily:2,textAlign:'left',verticalAlign:'top',containerId:null,autoResize:true,lineHeight:1.3});
  if(['line','arrow'].includes(type))Object.assign(e,{points:content,startBinding:null,endBinding:null,startArrowhead:null,endArrowhead:end,roundness:type==='line'?{type:2}:null});
}
line([[1790,1835],[1790,2860]],'#d6dfe7');
text(1890,1830,1880,'03  HOW AN ANSWER COMES BACK',38,C.blue);
text(1890,1888,1840,'Time runs downward. Save first; send complete afterward.',26,C.muted);
const actors=[['Browser',2010,C.blue],['FastAPI / chat',2500,C.orange],['Model',3000,C.purple],['SQLite',3490,C.green]];
for(const [name,x,color] of actors){
  if(name==='Browser'){rect(x-52,1980,104,72,color,'#ffffff');line([[x-35,2070],[x+35,2070]],color);line([[x,2052],[x,2070]],color);}
  else if(name==='Model'){oval(x-45,1981,90,72,color,F.purple);text(x-31,1999,75,'LLM',23,color);}
  else if(name==='SQLite'){oval(x-48,2038,96,28,color,F.green);rect(x-48,1999,96,52,color,F.green);oval(x-48,1985,96,29,color,F.green);}
  else {gear(x-40,1984,40,color);}
  text(x-110,2095,300,name,29,color);line([[x,2155],[x,2740]],'#bcc9d5',{dashed:true});
}
function sequence(a,b,y,label,color=C.blue){arrow([[a,y],[b,y]],color);text(Math.min(a,b)+20,y-44,Math.abs(a-b)-30,label,23,color);}
sequence(2010,2500,2215,'1  POST question');
sequence(2500,3000,2315,'2  Evidence + prompt');
sequence(3000,2500,2415,'3  Answer deltas',C.purple);
sequence(2500,2010,2475,'4  SSE → live text');
sequence(2500,3490,2575,'5  Commit messages + evidence snapshot',C.green);
sequence(2500,2010,2680,'6  complete');
text(1900,2790,1850,'SSE: start → sources → answer_delta → debug → complete\nStop aborts the request. EOF without complete is an interruption.',25,C.muted);
// Operations are a short lifecycle and terminal strip, not another card grid.
line([[85,2940],[3755,2940]],'#d6dfe7');
text(90,2980,1050,'04  RUN & MAINTAIN',35,C.muted);
group('terminal',()=>{
  rect(95,3050,475,150,C.ink,'#f3f6f8');text(122,3070,430,'> make app    :8000\n> make frontend  :5173\n> make stop',27,C.ink);
});
text(640,3060,980,'Startup: .env → data lock → storage → recovery → SDKs\nCLI and evals call the same Python services.\nEvaluation: retrieval, grounding, citations, abstention.',26);
text(1830,3000,1830,'File lifecycle',31,C.orange);
const states=[['Processing',1830,C.orange],['Ready',2210,C.green],['Failed',2510,C.red]];
for(const [label,x,color] of states){oval(x,3060,250,68,color,'#ffffff');text(x+35,3075,225,label,26,color);}
arrow([[2080,3094],[2210,3094]],C.orange);arrow([[1980,3129],[1980,3160],[2635,3160],[2635,3129]],C.red);
text(2870,3060,840,'Delete: exclude → remove vectors → remove rows\nRestart: abandoned processing → failed + cleanup\nUpload waits for indexing; no background worker.',24);
text(92,3250,3640,'Implemented local TXT MVP · Source map and detailed contracts: mvp-system-design.md · Architecture baseline: abd2e47',24,C.muted);
const scene={type:'excalidraw',version:2,source:'https://excalidraw.com',elements,appState:{viewBackgroundColor:'#ffffff',gridSize:null,zoom:{value:.3},scrollX:0,scrollY:0},files:{}};
fs.writeFileSync(path.join(out,'mvp-system-design.excalidraw'),JSON.stringify(scene,null,2)+'\n');
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const svg=[`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`,`<rect width="${W}" height="${H}" fill="white"/>`,'<defs><marker id="head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="context-stroke" stroke-width="1.4"/></marker></defs>'];
for(const e of elements){
  const attrs=`stroke="${e.strokeColor}" stroke-width="${e.strokeWidth}" fill="${e.backgroundColor==='transparent'?'none':e.backgroundColor}" ${e.strokeStyle==='dashed'?'stroke-dasharray="12 10"':''}`;
  if(e.type==='text')svg.push(`<text x="${e.x}" y="${e.y+e.fontSize}" font-family="Arial, sans-serif" font-size="${e.fontSize}" fill="${e.strokeColor}">${e.text.split('\n').map((l,i)=>`<tspan x="${e.x}" dy="${i?e.fontSize*e.lineHeight:0}">${esc(l)}</tspan>`).join('')}</text>`);
  else if(e.type==='rectangle')svg.push(`<rect x="${e.x}" y="${e.y}" width="${e.width}" height="${e.height}" rx="${e.roundness?14:0}" ${attrs}/>`);
  else if(e.type==='ellipse')svg.push(`<ellipse cx="${e.x+e.width/2}" cy="${e.y+e.height/2}" rx="${e.width/2}" ry="${e.height/2}" ${attrs}/>`);
  else if(e.type==='diamond')svg.push(`<polygon points="${e.x+e.width/2},${e.y} ${e.x+e.width},${e.y+e.height/2} ${e.x+e.width/2},${e.y+e.height} ${e.x},${e.y+e.height/2}" ${attrs}/>`);
  else svg.push(`<polyline points="${e.points.map(([x,y])=>`${x+e.x},${y+e.y}`).join(' ')}" ${attrs} stroke-linejoin="round" ${e.endArrowhead?'marker-end="url(#head)"':''}/>`);
}
svg.push('</svg>');fs.writeFileSync(path.join(out,'mvp-system-design.svg'),svg.join('\n'));
console.log(`Generated ${elements.length} editable elements; preserved ${old.length} original elements.`);
