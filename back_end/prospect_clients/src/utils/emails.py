"""Text of the e-mails the app sends, in plain text and HTML."""

from html import escape


def password_reset(link: str, minutes: int) -> tuple[str, str, str]:
    """Subject, text and HTML of the "Esqueci a senha" e-mail."""
    subject = "Redefina sua senha do Prospect"
    text = (
        "Recebemos um pedido para redefinir a senha da sua conta no Prospect.\n\n"
        f"Para escolher uma nova senha, abra o link abaixo. Ele vale por {minutes} "
        "minutos e só pode ser usado uma vez:\n\n"
        f"{link}\n\n"
        "Se não foi você, ignore este e-mail: sua senha continua a mesma."
    )
    safe = escape(link, quote=True)
    # Inline styles only: most mail clients drop <style> blocks.
    html = f"""\
<div style="background:#212523;padding:32px 16px;font-family:Inter,Helvetica,Arial,sans-serif">
  <div style="max-width:480px;margin:0 auto;background:#2b2f2d;border:1px solid #3a3f3c;border-radius:16px;padding:32px;color:#ffffff">
    <div style="font-size:28px;font-weight:800;letter-spacing:-0.5px;margin-bottom:24px">
      <span style="color:#10E580">Pr</span>ospect
    </div>
    <p style="color:#D1D6D3;font-size:15px;line-height:1.6;margin:0 0 24px">
      Recebemos um pedido para redefinir a senha da sua conta. O link vale por
      {minutes} minutos e só pode ser usado uma vez.
    </p>
    <a href="{safe}" style="display:inline-block;background:#10E580;color:#000000;font-weight:600;font-size:15px;text-decoration:none;padding:12px 24px;border-radius:9999px">
      Escolher nova senha
    </a>
    <p style="color:#8a918c;font-size:13px;line-height:1.6;margin:24px 0 0">
      Se não foi você, ignore este e-mail: sua senha continua a mesma.
    </p>
  </div>
</div>
"""
    return subject, text, html
