const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const cors = require('cors');

// Configuração recomendada para evitar problemas com versões do WhatsApp Web
const client = new Client({
    authStrategy: new LocalAuth({
        clientId: 'main',
        // dataPath: './.wwebjs_auth' // opcional (por padrão usa .wwebjs_auth na pasta atual)
    }),
    webVersionCache: {
        type: 'remote',
        remotePath: 'https://raw.githubusercontent.com/pedroslopez/whatsapp-web.js/main/web-version.json',
    },
});

// --- HTTP Server (Express) ---
const app = express();
app.use(express.json({ limit: '1mb' }));
app.use(cors());

let isReady = false;
let isAuthenticated = false;
let lastQr = null;
let lastAuthFailure = null;
let lastDisconnectReason = null;
// Log simples de mensagens enviadas
// Array<{ ts:number, to:string, lead:{nome,endereco,telefone,site}, ok:boolean }>
const sentLog = [];

// --- Server-Sent Events (SSE) para QR e status de autenticação ---
/** @type {Set<import('http').ServerResponse>} */
const sseClients = new Set();

function writeSseEvent(res, event, data) {
    try {
        const payload = typeof data === 'string' ? data : JSON.stringify(data);
        res.write(`event: ${event}\n`);
        res.write(`data: ${payload}\n\n`);
    } catch (e) {
        // ignora write em conexões encerradas
    }
}

function broadcast(event, data) {
    for (const res of sseClients) {
        writeSseEvent(res, event, data);
    }
}

app.get('/api/whatsapp/stream', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('Access-Control-Allow-Origin', '*');
    // flush headers
    res.flushHeaders && res.flushHeaders();

    sseClients.add(res);

    // Estado inicial
    writeSseEvent(res, 'hello', { ok: true, ts: Date.now() });
    writeSseEvent(res, 'ready', isReady);
    writeSseEvent(res, 'authenticated', isAuthenticated);
    if (lastQr) {
        writeSseEvent(res, 'qr', lastQr);
    }
    if (lastAuthFailure) {
        writeSseEvent(res, 'auth_failure', lastAuthFailure);
    }
    if (lastDisconnectReason) {
        writeSseEvent(res, 'disconnected', lastDisconnectReason);
    }

    req.on('close', () => {
        sseClients.delete(res);
        try { res.end(); } catch {}
    });
});

app.get('/api/whatsapp/status', (_req, res) => {
    res.json({
        ready: isReady,
        authenticated: isAuthenticated,
        hasQr: Boolean(lastQr)
    });
});

// Retorna informações básicas do cliente autenticado
app.get('/api/whatsapp/me', async (_req, res) => {
    try {
        if (!isAuthenticated) {
            return res.status(409).json({ ok: false, error: 'not_authenticated' });
        }
        // whatsapp-web.js expõe informações em client.info
        const info = client?.info || {};
        // Campos comuns: wid, pushname, platform
        const payload = {
            ok: true,
            wid: (info && info.wid && (info.wid._serialized || info.wid.user)) || null,
            pushname: info.pushname || null,
            platform: info.platform || null,
            me: info.me || null
        };
        return res.json(payload);
    } catch (err) {
        return res.status(500).json({ ok: false, error: 'internal_error', detail: String((err && err.message) || err) });
    }
});

