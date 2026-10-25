import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import test from 'node:test';
import { pathToFileURL } from 'node:url';
import config from './release.config.js';

const require = createRequire(import.meta.url);
const releaseRequire = createRequire(require.resolve('semantic-release'));

function pluginOptions(name) {
  const plugin = config.plugins.find((entry) => (Array.isArray(entry) ? entry[0] : entry) === name);
  assert.ok(plugin, `${name} must remain configured`);
  return Array.isArray(plugin) ? plugin[1] : {};
}

function context() {
  return {
    cwd: import.meta.dirname,
    env: process.env,
    logger: { log() {}, warn() {}, error() {} },
    options: { repositoryUrl: 'https://github.com/cmeister2/velatus.git' },
    lastRelease: { version: '0.1.0', gitTag: '0.1.0', gitHead: 'a'.repeat(40) },
    nextRelease: { version: '1.0.0', gitTag: '1.0.0' },
    commits: [
      { hash: 'b'.repeat(40), message: 'feat: add parallel matching\n\nCloses #123' },
      { hash: 'c'.repeat(40), message: 'fix: preserve match boundaries' },
      { hash: 'd'.repeat(40), message: 'feat: revise match output\n\nBREAKING CHANGE: match offsets use bytes' },
    ],
  };
}

test('configured release notes render features, fixes, breaking changes and links', async () => {
  const { generateNotes } = await import(pathToFileURL(releaseRequire.resolve('@semantic-release/release-notes-generator')));
  const notes = await generateNotes(pluginOptions('@semantic-release/release-notes-generator'), context());
  for (const expected of [
    /Features/, /Bug Fixes/, /BREAKING CHANGES/,
    /add parallel matching/, /preserve match boundaries/, /match offsets use bytes/,
    /compare\/0\.1\.0\.\.\.1\.0\.0/,
    /issues\/123/,
    /commit\/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/,
  ]) assert.match(notes, expected);
});

test('configured analyzer recognizes the breaking-change footer', async () => {
  const { analyzeCommits } = await import(pathToFileURL(releaseRequire.resolve('@semantic-release/commit-analyzer')));
  assert.equal(await analyzeCommits(pluginOptions('@semantic-release/commit-analyzer'), context()), 'major');
});
