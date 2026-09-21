import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { load } from 'cheerio';
import TurndownService from 'turndown';
import { gfm } from 'turndown-plugin-gfm';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const output = path.join(root, 'materials/deepseek');
const origin = 'https://api-docs.deepseek.com';
const sha256 = data => createHash('sha256').update(data).digest('hex');

function normalizeWhitespace(markdown) {
  let code = false;
  return markdown.split('\n').map(line => {
    if (/^```/.test(line)) code = !code;
    if (!code && / {2,}$/.test(line) && line.trim()) return line.trimEnd() + '<br>';
    return line.trimEnd();
  }).join('\n');
}

export function extract(html, url) {
  const $ = load(html);
  const main = $('.theme-doc-markdown').first().length ? $('.theme-doc-markdown').first() : $('main').first();
  if (!main.length) throw new Error(`No document body: ${url}`);
  const title = main.find('h1').first().text() || $('title').text().replace(/\s*\|.*$/, '');
  const links = [...new Set($('a[href]').map((_, a) => new URL($(a).attr('href'), url).href).get())];
  const images = main.find('img').map((_, n) => ({alt: $(n).attr('alt') || '', url: new URL($(n).attr('src'), url).href})).get();
  main.find('nav, script, style, svg, button, .hash-link, .theme-doc-toc-mobile').remove();
  // Keep every server-rendered language tab, including panels hidden by the UI.
  main.find('[role="tablist"]').remove();
  main.find('pre').each((_, pre) => {
    const code = $(pre).find('code').first();
    const lines = code.find('.token-line');
    const text = lines.length ? lines.map((_, n) => $(n).text()).get().join('\n') : code.text() || $(pre).text();
    const language = ($(pre).attr('class') || '').match(/language-([\w-]+)/)?.[1] || '';
    $(pre).empty().append($('<code>').attr('class', `language-${language}`).text(text));
  });
  main.find('a[href]').each((_, n) => $(n).attr('href', new URL($(n).attr('href'), url).href));
  main.find('img[src]').each((_, n) => $(n).attr('src', new URL($(n).attr('src'), url).href));
  const converter = new TurndownService({headingStyle: 'atx', codeBlockStyle: 'fenced', bulletListMarker: '-'});
  converter.use(gfm);
  converter.addRule('strong-blocks', {filter: ['strong', 'b'], replacement: (content, node) => node.querySelector('table') ? `\n\n${content.trim()}\n\n` : `**${content.trim().replace(/\s*\n+\s*/g, ' ')}**`});
  converter.addRule('complete-tables', {filter: 'table', replacement: (_, table) => {
    const grid = [];
    for (const [r, row] of Array.from(table.querySelectorAll('tr')).entries()) {
      grid[r] ||= [];
      let c = 0;
      for (const cell of Array.from(row.children).filter(n => ['TD','TH'].includes(n.nodeName))) {
        while (grid[r][c] !== undefined) c++;
        const text = converter.turndown(cell.innerHTML).trim().replace(/\n+/g, '<br>').replace(/\|/g, '&#124;');
        const rows = Number(cell.getAttribute('rowspan') || 1), cols = Number(cell.getAttribute('colspan') || 1);
        for (let y = r; y < r + rows; y++) {
          grid[y] ||= [];
          for (let x = c; x < c + cols; x++) grid[y][x] = text;
        }
        c += cols;
      }
    }
    const width = Math.max(...grid.map(row => row.length));
    const lines = grid.map(row => '| ' + Array.from({length:width},(_,i)=>row[i] || '').join(' | ') + ' |');
    lines.splice(1,0,'| '+Array(width).fill('---').join(' | ')+' |');
    return '\n\n'+lines.join('\n')+'\n\n';
  }});
  // Translate only the two Chinese descriptions in the English JSON example.
  const body = normalizeWhitespace(converter.turndown(main.html())).replace(/\u200b/g, '').replace(/\n{3,}/g, '\n\n')
    .replace(/\u53ef\u4ee5\u662f\u7535\u5b50\u90ae\u4ef6\u5730\u5740/g, 'Can be an email address')
    .replace(/\u621611\u4f4d\u624b\u673a\u53f7\u7801/g, 'Or an 11-digit mobile phone number')
    .replace(/^Loading\.\.\.$/gm, '').replace(/^#{1,6}[ \t]*$/gm, '').replace(/\n{3,}/g, '\n\n').trim();
  if (!body) throw new Error(`Empty document: ${url}`);
  return {title, body: (body.startsWith('# ') ? '' : `# ${title}\n\n`) + body, links, images};
}

function canonical(value) {
  const url = new URL(value);
  if (url.origin !== origin || /^\/(zh|zh-cn|zh-CN)(\/|$)/.test(url.pathname)) return null;
  if (/\.[a-z0-9]+$/i.test(url.pathname)) return null;
  return origin + (url.pathname.replace(/\/$/, '') || '/');
}

async function capture() {
  await fs.mkdir(output, {recursive: true});
  const get = url => execFileSync('curl', ['--fail', '--silent', '--show-error', '--location', '--max-time', '45', url]);
  const sitemap = get(`${origin}/sitemap.xml`);
  await fs.writeFile(path.join(output, 'sitemap.xml'), sitemap);
  const initial = [...new Set([...sitemap.toString().matchAll(/<loc>(.*?)<\/loc>/g)].map(m => canonical(m[1])).filter(Boolean))].sort();
  const queue = [...initial];
  const seen = new Set(queue);
  const documents = [];
  const failures = [];
  const exclusions = [];
  for (let i = 0; i < queue.length; i++) {
    const url = queue[i];
    if (url === `${origin}/prompt-library`) {
      exclusions.push({url, reason: 'Chinese-only client-rendered prompt-library landing page; outside the English documentation corpus.'});
      continue;
    }
    try {
      const cached = `/tmp/knowledgebase-deepseek-html/${(new URL(url).pathname.slice(1) || 'index').replaceAll('/', '__')}.html`;
      const html = process.argv.includes('--cached') ? await fs.readFile(cached) : get(url);
      await fs.mkdir('/tmp/knowledgebase-deepseek-html', {recursive:true});
      if (!process.argv.includes('--cached')) await fs.writeFile(cached, html);
      const {title, body, links, images} = extract(html.toString(), url);
      const fetched_at = (await fs.stat(cached)).mtime.toISOString();
      const slug = new URL(url).pathname.slice(1) || 'index';
      const file = `md/${slug}.md`;
      const txt_file = `txt/${slug.replaceAll('/', '__')}.txt`;
      const text = `${body.split('\n')[0]}\n\nSource: ${url}\nCaptured: ${fetched_at}\n\n${body.split('\n').slice(1).join('\n').trim()}\n`;
      for (const name of [file, txt_file]) {
        await fs.mkdir(path.dirname(path.join(output, name)), {recursive:true});
        await fs.writeFile(path.join(output, name), text);
      }
      const discovered = links.map(canonical).filter(Boolean);
      for (const link of discovered) if (!seen.has(link)) {seen.add(link); queue.push(link);}
      documents.push({id: slug, title, source_url: url, fetched_at, file, txt_file,
        bytes: Buffer.byteLength(text), characters: [...text].length, sha256: sha256(text),
        html_sha256: sha256(html), body_sha256: sha256(body), images, internal_links: [...new Set(discovered)],
        section: slug.includes('/') ? slug.split('/')[0] : 'overview',
        historical: slug.startsWith('news/') || slug === 'updates' || slug === 'guides/comparison_testing'});
      console.log(`${documents.length}: ${slug} (${Buffer.byteLength(text)} bytes)`);
    } catch (error) {failures.push({url, error: error.message}); console.error(`FAILED: ${url}`);}
  }
  documents.sort((a,b) => a.id.localeCompare(b.id));
  const uniqueBodies = new Map();
  for (const doc of documents) {
    if (uniqueBodies.has(doc.body_sha256)) doc.duplicate_of = uniqueBodies.get(doc.body_sha256);
    else uniqueBodies.set(doc.body_sha256, doc.id);
  }
  const manifest = {corpus_id: 'deepseek-docs-2026-09-21', source_root: `${origin}/`, captured_at: new Date().toISOString(),
    language: 'en', extraction: 'Full server-rendered document body, all language tabs, absolute links, fenced code and expanded table cells; navigation removed. Images are linked and inventoried, not OCR-transcribed. Two Chinese JSON example descriptions in guides/tool_calls are translated into English.',
    offset_unit: 'Unicode code points, zero-based half-open; compatible with Python str slicing',
    sitemap_url: `${origin}/sitemap.xml`, sitemap_sha256: sha256(sitemap), sitemap_urls: initial,
    discovered_urls: [...seen].sort(), exclusions, failures, documents};
  await fs.writeFile(path.join(output, 'manifest.json'), JSON.stringify(manifest,null,2)+'\n');
  if (failures.length) throw new Error(`${failures.length} capture failures; inspect manifest`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) await capture();