// Envia mensagem personalizada para um único contato
// Body: { lead: { nome, endereco, telefone, site }, message: string }
app.post('/api/send', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ ok: false, error: 'client_not_ready' });
        }
        const lead = req.body?.lead || {};
        const messageRaw = (req.body?.message || '').trim();
        const telefone = lead?.telefone;
        if (!telefone) {
            return res.status(400).json({ ok: false, error: 'missing_telefone' });
        }
        if (!messageRaw) {
            return res.status(400).json({ ok: false, error: 'missing_message' });
        }
        const jid = phoneToJid(telefone);
        const lines = [
            messageRaw,
            '',
            '— Dados da empresa —',
            lead?.nome ? `Nome: ${lead.nome}` : null,
            lead?.endereco ? `Endereço: ${lead.endereco}` : null,
            lead?.site ? `Site: ${lead.site}` : null,
            `Telefone: ${telefone}`,
        ].filter(Boolean);
        const finalMessage = lines.join('\n');
        await client.sendMessage(jid, finalMessage);
        sentLog.push({ ts: Date.now(), to: jid, lead, ok: true });
        return res.json({ ok: true, to: jid });
    } catch (err) {
        console.error('Erro em /api/send:', err);
        sentLog.push({ ts: Date.now(), to: 'unknown', lead: req.body?.lead || null, ok: false });
        return res.status(500).json({ ok: false, error: 'internal_error', detail: String((err && err.message) || err) });
    }
});

// Envio em lote: Body { leads: Lead[], message: string }
app.post('/api/send-batch', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ ok: false, error: 'client_not_ready' });
        }
        const leads = Array.isArray(req.body?.leads) ? req.body.leads : [];
        const messageRaw = (req.body?.message || '').trim();
        if (!messageRaw) {
            return res.status(400).json({ ok: false, error: 'missing_message' });
        }
        if (leads.length === 0) {
            return res.status(400).json({ ok: false, error: 'empty_leads' });
        }

        const results = [];
        for (const lead of leads) {
            const telefone = lead?.telefone;
            if (!telefone) {
                results.push({ ok: false, error: 'missing_telefone', lead });
                continue;
            }
            const jid = phoneToJid(telefone);
            const lines = [
                messageRaw,
                '',
                '— Dados da empresa —',
                lead?.nome ? `Nome: ${lead.nome}` : null,
                lead?.endereco ? `Endereço: ${lead.endereco}` : null,
                lead?.site ? `Site: ${lead.site}` : null,
                `Telefone: ${telefone}`,
            ].filter(Boolean);
            const finalMessage = lines.join('\n');
            try {
                await client.sendMessage(jid, finalMessage);
                results.push({ ok: true, to: jid, lead });
                sentLog.push({ ts: Date.now(), to: jid, lead, ok: true });
                await new Promise(r => setTimeout(r, 250));
            } catch (err) {
                results.push({ ok: false, to: jid, error: String(err && err.message || err), lead });
                sentLog.push({ ts: Date.now(), to: jid, lead, ok: false });
            }
        }

        const summary = {
            ok: true,
            total: results.length,
            sent: results.filter(r => r.ok).length,
            failed: results.filter(r => !r.ok).length,
            results
        };
        return res.json(summary);
    } catch (err) {
        console.error('Erro em /api/send-batch:', err);
        return res.status(500).json({ ok: false, error: 'internal_error', detail: String((err && err.message) || err) });
    }
});

// Estatísticas simples
app.get('/api/sent/summary', (_req, res) => {
    const total = sentLog.length;
    const sent = sentLog.filter(i => i.ok).length;
    const failed = total - sent;
    res.json({ ok: true, total, sent, failed });
});

app.get('/api/sent/log', (req, res) => {
    const limit = Math.max(1, Math.min(500, Number(req.query.limit) || 100));
    const items = sentLog.slice(-limit).reverse();
    res.json({ ok: true, items, total: sentLog.length });
});
// Estado de leads contatados via /api/landing
// Map<JID, { stage: 'sent_offer' | 'asked_optin' | 'opted_in', prospect: any, ts: number }>
const outreachState = new Map();
const SELLER_JID = '5527988033791@c.us'; // +55 27 98803-3791

client.on('qr', (qr) => {
    // Guardar e transmitir o QR para o front-end
    lastQr = qr;
    isAuthenticated = false;
    console.log('QR code recebido. Aguardando leitura no aplicativo WhatsApp.');
    // Não gerar QR no terminal; o front-end irá renderizar
    broadcast('qr', qr);
});

