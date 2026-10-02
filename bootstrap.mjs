import fs from 'node:fs';
import zlib from 'node:zlib';

const packed = fs.readFileSync(new URL('./app.gz.b64', import.meta.url), 'utf8').trim();
const source = zlib.gunzipSync(Buffer.from(packed, 'base64'));
const target = '/tmp/affilhunt-private-omega.mjs';
fs.writeFileSync(target, source);
await import('file://' + target);
