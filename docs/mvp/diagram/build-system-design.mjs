/** Generate the editable implementation map and matching SVG. No application code changes. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url)), out=path.dirname(dir);
const C={ink:'#243247',muted:'#68758a',blue:'#2563a6',orange:'#ad6525',green:'#237b59',purple:'#7653a6',red:'#b44646'};
const fills={blue:'#edf5ff',orange:'#fff6e8',green:'#eaf7f0',purple:'#f3effb',red:'#fff0ef',gray:'#f5f7fa'};
const elements=[], cardBounds=[]; let serial=0;
function base(type,x,y,w,h,color=C.ink,bg='transparent'){
 const n=++serial;const e={id:`kb-map-${n}`,type,x,y,width:w,height:h,angle:0,strokeColor:color,backgroundColor:bg,fillStyle:'solid',strokeWidth:2,strokeStyle:'solid',roughness:0,opacity:100,groupIds:[],frameId:null,roundness:type==='rectangle'?{type:3}:null,seed:n*7171,version:1,versionNonce:n*7919,isDeleted:false,boundElements:[],updated:1790000000000,link:null,locked:false};elements.push(e);return e;
}
function wrap(text,max){return text.split('\n').flatMap(line=>{const words=line.split(' '), lines=[];let s='';for(const w of words){if(s&&s.length+w.length+1>max){lines.push(s);s=w;}else s+=(s?' ':'')+w;}lines.push(s);return lines;}).join('\n');}
function text(x,y,w,t,size=24,color=C.ink){t=wrap(t,Math.floor(w/(size*.56)));const e=base('text',x,y,w,t.split('\n').length*size*1.3,color);Object.assign(e,{text:t,originalText:t,fontSize:size,fontFamily:2,textAlign:'left',verticalAlign:'top',containerId:null,autoResize:false,lineHeight:1.3});return e;}
function rect(x,y,w,h,color=C.ink,bg='transparent'){return base('rectangle',x,y,w,h,color,bg);}
function card(x,y,w,h,title,body,tone='blue',size=24){const b=rect(x,y,w,h,C[tone]||C.ink,fills[tone]||fills.gray);const titleE=text(x+22,y+17,w-44,title,29,C[tone]||C.ink);const bodyE=text(x+22,y+65,w-44,body,size);const group=`card-${b.id}`;[b,titleE,bodyE].forEach(e=>e.groupIds=[group]);if(bodyE.y+bodyE.height>y+h-12)throw Error(`Text overflow: ${title}`);cardBounds.push({title,id:b.id,x,y,w,h});return b;}
function arrow(points,color=C.blue,label='',labelX=0,labelY=0,dashed=false){const [x,y]=points[0], rel=points.map(([a,b])=>[a-x,b-y]);const e=base('arrow',x,y,Math.max(...points.map(p=>p[0]))-Math.min(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))-Math.min(...points.map(p=>p[1])),color);Object.assign(e,{points:rel,startBinding:null,endBinding:null,startArrowhead:null,endArrowhead:'arrow',elbowed:false,strokeStyle:dashed?'dashed':'solid'});if(label)text(labelX,labelY,500,label,22,color);return e;}
function panel(x,y,w,h,num,title,subtitle,tone='blue'){const b=rect(x,y,w,h,'#ccd5e1','#ffffff');b.strokeWidth=1;b.locked=true;text(x+28,y+22,w-56,`${num}  ${title}`,36,C[tone]);text(x+28,y+75,w-56,subtitle,23,C.muted);}
text(60,28,4600,'KNOWLEDGEBASE  /  HOW THE LOCAL MVP WORKS',52);
text(62,100,4850,'Implemented system • English UTF-8 TXT • Single user • Read 01 first, then follow the numbered workflows • Updated 2026-09-21',25,C.muted);
panel(60,160,4880,800,'01','SYSTEM AT A GLANCE','Solid arrows: requests / data flow. Dashed arrows: returned data / stream. Boxes inside the local app are modules, not separate servers.');
card(100,320,700,300,'Browser / React workspace','LibraryPanel: upload, list, delete\nChatPanel + AnswerText: ask and cite\nEvidencePanel: inspect original text\nuseLibrary / useChat: UI state\nResponsive layout + modal drawers','blue');
card(1010,320,700,300,'FastAPI / HTTP boundary','GET + POST /api/files\nDELETE /api/files/{file_id}\nPOST /api/chat or /api/chat/stream\nGET /api/conversations/{id}\nPydantic request / response schemas','blue');
card(1920,320,790,300,'Python application services','files.py: ingest, delete, recover\nchat.py: coordinate each answer\nRAG modules: resolve → retrieve →\ncontext → generate → citation check\nOwn transaction and completion rules','orange');
card(2920,320,850,300,'Provider adapters','EmbeddingClient: text / query → vector\nLLMClient: rewrite or full answer\nStreamingLLMClient: answer deltas\nOpenAI SDK clients owned by lifespan\nOnly backend reads the API key','purple');
card(4010,320,880,300,'External / OpenAI APIs','Embedding: text-embedding-3-small\nAnswer + resolver: gpt-4.1 (default)\nANSWER_MODEL can override it\nDocument text / questions / excerpts\nleave this machine for provider calls','purple');
arrow([[800,410],[1010,410]],C.blue,'HTTP',838,370);arrow([[1710,410],[1920,410]],C.orange,'service calls',1730,370);arrow([[2710,410],[2920,410]],C.purple,'model calls',2725,370);arrow([[3770,410],[4010,410]],C.purple,'HTTPS',3822,370);
arrow([[1010,560],[800,560]],C.blue,'JSON / SSE',822,585,true);
card(100,750,700,150,'Browser persistence','localStorage: conversation ID only\nSaved messages come from the API.','gray',22);
card(1010,750,700,150,'One local server','make app → built UI + API on :8000\nGET / serves frontend/dist.','gray',22);
card(1920,750,1830,150,'Local durable storage / shared storage adapters','SQLAlchemy + SQLite: file states, canonical text, messages and evidence snapshots.\nChroma: searchable vectors + chunk/file IDs. The two stores do not share a transaction.','green',24);
arrow([[2310,620],[2310,750]],C.green,'read / write',2340,664);
card(4010,750,880,150,'Other entry points','CLI and evaluation runner use the\nsame Python services (see 07).','gray',22);
// Existing Chrome sketch, retained as the familiar data-level view.
panel(60,1010,1580,1120,'02','INGESTION + RETRIEVAL DATA','Original Chrome sketch retained; service timing and failure rules are expanded in 04.','orange');
const old=JSON.parse(fs.readFileSync(path.join(dir,'original-ingestion-layout.json'),'utf8'));
if(old.length!==79)throw Error('Original scene must contain all 79 observed elements.');
for(const [type,x,y,w,h,stroke,bg,content,font,sw,end] of old){const e=base(type,x+100,y+1150,w,h,stroke,bg);e.roughness=1;e.strokeWidth=sw;e.groupIds=['original-ingestion-sketch'];if(type==='text')Object.assign(e,{text:content,originalText:content,fontSize:font,fontFamily:2,textAlign:'left',verticalAlign:'top',containerId:null,autoResize:true,lineHeight:1.3});if(['line','arrow'].includes(type))Object.assign(e,{points:content,startBinding:null,endBinding:null,startArrowhead:null,endArrowhead:end,roundness:type==='line'?{type:2}:null});}
text(100,2060,1500,'Defaults: 2048 characters / 256 overlap • cosine search • top-k 5 • only ready files',22,C.orange);
panel(1690,1010,1600,1120,'03','ONE QUESTION → ONE SAVED ANSWER','Follow the numbered arrows. History resolves references; it is not factual evidence.');
const qx=1730, qy=1160, qw=700,qh=165,qgap=115;
card(qx,qy,qw,qh,'1  Receive original question','question + conversation_id (optional)\nrequest_id correlates streamed events','blue');
card(qx+815,qy,qw,qh,'2  Load recent history','At most 10 messages from SQLite.\nNo history? Use original question.','green');
card(qx+815,qy+245,qw,qh,'3  Resolve references','query.py + LLMClient\n"that year" → standalone retrieval query','purple');
card(qx,qy+245,qw,qh,'4  Retrieve current evidence','Embed query → Chroma top-k IDs\nSQLite supplies ready-file chunk text','blue');
card(qx,qy+490,qw,qh,'5  Build the answer prompt','Original question + non-evidence hint\ncontext.py numbers excerpts [1]...[k]','orange');
card(qx+815,qy+490,qw,qh,'6  Generate and stream','generation.py + StreamingLLMClient\nUse excerpts; identify missing facts','purple');
card(qx+815,qy+735,qw,qh,'7  Check citation numbers','citations.py: known vs invalid IDs\nThis does NOT verify claim support.','orange');
card(qx,qy+735,qw,qh,'8  Save, then complete','One SQLite transaction: user + answer\n+ snapshot; emit complete after commit','green');
arrow([[qx+qw,qy+80],[qx+815,qy+80]]);arrow([[qx+1165,qy+qh],[qx+1165,qy+245]]);arrow([[qx+815,qy+325],[qx+qw,qy+325]]);arrow([[qx+350,qy+410],[qx+350,qy+490]]);arrow([[qx+qw,qy+570],[qx+815,qy+570]]);arrow([[qx+1165,qy+655],[qx+1165,qy+735]]);arrow([[qx+815,qy+815],[qx+qw,qy+815]]);
panel(3340,1010,1600,1120,'04','FILE LIFECYCLE','Upload waits for indexing; there is no background queue or worker.','orange');
card(3380,1160,440,220,'1  Validate TXT','UTF-8, nonempty .txt\nGenerate file ID.\nsplit_text preserves\ntext + source offsets.','orange');
card(3890,1160,440,220,'2  Processing','Commit file metadata\nwith processing state.\nEmbed all chunks.','orange');
card(4400,1160,500,220,'3  Ready','Save chunks, upsert vectors,\nmark ready and commit.\nReturn HTTP 201.','green');
arrow([[3820,1260],[3890,1260]],C.orange);arrow([[4330,1260],[4400,1260]],C.orange);
card(3380,1450,1520,155,'Failure during indexing','Mark Failed and attempt vector cleanup. Failed files cannot enter retrieval.\nA failed upload can be deleted; re-upload the original TXT to retry indexing.','red',24);
arrow([[4110,1380],[4110,1450]],C.red,'error',4140,1402);
card(3380,1680,715,185,'Delete: exclude first','Commit non-ready / deletion-pending\nstate before touching the vector index.\nHTTP 409 while upload is processing.','red');
card(4185,1680,715,185,'Then remove indexed content','Delete Chroma vectors → SQLite chunks\nand file record. On failure, retain a\nfailed record so Delete can retry.','red');
arrow([[4095,1770],[4185,1770]],C.red);
card(3380,1940,1520,140,'Restart recovery / exclusive owner','Acquire DATA_DIR/.owner.lock before recovery. Abandoned processing → failed → cleanup.\nReady files survive. If cleanup is interrupted, the failed record remains deletable.','green',23);
panel(60,2190,1580,1040,'05','WHAT IS STORED WHERE?','SQLite is the source of truth. Chroma supplies search candidates.','green');
card(100,2340,640,160,'files','PK file_id; name, status, error, time\nready / processing / failed','green',23);
card(920,2340,680,160,'chunks','PK chunk_id; FK file_id; original text\nindex, start_offset, end_offset','green',23);
arrow([[740,2410],[920,2410]],C.green,'1 : many',770,2370);
card(100,2600,640,160,'conversations','PK conversation_id; created_at\nParent of ordered chat messages','green',23);
card(920,2600,680,160,'messages','PK message_id; FK conversation_id\nrole, content, created_at','green',23);
arrow([[740,2670],[920,2670]],C.green,'1 : many',770,2630);
card(920,2870,680,205,'answer_snapshots','PK / FK assistant message_id\nretrieval_question; sources JSON\ncitation_check JSON\nCopied excerpts survive source deletion.','green',23);
arrow([[1260,2760],[1260,2870]],C.green,'assistant 1 : 1',1288,2792);
card(100,2870,640,205,'Chroma / persistent index','collection: knowledgebase-chunks\nvector + chunk_id + file_id\nFilter by eligible file IDs.\nNo automatic embedding function.','blue',23);
text(100,3120,1500,'database.py / models.py / operations.py / vectordb.py • Original TXT is retained as chunks, not a second disk copy.',23,C.muted);
panel(1690,2190,1600,1040,'06','FRONTEND + STREAM CONTRACT','Workspace.tsx composes the library, chat, evidence pane and responsive drawers.');
card(1730,2340,700,190,'Library state / useLibrary','api/files.ts + api/client.ts\nUpload progress, file list, deletion\nReady state enables asking questions.','blue',24);
card(2545,2340,700,190,'Chat state / useChat + reducer','api/chat.ts parses fetch response SSE\nAbortController supports Stop.\nrequest_id ignores stale events.','blue',24);
card(1730,2610,1515,155,'SSE events / api/streaming.py','start → sources → answer_delta (many) → debug → complete\nErrors produce error. EOF without complete means interrupted, not successful.','purple',25);
arrow([[2895,2530],[2895,2610]],C.purple,'decode events',2930,2550);
card(1730,2840,700,190,'Display + source inspection','ChatPanel → AnswerText citations\nEvidencePanel selects source_id\nHistorical excerpts show deleted flags.','blue',24);
card(2545,2840,700,190,'Completion + cancellation','Complete stores conversation ID locally.\nRefresh GETs saved history.\nStop leaves partial text only in UI.','blue',24);
arrow([[2080,2765],[2080,2840]],C.blue);arrow([[2895,2765],[2895,2840]],C.blue);
text(1730,3070,1515,'Commit boundary: a disconnect after commit can lose complete delivery. Existing conversations reload before retry.\nUI helpers: Modal / Icon / useMediaQuery / CSS Modules / tokens.css. Shared API types: types.ts + schemas.py.',22,C.muted);
panel(3340,2190,1600,1040,'07','STARTUP, CLI + EVALUATION','The runtime owns clients and storage; evaluation measures the same service path.','purple');
card(3380,2340,715,210,'Startup / app.py + runtime.py','Settings reads .env (never committed).\nLock data directory → init SQLite\n→ open Chroma → recover uploads\n→ create SDK clients + AppResources','green',23);
card(4185,2340,715,210,'Local development','make app: UI + API on 127.0.0.1:8000\nmake frontend: Vite on :5173\nDev proxy forwards /api to :8000.\nmake stop: release configured ports','gray',23);
card(3380,2630,715,185,'CLI / main.py → cli.py','Index TXT → interactive questions\nUses the same services and storage.\nOne owner per DATA_DIR.','orange',24);
card(4185,2630,715,185,'Evaluation / evals/evaluate.py','Frozen corpus + cases → fresh index\nanswer_question → raw answers,\nretrieved text, settings and timings','purple',24);
card(3380,2890,1520,210,'Verification and evidence boundaries','pytest + Vitest + Playwright: behavior and integration. Real-provider runs: observed answers.\nSeparate retrieval coverage, grounding, citations and abstention; valid IDs are not truth.\n25-case release: 6 qualitative issues remain. See the release report for full evidence.\nScope: local, single-user TXT/basic RAG; no authentication, PDF parser or hosted service.','gray',23);
text(60,3320,4880,'SOURCE MAP  knowledgebase/{api,services,rag,providers,storage} + frontend/src + evals  |  Implementation: abd2e47  |  Original Chrome sketch continued, not replaced by a different design.',24,C.muted);
const scene={type:'excalidraw',version:2,source:'https://excalidraw.com',elements,appState:{viewBackgroundColor:'#f8fafc',gridSize:null,zoom:{value:.25},scrollX:0,scrollY:0},files:{}};
fs.writeFileSync(path.join(out,'mvp-system-design.excalidraw'),JSON.stringify(scene,null,2)+'\n');
// A vector preview mirrors the same geometry, so it remains readable when zoomed.
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const svg=['<svg xmlns="http://www.w3.org/2000/svg" width="5000" height="3420" viewBox="0 0 5000 3420">','<rect width="5000" height="3420" fill="#f8fafc"/>','<defs><marker id="head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="context-stroke" stroke-width="1.4"/></marker></defs>'];
for(const e of elements){const attrs=`stroke="${e.strokeColor}" stroke-width="${e.strokeWidth}" fill="${e.backgroundColor==='transparent'?'none':e.backgroundColor}"`;if(e.type==='text'){svg.push(`<text x="${e.x}" y="${e.y+e.fontSize}" font-family="Arial, sans-serif" font-size="${e.fontSize}" fill="${e.strokeColor}">${e.text.split('\n').map((l,i)=>`<tspan x="${e.x}" dy="${i?e.fontSize*e.lineHeight:0}">${esc(l)}</tspan>`).join('')}</text>`);}else if(e.type==='rectangle'){svg.push(`<rect x="${e.x}" y="${e.y}" width="${e.width}" height="${e.height}" rx="${e.roundness?16:0}" ${attrs}/>`);}else if(e.type==='ellipse'){svg.push(`<ellipse cx="${e.x+e.width/2}" cy="${e.y+e.height/2}" rx="${e.width/2}" ry="${e.height/2}" ${attrs}/>`);}else{svg.push(`<polyline points="${e.points.map(([x,y])=>`${x+e.x},${y+e.y}`).join(' ')}" ${attrs} stroke-linejoin="round" ${e.strokeStyle==='dashed'?'stroke-dasharray="10 7"':''} ${e.endArrowhead?'marker-end="url(#head)"':''}/>`);}}
svg.push('</svg>');fs.writeFileSync(path.join(out,'mvp-system-design.svg'),svg.join('\n'));
fs.writeFileSync(path.join(dir,'component-bounds.json'),JSON.stringify(cardBounds,null,2)+'\n');
console.log(`Generated ${elements.length} editable elements, ${cardBounds.length} component/detail cards; retained ${old.length} original elements.`);