client.on('ready', () => {
    console.log('Client is ready!');
    isReady = true;
    broadcast('ready', true);
});

client.on('authenticated', () => {
    console.log('Authenticated. Session persisted by LocalAuth.');
    isAuthenticated = true;
    lastQr = null; // QR não é mais necessário
    broadcast('authenticated', true);
});

client.on('auth_failure', (msg) => {
    console.error('Auth failure:', msg);
    console.error('If this persists, delete .wwebjs_auth and re-scan the QR.');
    isAuthenticated = false;
    lastAuthFailure = String(msg || 'auth_failure');
    broadcast('auth_failure', lastAuthFailure);
});

client.on('disconnected', (reason) => {
    console.warn('Client was disconnected:', reason);
    // Opcional: tentar reinicializar automaticamente
    // client.initialize();
    isReady = false;
    isAuthenticated = false;
    lastDisconnectReason = String(reason || 'unknown');
    broadcast('disconnected', lastDisconnectReason);
});

function onlyDigits(str) {
    return (str || '').replace(/\D+/g, '');
}

function phoneToJid(phoneRaw) {
    let d = onlyDigits(phoneRaw);
    if (!d.startsWith('55')) {
        d = '55' + d;
    }
    return `${d}@c.us`;
}

function normalizeText(t) {
    const s = (t || '').trim().toLowerCase();
    // troca 'não' acentuado por 'nao' para facilitar matching
    return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

function isYes(text) {
    const s = normalizeText(text);
    return /\b(sim|s|quero|interessad|fechar|ok|vamos)\b/.test(s);
}

function isNo(text) {
    const s = normalizeText(text);
    return /\b(nao|n|depois|agora nao|talvez depois)\b/.test(s);
}

function buildLandingMessage(prospect) {
    const nome = prospect?.nome?.trim() || 'Olá';
    const endereco = prospect?.endereco?.trim();
    const site = (prospect?.site && String(prospect.site).trim()) || null;

    const line1 = `Olá ${nome}! 👋`;
    const line2 = endereco ? `Vi seu negócio em ${endereco}.` : `Vi seu negócio e acredito que podemos ajudar.`;
    const pitch = site
        ? `Somos especialistas em páginas de alta conversão e podemos modernizar o seu site (${site}) com desempenho, SEO e WhatsApp integrado.`
        : `Somos especialistas em páginas de alta conversão e podemos criar uma landing page moderna com desempenho, SEO e WhatsApp integrado.`;
    const cta = `Posso te enviar algumas ideias de layout e orçamento sem compromisso?`;

    return `${line1}
${line2}
${pitch}
${cta}`;
}

async function sendIntroSequence(jid, prospect) {
    const intro = [
        'Como posso te ajudar hoje?',
        '1) Falar com vendedor',
        '2) Ver planos',
        '3) Não tenho interesse',
        '',
        'Responda com 1, 2 ou 3, ou envie: "falar com vendedor", "ver planos" ou "não tenho interesse".'
    ].join('\n');
    await client.sendMessage(jid, intro);

    const existing = outreachState.get(jid) || { stage: 'sent_offer' };
    outreachState.set(jid, { ...existing, stage: 'asked_optin', prospect, ts: Date.now() });
}

async function sendPlansList(jid) {
    const text = [
        'Planos disponíveis:',
        '- Plano Básico: 1 página, formulário, WhatsApp, SEO inicial',
        '- Plano Pro: até 3 seções, SEO, analytics, otimização de conversão',
        '- Plano Premium: LP completa, copy, SEO avançado, integrações',
        '',
        'Para detalhes, responda: "plano basico", "plano pro" ou "plano premium".',
        'Para falar com um vendedor, responda: "falar com vendedor".'
    ].join('\n');
    await client.sendMessage(jid, text);
}

async function sendPlanDetails(jid, planId) {
    const details = {
        plano_basic: 'Plano Básico: LP 1 página, formulário, WhatsApp, SEO inicial. Ideal para começar rápido.',
        plano_pro: 'Plano Pro: até 3 seções, SEO, analytics, otimização de conversão. Equilíbrio custo/benefício.',
        plano_premium: 'Plano Premium: LP completa, copy, SEO avançado e integrações. Foco máximo em resultados.'
    };
    const text = details[planId] || 'Opção não reconhecida.';
    await client.sendMessage(jid, text + '\n\nDeseja falar com um vendedor agora? Responda SIM ou NAO.');
}

async function handoffToSeller(jid, contact, state) {
    const displayName = contact.pushname || contact.name || contact.number || 'Contato';
    const contactNumber = contact.number || (contact.id && contact.id.user) || 'desconhecido';
    const prospect = state?.prospect;

    await client.sendMessage(jid, `Perfeito, ${displayName}! 🙌
Vou te conectar com um vendedor para explicar preços e serviços disponíveis.
Em instantes você receberá um retorno.`);

    // Notifica vendedor com contexto
    const contextLines = [
        `Novo lead interessado em LP:`,
        `• Nome: ${displayName} (${contactNumber})`,
        `• JID: ${jid}`,
    ];
    if (prospect) {
        contextLines.push(`• Prospect: ${JSON.stringify(prospect)}`);
    }
    await client.sendMessage(SELLER_JID, contextLines.join('\n'));

    outreachState.set(jid, { ...state, stage: 'handoff_done', ts: Date.now() });
}

async function sendRandomChristmasGreetings(count = 10) {
    try {
        const contacts = await client.getContacts();
        const candidates = contacts.filter(c =>
            !c.isGroup &&
            !c.isMe &&
            (c.isMyContact || c.isWAContact) &&
            c.id && c.id._serialized
        );

        // Embaralhar (Fisher-Yates)
        for (let i = candidates.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
        }

        const selected = candidates.slice(0, Math.min(count, candidates.length));
        console.log(`Enviando Feliz Natal para ${selected.length} contato(s)...`);

        for (const c of selected) {
            const name = c.pushname || c.name || c.number || 'Amigo(a)';
            const message = `Feliz Natal, ${name}! 🎄✨
            Que seu dia seja repleto de paz, saúde e alegria.
            Abraços do nosso bot de telecomunicações!`;
            await client.sendMessage(c.id._serialized, message);
        }

        console.log('Envio de Feliz Natal concluído.');
    } catch (err) {
        console.error('Erro ao enviar mensagens de Feliz Natal:', err);
    }
}

// Rota: POST /api/landing
// Body: Array de objetos { nome, endereco, telefone, site } ou {contatos:[...]}
app.post('/api/landing', async (req, res) => {
    try {
        if (!isReady) {
            return res.status(503).json({ ok: false, error: 'WhatsApp client not ready yet' });
        }
        const body = req.body;
        const list = Array.isArray(body) ? body : Array.isArray(body?.contatos) ? body.contatos : null;
        if (!list || list.length === 0) {
            return res.status(400).json({ ok: false, error: 'Expected a non-empty array or {contatos: [...]}' });
        }

        const results = [];
        for (const item of list) {
            const telefone = item?.telefone;
            const jid = telefone ? phoneToJid(telefone) : null;
            if (!jid) {
                results.push({ input: item, ok: false, error: 'telefone inválido' });
                continue;
            }
            const message = buildLandingMessage(item);
            try {
                await client.sendMessage(jid, message);
                results.push({ input: item, ok: true, to: jid });
                // marca contato como lead aguardando opt-in
                outreachState.set(jid, { stage: 'sent_offer', prospect: item, ts: Date.now() });
                await new Promise(r => setTimeout(r, 400));

                // Envia sequência com imagem e botões após a oferta
                await sendIntroSequence(jid, item);
            } catch (err) {
                results.push({ input: item, ok: false, to: jid, error: String((err && err.message) || err) });
            }
        }

        const summary = {
            ok: true,
            sent: results.filter(r => r.ok).length,
            failed: results.filter(r => !r.ok).length,
            total: results.length,
            results,
        };
        return res.json(summary);
    } catch (err) {
        console.error('Erro na rota /api/landing:', err);
        return res.status(500).json({ ok: false, error: 'internal_error', detail: String((err && err.message) || err) });
    }
});

const PORT = process.env.PORT || 3001;
const server = app.listen(PORT, () => {
    console.log(`HTTP server listening on http://localhost:${PORT}`);
});

server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.error(`\n[ERRO] A porta ${PORT} já está em uso!`);
        console.error(`Provavelmente o servidor já está rodando em outro terminal.`);
        console.error(`Tente fechar o processo anterior ou usar outra porta.\n`);
        process.exit(1);
    } else {
        throw err;
    }
});

