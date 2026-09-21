import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {parse} from 'acorn';
const output = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../materials/deepseek');
const sha256 = value => createHash('sha256').update(value).digest('hex');

export function renderNode(node) {
  const content = (node.children || []).map(renderNode).join('');
  switch (node.type) {
    case 'text': return node.value;
    case 'inlineCode': return '`' + node.value + '`';
    case 'strong': return '**' + content + '**';
    case 'emphasis': return '*' + content + '*';
    case 'link': return '[' + content + '](' + node.url + ')';
    case 'paragraph': return content + '\n\n';
    case 'listItem': return content.trim();
    case 'list': return node.children.map((child, i) => (node.ordered ? `${(node.start || 1)+i}. ` : '- ') + renderNode(child).replace(/\n/g, '\n    ')).join('\n') + '\n\n';
    default: throw new Error(`Unimplemented FAQ node: ${node.type}`);
  }
}

export function extractFaq(script) {
  let data;
  // Parse the public bundle as data; never execute downloaded JavaScript.
  function walk(node) {
    if (!node || typeof node !== 'object') return;
    if (node.type === 'Literal' && typeof node.value === 'string' && node.value.startsWith('{"zh":{"categories"')) data = JSON.parse(node.value);
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) value.forEach(walk);
      else if (value && typeof value === 'object') walk(value);
    }
  }
  walk(parse(script, {ecmaVersion:'latest'}));
  return data.en.categories.find(category => category.id === '4').questions;
}

async function capture() {
  const get = url => execFileSync('curl', ['--fail','--silent','--show-error','--location','--max-time','45',url]).toString();
  const landing = 'https://static.deepseek.com/faq/index.html?lang=en';
  const html = get(landing);
  const bundle = html.match(/src="(https:\/\/static.deepseek.com\/faq\/static\/main\.[^"]+\.js)"/)[1];
  const script = get(bundle);
  const fetched_at = new Date().toISOString();
  const manifestPath = path.join(output,'manifest.json');
  const manifest = JSON.parse(await fs.readFile(manifestPath,'utf8'));
  manifest.documents = manifest.documents.filter(doc => doc.section !== 'faq-api');
  const questions = extractFaq(script);
  for (const question of questions) {
    const id = `faq-api/${question.id}`;
    const source_url = `${landing}#/question/${question.id}`;
    const body = question.answer.map(renderNode).join('').trim();
    const text = `# ${question.title}\n\nSource: ${source_url}\nCaptured: ${fetched_at}\n\n${body}\n`;
    const file = `md/${id}.md`, txt_file = `txt/faq-api__${question.id}.txt`;
    for (const name of [file,txt_file]) {
      await fs.mkdir(path.dirname(path.join(output,name)),{recursive:true});
      await fs.writeFile(path.join(output,name),text);
    }
    manifest.documents.push({id,title:question.title,source_url,fetched_at,file,txt_file,
      bytes:Buffer.byteLength(text),characters:[...text].length,sha256:sha256(text),
      bundle_sha256:sha256(script),bundle_url:bundle,section:'faq-api',historical:false,images:[],internal_links:[]});
  }
  manifest.external_faq = {landing_url:landing,category:'4',language:'en',question_count:questions.length,bundle_url:bundle,bundle_sha256:sha256(script),fetched_at,
    extraction:'English API category Markdown AST embedded in official FAQ JavaScript. Login, consumer-chat, and user-guide categories excluded.'};
  manifest.documents.sort((a,b)=>a.id.localeCompare(b.id));
  await fs.writeFile(manifestPath,JSON.stringify(manifest,null,2)+'\n');
  console.log(`Captured ${questions.length} API FAQ documents; ${manifest.documents.length} documents total.`);
}
if (process.argv[1] === fileURLToPath(import.meta.url)) await capture();
