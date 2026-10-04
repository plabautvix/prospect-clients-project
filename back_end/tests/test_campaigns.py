import random
from datetime import datetime, timedelta

import pytest

from prospect_clients.src.configurations.auth import SERVICE_API_KEY
from prospect_clients.src.configurations.messaging import LEASE_SECONDS, PACING
from prospect_clients.src.repositories.leads_repository import LeadsRepository
from prospect_clients.src.repositories.user_repository import UserRepository
from prospect_clients.src.services import campaigns_service
from prospect_clients.src.services.pacing import after_send, blocked_until
from prospect_clients.src.utils.phone import instagram_handle, normalize_br_mobile
from prospect_clients.src.utils.template import render_message

SERVICE = {"X-Service-Key": SERVICE_API_KEY}
WA = PACING["whatsapp"]

# 15:00 UTC is 12:00 in Sao Paulo: inside the sending window.
NOON = datetime(2026, 10, 5, 15, 0, 0)


class TestPhone:
    @pytest.mark.parametrize(
        "raw",
        ["(27) 99876-5432", "+55 27 99876-5432", "027 99876-5432", "27998765432"],
    )
    def test_mobile_formats(self, raw):
        assert normalize_br_mobile(raw) == "5527998765432"

    @pytest.mark.parametrize(
        "raw",
        [None, "", "(27) 3222-1234", "0800 123 4567", "(20) 99876-5432", "12345"],
    )
    def test_not_a_mobile(self, raw):
        assert normalize_br_mobile(raw) is None

    def test_instagram_handle(self):
        assert instagram_handle("@Padaria.Sol") == "padaria.sol"
        assert instagram_handle("Padaria Sol") is None


class TestTemplate:
    def test_placeholders(self):
        text = render_message("Oi {nome}, vi que é {categoria}.", "Sol", "padaria")
        assert text == "Oi Sol, vi que é padaria."

    def test_variations_pick_one_option(self):
        rng = random.Random(1)
        seen = {render_message("{Olá|Oi} {nome}", "Sol", None, rng) for _ in range(30)}
        assert seen == {"Olá Sol", "Oi Sol"}

    def test_a_name_is_never_read_as_a_variation(self):
        assert render_message("Oi {nome}", "A|B", None) == "Oi A|B"

    def test_unknown_placeholder_is_kept(self):
        assert render_message("Oi {nmoe}", "Sol", None) == "Oi {nmoe}"


class TestPacing:
    def test_free_inside_window(self):
        assert blocked_until(NOON, WA, None, None, sent_today=0) is None

    def test_waits_for_window_to_open(self):
        early = datetime(2026, 10, 5, 10, 0)  # 07:00 local
        assert blocked_until(early, WA, None, None, 0) == datetime(2026, 10, 5, 12, 0)

    def test_after_window_waits_for_tomorrow(self):
        late = datetime(2026, 10, 5, 23, 0)  # 20:00 local
        assert blocked_until(late, WA, None, None, 0) == datetime(2026, 10, 6, 12, 0)

    def test_daily_cap(self):
        wait = blocked_until(NOON, WA, None, None, sent_today=WA.daily_cap)
        assert wait == datetime(2026, 10, 6, 12, 0)

    def test_latest_rule_wins(self):
        gap = NOON + timedelta(seconds=40)
        pause = NOON + timedelta(hours=2)
        assert blocked_until(NOON, WA, gap, pause, 0) == pause

    def test_gap_then_long_pause_after_chunk(self):
        rng = random.Random(0)
        nxt, count = after_send(NOON, WA, 0, rng)
        assert count == 1
        assert WA.min_gap_seconds <= (nxt - NOON).total_seconds() <= WA.max_gap_seconds

        nxt, count = after_send(NOON, WA, WA.chunk_size - 1, rng)
        assert count == 0
        assert (nxt - NOON).total_seconds() >= WA.chunk_pause_min_seconds


class Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


