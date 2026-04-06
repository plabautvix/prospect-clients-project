const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const cors = require('cors');

const puppeteerArgs = ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'];

const client = new Client({
    authStrategy: new LocalAuth({
        clientId: 'main',
    }),
    puppeteer: {
        executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
        args: puppeteerArgs,
    },
    webVersionCache: {
        type: 'remote',
        remotePath: 'https://raw.githubusercontent.com/pedroslopez/whatsapp-web.js/main/web-version.json',
    },
});

// --- HTTP Server ---
const app = express();
app.use(express.json({ limit: '1mb' }));
app.use(cors());

let isReady = false;
let isAuthenticated = false;
let lastQr = null;
let lastAuthFailure = null;
let lastDisconnectReason = null;

// Log de mensagens enviadas: Array<{ ts, to, lead, ok }>
const sentLog = [];

// --- Server-Sent Events para QR e status de autenticação ---
/** @type {Set<import('http').ServerResponse>} */
const sseClients = new Set();

function writeSseEvent(res, event, data) {
    try {
        const payload = typeof data === 'string' ? data : JSON.stringify(data);
        res.write(`event: ${event}\n`);
        res.write(`data: ${payload}\n\n`);
    } catch (_) {}
}

function broadcast(event, data) {
    for (const res of sseClients) {
        writeSseEvent(res, event, data);
    }
}

// Stream de eventos (QR, autenticação, status)
app.get('/api/whatsapp/stream', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.flushHeaders && res.flushHeaders();

    sseClients.add(res);

    writeSseEvent(res, 'hello', { ok: true, ts: Date.now() });
    writeSseEvent(res, 'ready', isReady);
    writeSseEvent(res, 'authenticated', isAuthenticated);
    if (lastQr) writeSseEvent(res, 'qr', lastQr);
    if (lastAuthFailure) writeSseEvent(res, 'auth_failure', lastAuthFailure);
    if (lastDisconnectReason) writeSseEvent(res, 'disconnected', lastDisconnectReason);

    req.on('close', () => {
        sseClients.delete(res);
        try { res.end(); } catch (_) {}
    });
});

app.get('/api/whatsapp/status', (_req, res) => {
    res.json({ ready: isReady, authenticated: isAuthenticated, hasQr: Boolean(lastQr) });
});

app.get('/api/whatsapp/me', async (_req, res) => {
    try {
        if (!isAuthenticated) {
            return res.status(409).json({ ok: false, error: 'not_authenticated' });
        }
        const info = client?.info || {};
        return res.json({
            ok: true,
            wid: (info.wid && (info.wid._serialized || info.wid.user)) || null,
            pushname: info.pushname || null,
            platform: info.platform || null,
        });
    } catch (err) {
        return res.status(500).json({ ok: false, error: 'internal_error', detail: String(err?.message || err) });
    }
});

// Envia mensagem para um único lead
// Body: { lead: { nome, endereco, telefone, site }, message: string }
app.post('/api/send', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ ok: false, error: 'client_not_ready' });
        }
        const lead = req.body?.lead || {};
        const messageRaw = (req.body?.message || '').trim();
        const telefone = lead?.telefone;

        if (!telefone) return res.status(400).json({ ok: false, error: 'missing_telefone' });
        if (!messageRaw) return res.status(400).json({ ok: false, error: 'missing_message' });

        const jid = phoneToJid(telefone);
        const finalMessage = buildMessage(messageRaw, lead);

        await client.sendMessage(jid, finalMessage);
        sentLog.push({ ts: Date.now(), to: jid, lead, ok: true });
        return res.json({ ok: true, to: jid });
    } catch (err) {
        console.error('Erro em /api/send:', err);
        sentLog.push({ ts: Date.now(), to: 'unknown', lead: req.body?.lead || null, ok: false });
        return res.status(500).json({ ok: false, error: 'internal_error', detail: String(err?.message || err) });
    }
});

