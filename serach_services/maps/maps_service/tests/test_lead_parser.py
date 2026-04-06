from scraper.lead_parser import build_lead_messages


class TestBuildLeadMessages:
    def test_builds_messages_with_template(self):
        leads = [
            {"nome": "Pizzaria Roma", "telefone": "+55111"},
            {"nome": "Bar Central", "telefone": "+55222"},
        ]
        result = build_lead_messages(leads, "Ola {nome}, tudo bem?")

        assert len(result) == 2
        assert result[0]["lead"] == "+55111"
        assert result[0]["message"] == "Ola Pizzaria Roma, tudo bem?"
        assert result[1]["lead"] == "+55222"
        assert result[1]["message"] == "Ola Bar Central, tudo bem?"

    def test_skips_leads_without_phone(self):
        leads = [
            {"nome": "Sem Telefone", "telefone": None},
            {"nome": "Com Telefone", "telefone": "+55333"},
        ]
        result = build_lead_messages(leads, "Oi {nome}")

        assert len(result) == 1
        assert result[0]["lead"] == "+55333"

    def test_empty_leads_returns_empty(self):
        assert build_lead_messages([], "Oi {nome}") == []

    def test_message_without_placeholder(self):
        leads = [{"nome": "Test", "telefone": "+55444"}]
        result = build_lead_messages(leads, "Mensagem fixa sem variavel")

        assert result[0]["message"] == "Mensagem fixa sem variavel"

    def test_lead_with_empty_name(self):
        leads = [{"nome": "", "telefone": "+55555"}]
        result = build_lead_messages(leads, "Ola {nome}!")

        assert result[0]["message"] == "Ola !"