@pytest.fixture()
def clock(monkeypatch):
    clock = Clock(NOON)
    monkeypatch.setattr(campaigns_service, "utcnow", clock)
    return clock


def _seed(client, db, email, leads):
    client.post("/users/", json={"email": email, "password": "pass"})
    token = client.post(
        "/users/login", data={"username": email, "password": "pass"}
    ).json()["access_token"]
    user = UserRepository(db).get_by_email(email)
    if leads:
        client.post(f"/leads/?user_id={user.id_person}", json=leads, headers=SERVICE)
    ids = {
        lead.nome: lead.id_lead
        for lead in LeadsRepository(db).get_all_by_user(user.id_person)
    }
    return {"Authorization": f"Bearer {token}"}, ids


MAPS_LEADS = [
    {"nome": "Padaria Sol", "telefone": "(27) 99876-5432", "categoria": "padaria"},
    {"nome": "Padaria Lua", "telefone": "(27) 3222-1234", "categoria": "padaria"},
    {"nome": "Barbearia", "telefone": None, "categoria": "barbearia"},
    {"nome": "Mesma Linha", "telefone": "27 99876-5432", "categoria": "padaria"},
    {"nome": "Mercado", "telefone": "(11) 91234-5678", "categoria": "mercado"},
]


class TestCampaignEndpoints:
    def test_preview_explains_who_is_left_out(self, client, db):
        auth, _ = _seed(client, db, "prev@test.com", MAPS_LEADS)

        response = client.post(
            "/campaigns/preview",
            json={"channel": "whatsapp", "template": "Oi {nome}", "filters": {}},
            headers=auth,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["eligible"] == 2
        assert body["skipped"]["sem_contato"] == 2  # landline and no phone
        assert body["skipped"]["duplicado"] == 1
        assert body["samples"][0] == {
            "nome": "Padaria Sol",
            "recipient": "5527998765432",
            "body": "Oi Padaria Sol",
        }

    def test_target_needs_ids_or_filters(self, client, db):
        auth, _ = _seed(client, db, "target@test.com", MAPS_LEADS)
        response = client.post(
            "/campaigns", json={"channel": "whatsapp", "template": "Oi"}, headers=auth
        )
        assert response.status_code == 422

    def test_create_stores_every_message(self, client, db, clock):
        auth, ids = _seed(client, db, "create@test.com", MAPS_LEADS)

        response = client.post(
            "/campaigns",
            json={
                "channel": "whatsapp",
                "template": "Oi {nome}",
                "lead_ids": [ids["Padaria Sol"], ids["Mercado"], ids["Barbearia"]],
            },
            headers=auth,
        )

        assert response.status_code == 201
        body = response.json()
        assert body["queued"] == 2
        assert body["skipped"]["sem_contato"] == 1
        assert body["campaign"]["counts"]["pending"] == 2
        assert body["campaign"]["name"] == "WhatsApp 05/10 12:00"

    def test_nobody_is_contacted_twice(self, client, db, clock):
        auth, ids = _seed(client, db, "twice@test.com", MAPS_LEADS)
        payload = {
            "channel": "whatsapp",
            "template": "Oi",
            "lead_ids": [ids["Padaria Sol"]],
        }
        assert client.post("/campaigns", json=payload, headers=auth).status_code == 201

        again = client.post("/campaigns", json=payload, headers=auth)

        assert again.status_code == 422

    def test_do_not_contact_is_respected(self, client, db):
        auth, ids = _seed(client, db, "dnc@test.com", MAPS_LEADS)
        client.post(
            "/leads/do-not-contact",
            json={"lead_ids": [ids["Padaria Sol"]]},
            headers=auth,
        )

        body = client.post(
            "/campaigns/preview",
            json={"channel": "whatsapp", "template": "Oi", "filters": {}},
            headers=auth,
        ).json()

        # "Mesma Linha" shares the phone, and the opt out is the person's.
        assert body["skipped"]["nao_contatar"] == 2
        assert [s["nome"] for s in body["samples"]] == ["Mercado"]

    def test_instagram_uses_the_handle(self, client, db):
        auth, _ = _seed(
            client,
            db,
            "ig@test.com",
            [
                {"nome": "@padaria.sol", "origem": "instagram"},
                {"nome": "Padaria Sol", "telefone": "(27) 99876-5432"},
            ],
        )

        body = client.post(
            "/campaigns/preview",
            json={"channel": "instagram", "template": "Oi", "filters": {}},
            headers=auth,
        ).json()

        assert body["eligible"] == 1
        assert body["samples"][0]["recipient"] == "padaria.sol"

    def test_campaigns_are_private(self, client, db, clock):
        auth, ids = _seed(client, db, "owner@test.com", MAPS_LEADS)
        other, _ = _seed(client, db, "other@test.com", [])
        created = client.post(
            "/campaigns",
            json={"channel": "whatsapp", "template": "Oi", "lead_ids": [ids["Mercado"]]},
            headers=auth,
        ).json()["campaign"]

        response = client.get(f"/campaigns/{created['id_campaign']}", headers=other)

        assert response.status_code == 404

    def test_outbox_requires_the_service_key(self, client):
        assert client.post("/outbox/whatsapp/claim").status_code == 401


def _campaign(client, db, clock, email="flow@test.com"):
    auth, ids = _seed(client, db, email, MAPS_LEADS)
    created = client.post(
        "/campaigns",
        json={"channel": "whatsapp", "template": "Oi {nome}", "filters": {}},
        headers=auth,
    ).json()
    return auth, created["campaign"]["id_campaign"]


def _claim(client):
    return client.post("/outbox/whatsapp/claim", headers=SERVICE).json()


def _report(client, message_id, outcome, error=None):
    return client.post(
        f"/outbox/messages/{message_id}/result",
        json={"outcome": outcome, "error": error},
        headers=SERVICE,
    )


class TestSending:
    def test_claim_send_and_pace(self, client, db, clock):
        auth, campaign_id = _campaign(client, db, clock)

        first = _claim(client)
        assert first["message"]["body"] == "Oi Padaria Sol"

        # One at a time: nothing else while the first is in flight.
        assert _claim(client)["message"] is None

        _report(client, first["message"]["id_message"], "sent")

        # The gap after a send is respected.
        waiting = _claim(client)
        assert waiting["message"] is None
        assert WA.min_gap_seconds <= waiting["retry_after_seconds"] <= WA.max_gap_seconds

        clock.now += timedelta(seconds=WA.max_gap_seconds + 1)
        second = _claim(client)
        assert second["message"]["body"] == "Oi Mercado"
        _report(client, second["message"]["id_message"], "sent")

        campaign = client.get(f"/campaigns/{campaign_id}", headers=auth).json()
        assert campaign["status"] == "completed"
        assert campaign["counts"]["sent"] == 2

    def test_a_crash_mid_send_does_not_lose_the_message(self, client, db, clock):
        _campaign(client, db, clock)
        lost = _claim(client)["message"]

        # The worker dies without reporting. Once the lease ends, the same
        # message is handed out again.
        clock.now += timedelta(seconds=LEASE_SECONDS + 1)
        again = _claim(client)["message"]

        assert again["id_message"] == lost["id_message"]
        assert again["attempts"] == 2

    def test_transient_error_backs_off_then_gives_up(self, client, db, clock):
        auth, campaign_id = _campaign(client, db, clock)
        message_id = _claim(client)["message"]["id_message"]

        for _ in range(2):
            _report(client, message_id, "retry", "timeout")
            clock.now += timedelta(hours=1)
            assert _claim(client)["message"]["id_message"] == message_id

        _report(client, message_id, "retry", "timeout")

        messages = client.get(
            f"/campaigns/{campaign_id}/messages",
            params={"status": "failed"},
            headers=auth,
        ).json()
        assert messages["total"] == 1
        assert messages["items"][0]["last_error"] == "timeout"

    def test_release_does_not_spend_an_attempt(self, client, db, clock):
        _campaign(client, db, clock)
        message = _claim(client)["message"]

        _report(client, message["id_message"], "release")

        assert _claim(client)["message"]["attempts"] == 1

    def test_paused_campaign_is_not_served(self, client, db, clock):
        auth, campaign_id = _campaign(client, db, clock)
        client.post(f"/campaigns/{campaign_id}/pause", headers=auth)

        assert _claim(client)["message"] is None

        client.post(f"/campaigns/{campaign_id}/resume", headers=auth)
        assert _claim(client)["message"] is not None

    def test_cancel_drops_what_has_not_gone_out(self, client, db, clock):
        auth, campaign_id = _campaign(client, db, clock)

        campaign = client.post(f"/campaigns/{campaign_id}/cancel", headers=auth).json()

        assert campaign["status"] == "cancelled"
        assert campaign["counts"] == {
            "pending": 0, "sending": 0, "sent": 0, "failed": 0, "cancelled": 2,
        }
        assert _claim(client)["message"] is None

    def test_blocked_account_pauses_the_channel(self, client, db, clock):
        auth, _ = _campaign(client, db, clock)

        client.post(
            "/outbox/whatsapp/health",
            json={"state": "blocked", "detail": "Try again later", "pause_minutes": 60},
            headers=SERVICE,
        )

        assert _claim(client)["retry_after_seconds"] == 3600
        channels = {c["channel"]: c for c in client.get("/channels", headers=auth).json()}
        assert channels["whatsapp"]["paused_until"] is not None
        assert channels["whatsapp"]["queued"] == 2

        client.post("/channels/whatsapp/unpause", headers=auth)
        assert _claim(client)["message"] is not None

    def test_new_qr_code_is_handed_to_the_worker_once(self, client, db, clock):
        auth, _ = _campaign(client, db, clock)
        disconnected = {"state": "disconnected", "qr_code": "data:image/png;base64,OLD"}
        client.post("/outbox/whatsapp/health", json=disconnected, headers=SERVICE)

        status = client.post("/channels/whatsapp/reconnect", headers=auth).json()

        # The stale code disappears from the screen right away.
        assert status["qr_code"] is None
        assert status["reconnect_pending"] is True

        first = client.post("/outbox/whatsapp/health", json=disconnected, headers=SERVICE)
        second = client.post("/outbox/whatsapp/health", json=disconnected, headers=SERVICE)
        assert first.json()["reconnect"] is True
        assert second.json()["reconnect"] is False

    def test_verification_code_is_handed_to_the_worker_once(self, client, db, clock):
        auth, _ = _campaign(client, db, clock)
        waiting = {"state": "disconnected", "detail": "Codigo", "needs_code": True}
        client.post("/outbox/instagram/health", json=waiting, headers=SERVICE)

        status = client.post(
            "/channels/instagram/verification-code", json={"code": "123 456"}, headers=auth
        ).json()
        assert status["needs_code"] is True
        assert status["code_pending"] is True

        first = client.post("/outbox/instagram/health", json=waiting, headers=SERVICE)
        second = client.post("/outbox/instagram/health", json=waiting, headers=SERVICE)
        assert first.json()["verification_code"] == "123456"
        assert second.json()["verification_code"] is None

        client.post("/outbox/instagram/health", json={"state": "ok"}, headers=SERVICE)
        instagram = client.get("/channels", headers=auth).json()[1]
        assert instagram["needs_code"] is False

    def test_qr_code_reaches_the_ui(self, client, db, clock):
        auth, _ = _campaign(client, db, clock)
        client.post(
            "/outbox/whatsapp/health",
            json={"state": "disconnected", "qr_code": "data:image/png;base64,AAA"},
            headers=SERVICE,
        )

        whatsapp = client.get("/channels", headers=auth).json()[0]

        assert whatsapp["health"] == "disconnected"
        assert whatsapp["qr_code"] == "data:image/png;base64,AAA"
        assert whatsapp["worker_online"] is True


class TestLeadsAndCampaigns:
    def test_leads_show_what_was_sent_and_can_be_filtered_by_it(self, client, db, clock):
        auth, ids = _seed(client, db, "contato@test.com", MAPS_LEADS)
        client.post(
            "/campaigns",
            json={"channel": "whatsapp", "template": "Oi", "lead_ids": [ids["Padaria Sol"], ids["Mercado"]]},
            headers=auth,
        )
        sent = _claim(client)["message"]
        _report(client, sent["id_message"], "sent")

        page = client.get("/leads/", headers=auth).json()
        contatos = {l["nome"]: l["contatos"] for l in page["items"]}
        assert contatos["Padaria Sol"][0]["channel"] == "whatsapp"
        assert contatos["Padaria Sol"][0]["status"] == "enviado"
        assert contatos["Padaria Sol"][0]["sent_at"].endswith(("Z", "+00:00"))
        assert contatos["Mercado"][0]["status"] == "na_fila"
        assert contatos["Barbearia"] == []

        def names(contato):
            items = client.get("/leads/", params={"contato": contato}, headers=auth).json()["items"]
            return sorted(l["nome"] for l in items)

        assert names("enviado") == ["Padaria Sol"]
        assert names("na_fila") == ["Mercado"]
        assert names("nao_contatado") == ["Barbearia", "Mesma Linha", "Padaria Lua"]

    def test_audience_per_category(self, client, db, clock):
        auth, ids = _seed(client, db, "audience@test.com", MAPS_LEADS)

        before = {
            c["categoria"]: c
            for c in client.get("/campaigns/audience", params={"channel": "whatsapp"}, headers=auth).json()
        }
        # padaria: Sol (mobile), Lua (landline), Mesma Linha (same phone as Sol).
        assert before["padaria"] == {"categoria": "padaria", "total": 3, "elegiveis": 1, "ja_contatados": 0}
        assert before["mercado"]["elegiveis"] == 1
        assert before["barbearia"]["elegiveis"] == 0

        client.post(
            "/campaigns",
            json={"channel": "whatsapp", "template": "Oi", "filters": {"categoria": ["padaria"]}},
            headers=auth,
        )

        after = {
            c["categoria"]: c
            for c in client.get("/campaigns/audience", params={"channel": "whatsapp"}, headers=auth).json()
        }
        assert after["padaria"]["elegiveis"] == 0
        assert after["padaria"]["ja_contatados"] == 1
        assert after["mercado"]["elegiveis"] == 1

    def test_campaign_for_leads_not_yet_contacted(self, client, db, clock):
        auth, ids = _seed(client, db, "naocontatado@test.com", MAPS_LEADS)
        client.post(
            "/campaigns",
            json={"channel": "whatsapp", "template": "Oi", "lead_ids": [ids["Padaria Sol"]]},
            headers=auth,
        )

        preview = client.post(
            "/campaigns/preview",
            json={"channel": "whatsapp", "template": "Oi", "filters": {"contato": "nao_contatado"}},
            headers=auth,
        ).json()

        assert [s["nome"] for s in preview["samples"]] == ["Mercado"]

    def test_pages_follow_a_fixed_order_and_never_overlap(self, client, db):
        leads = [{"nome": f"Lead {i:03d}", "categoria": "x"} for i in range(120)]
        auth, _ = _seed(client, db, "paging@test.com", leads)

        seen = []
        for skip in (0, 50, 100):
            page = client.get("/leads/", params={"skip": skip, "limit": 50}, headers=auth).json()
            seen += [l["id_lead"] for l in page["items"]]

        assert len(seen) == 120
        assert seen == sorted(seen)

    def test_empty_category_is_not_an_option(self, client, db):
        auth, _ = _seed(
            client, db, "emptycat@test.com",
            [{"nome": "A", "categoria": ""}, {"nome": "B", "categoria": "padaria"}],
        )
        assert client.get("/leads/categories", headers=auth).json() == ["padaria"]
