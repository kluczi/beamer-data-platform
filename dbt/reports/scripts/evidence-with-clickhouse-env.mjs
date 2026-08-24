import { spawn } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const reportRoot = path.resolve(scriptDir, '..');
const projectRoot = path.resolve(reportRoot, '..', '..');

function parseDotenv(contents) {
    const env = {};

    for (const line of contents.split(/\r?\n/)) {
        const trimmed = line.trim();

        if (!trimmed || trimmed.startsWith('#')) {
            continue;
        }

        const equalsIndex = trimmed.indexOf('=');

        if (equalsIndex === -1) {
            continue;
        }

        const key = trimmed.slice(0, equalsIndex).trim();
        let value = trimmed.slice(equalsIndex + 1).trim();

        if (
            (value.startsWith('"') && value.endsWith('"')) ||
            (value.startsWith("'") && value.endsWith("'"))
        ) {
            value = value.slice(1, -1);
        }

        env[key] = value;
    }

    return env;
}

function loadEnvFile(filePath) {
    if (!existsSync(filePath)) {
        return;
    }

    const parsed = parseDotenv(readFileSync(filePath, 'utf8'));

    for (const [key, value] of Object.entries(parsed)) {
        process.env[key] ??= value;
    }
}

loadEnvFile(path.join(projectRoot, '.env'));
loadEnvFile(path.join(reportRoot, '.env'));

process.env.EVIDENCE_SOURCE__beamer_clickhouse__username ??= process.env.CLICKHOUSE_USER;
process.env.EVIDENCE_SOURCE__beamer_clickhouse__password ??= process.env.CLICKHOUSE_PASSWORD;
process.env.EVIDENCE_SOURCE__beamer_clickhouse__url ??=
    `http://${process.env.CLICKHOUSE_HOST ?? '127.0.0.1'}:${process.env.CLICKHOUSE_PORT ?? '8123'}/${process.env.CLICKHOUSE_DB ?? 'beamer_warehouse'}`;

const evidenceCli = path.join(reportRoot, 'node_modules', '@evidence-dev', 'evidence', 'cli.js');
const child = spawn(process.execPath, [evidenceCli, ...process.argv.slice(2)], {
    cwd: reportRoot,
    env: process.env,
    stdio: 'inherit',
});

child.on('exit', (code, signal) => {
    if (signal) {
        process.kill(process.pid, signal);
    }

    process.exit(code ?? 1);
});
