const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');

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

let isReady = false;
// Estado de leads contatados via /api/landing
// Map<JID, { stage: 'sent_offer' | 'asked_optin' | 'opted_in', prospect: any, ts: number }>
const outreachState = new Map();
const SELLER_JID = '5527988033791@c.us'; // +55 27 98803-3791

// Exibir o QR no terminal em formato de "imagem" (ASCII)
client.on('qr', (qr) => {
    console.log('QR RECEIVED, scan the code below:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('Client is ready!');
    isReady = true;
});

client.on('authenticated', () => {
    console.log('Authenticated. Session persisted by LocalAuth.');
});

client.on('auth_failure', (msg) => {
    console.error('Auth failure:', msg);
    console.error('If this persists, delete .wwebjs_auth and re-scan the QR.');
});

client.on('disconnected', (reason) => {
    console.warn('Client was disconnected:', reason);
    // Opcional: tentar reinicializar automaticamente
    // client.initialize();
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

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`HTTP server listening on http://localhost:${PORT}`);
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