// Envia mensagens em lote
// Body: { leads: Array<{ nome, endereco, telefone, site }>, message: string }
app.post('/api/send-batch', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ ok: false, error: 'client_not_ready' });
        }
        const leads = Array.isArray(req.body?.leads) ? req.body.leads : [];
        const messageRaw = (req.body?.message || '').trim();

        if (!messageRaw) return res.status(400).json({ ok: false, error: 'missing_message' });
        if (leads.length === 0) return res.status(400).json({ ok: false, error: 'empty_leads' });

        const results = [];
        for (const lead of leads) {
            const telefone = lead?.telefone;
            if (!telefone) {
                results.push({ ok: false, error: 'missing_telefone', lead });
                continue;
            }
            const jid = phoneToJid(telefone);
            const finalMessage = buildMessage(messageRaw, lead);
            try {
                await client.sendMessage(jid, finalMessage);
                results.push({ ok: true, to: jid, lead });
                sentLog.push({ ts: Date.now(), to: jid, lead, ok: true });
                await new Promise(r => setTimeout(r, 250));
            } catch (err) {
                results.push({ ok: false, to: jid, error: String(err?.message || err), lead });
                sentLog.push({ ts: Date.now(), to: jid, lead, ok: false });
            }
        }

        return res.json({
            ok: true,
            total: results.length,
            sent: results.filter(r => r.ok).length,
            failed: results.filter(r => !r.ok).length,
            results,
        });
    } catch (err) {
        console.error('Erro em /api/send-batch:', err);
        return res.status(500).json({ ok: false, error: 'internal_error', detail: String(err?.message || err) });
    }
});

app.get('/api/sent/summary', (_req, res) => {
    const total = sentLog.length;
    const sent = sentLog.filter(i => i.ok).length;
    res.json({ ok: true, total, sent, failed: total - sent });
});

app.get('/api/sent/log', (req, res) => {
    const limit = Math.max(1, Math.min(500, Number(req.query.limit) || 100));
    res.json({ ok: true, items: sentLog.slice(-limit).reverse(), total: sentLog.length });
});

// --- Helpers ---
function onlyDigits(str) {
    return (str || '').replace(/\D+/g, '');
}

function phoneToJid(phoneRaw) {
    let d = onlyDigits(phoneRaw);
    if (!d.startsWith('55')) d = '55' + d;
    return `${d}@c.us`;
}

function buildMessage(messageRaw, lead) {
    return [
        messageRaw,
        '',
        '— Dados da empresa —',
        lead?.nome ? `Nome: ${lead.nome}` : null,
        lead?.endereco ? `Endereço: ${lead.endereco}` : null,
        lead?.site ? `Site: ${lead.site}` : null,
        lead?.telefone ? `Telefone: ${lead.telefone}` : null,
    ].filter(Boolean).join('\n');
}

// --- WhatsApp client events ---
client.on('qr', (qr) => {
    lastQr = qr;
    isAuthenticated = false;
    console.log('QR code recebido. Aguardando leitura no aplicativo WhatsApp.');
    broadcast('qr', qr);
});

client.on('ready', () => {
    console.log('Client is ready!');
    isReady = true;
    broadcast('ready', true);
});

client.on('authenticated', () => {
    console.log('Authenticated.');
    isAuthenticated = true;
    lastQr = null;
    broadcast('authenticated', true);
});

client.on('auth_failure', (msg) => {
    console.error('Auth failure:', msg);
    isAuthenticated = false;
    lastAuthFailure = String(msg || 'auth_failure');
    broadcast('auth_failure', lastAuthFailure);
});

client.on('disconnected', (reason) => {
    console.warn('Client disconnected:', reason);
    isReady = false;
    isAuthenticated = false;
    lastDisconnectReason = String(reason || 'unknown');
    broadcast('disconnected', lastDisconnectReason);
});

// --- Start ---
const PORT = process.env.PORT || 3001;
const server = app.listen(PORT, () => {
    console.log(`HTTP server listening on http://localhost:${PORT}`);
});

server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.error(`[ERRO] Porta ${PORT} já está em uso.`);
        process.exit(1);
    } else {
        throw err;
    }
});

client.initialize();
