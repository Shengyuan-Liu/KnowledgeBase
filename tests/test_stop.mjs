import assert from 'node:assert/strict';
import { execFile, spawn } from 'node:child_process';
import { once } from 'node:events';
import { createServer } from 'node:net';
import { promisify } from 'node:util';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const exec = promisify(execFile);
const root = fileURLToPath(new URL('../', import.meta.url));

async function listener() {
  const child = spawn(process.execPath, ['-e', `
    const server = require('node:net').createServer();
    server.listen(0, '127.0.0.1', () => console.log(server.address().port));
  `], { stdio: ['ignore', 'pipe', 'inherit'] });
  const exited = once(child, 'exit');
  const [output] = await once(child.stdout, 'data');
  return { child, exited, port: Number(output.toString().trim()) };
}

async function assertAvailable(port) {
  const server = createServer();
  server.listen(port, '127.0.0.1');
  await once(server, 'listening');
  await new Promise(resolve => server.close(resolve));
}

test('stop releases selected ports, leaves other listeners, and can run twice', async () => {
  const targets = await Promise.all([listener(), listener()]);
  const other = await listener();
  try {
    const args = ['stop', `STOP_PORTS=${targets.map(item => item.port).join(' ')}`];
    const first = await exec('make', args, { cwd: root });
    assert.match(first.stdout, /Project ports are free/);
    for (const target of targets) {
      const [, signal] = await target.exited;
      assert.equal(signal, 'SIGTERM');
      await assertAvailable(target.port);
    }
    assert.equal(other.child.exitCode, null);
    assert.equal(other.child.signalCode, null);
    process.kill(other.child.pid, 0);
    const second = await exec('make', args, { cwd: root });
    assert.match(second.stdout, /already free/);
  } finally {
    for (const { child, exited } of [...targets, other]) {
      if (child.exitCode === null && child.signalCode === null) child.kill();
      await exited;
    }
  }
});