client.on('message', async (msg) => {
    if (!msg.body) return;

    // Comando para disparar Feliz Natal para 10 contatos aleatórios
    const lowered = msg.body.trim().toLowerCase();
    if (lowered === '!feliznatal' || lowered === 'feliz natal' || lowered === '/feliznatal') {
        sendRandomChristmasGreetings(10);
        return;
    }

    // Conversa baseada no lead enviado pela /api/landing
    try {
        const contact = await msg.getContact();
        const displayName = contact.pushname || contact.name || contact.number || 'Contato';
        const contactNumber = contact.number || (contact.id && contact.id.user) || 'desconhecido';
        const jid = contact.id && contact.id._serialized;

        // Respostas interativas (botões e listas)
        

        if (jid && outreachState.has(jid)) {
            const state = outreachState.get(jid) || { stage: 'sent_offer' };
            const text = msg.body || '';
            const choice = normalizeText(text);

            // Atalhos sem botões/listas
            if (choice === '1' || choice.includes('vendedor')) {
                await handoffToSeller(jid, contact, state);
                return;
            }
            if (choice === '2' || choice.includes('plano') || choice.includes('planos')) {
                await sendPlansList(jid);
                return;
            }
            if (choice === '3' || choice.includes('nao tenho interesse')) {
                await msg.reply(
                    `Sem problemas, ${displayName}! 😊\nSe mudar de ideia, é só me mandar "falar com vendedor".`
                );
                outreachState.delete(jid);
                return;
            }

            if (isYes(text)) {
                await handoffToSeller(jid, contact, state);
                return;
            }

            if (isNo(text)) {
                await msg.reply(
                    `Sem problemas, ${displayName}! 😊\nSe mudar de ideia, é só me mandar "SIM" que te coloco em contato com um vendedor.`
                );
                outreachState.delete(jid);
                return;
            }

            if (state.stage !== 'asked_optin') {
                await sendIntroSequence(jid, state.prospect);
                return;
            }

            // Se já perguntamos e a resposta não foi clara, reforça a instrução
            const intro = [
                'Como posso te ajudar hoje?',
                '1) Falar com vendedor',
                '2) Ver planos',
                '3) Não tenho interesse',
                '',
                'Responda com 1, 2 ou 3, ou envie: "falar com vendedor", "ver planos" ou "não tenho interesse".'
            ].join('\n');
            await client.sendMessage(jid, intro);
            return;
        }

        // fallback genérico quando não é um lead enviado pela API
        // Fluxo responsivo para inbound (não veio da API)
        const norm = normalizeText(msg.body);
        if (norm.includes('vendedor') || isYes(norm)) {
            const state = outreachState.get(jid) || { stage: 'asked_optin' };
            await handoffToSeller(jid, contact, state);
            return;
        }
        if (norm.includes('plano') || norm.includes('planos') || norm.includes('preco') || norm.includes('preço') || norm.includes('precos') || norm.includes('preços')) {
            await sendPlansList(jid);
            return;
        }
        // envia sequência interativa padrão
        await sendIntroSequence(jid, null);
        return;
    } catch (err) {
        console.error('Erro ao responder mensagem:', err);
    }
});

client.initialize();