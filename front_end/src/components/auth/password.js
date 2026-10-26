// As mesmas regras do backend (models/schemas/user.py), para avisar antes de
// enviar. O backend continua validando.
export const PASSWORD_MIN_LENGTH = 8
const PASSWORD_MAX_BYTES = 72 // limite do bcrypt

// Mensagem do primeiro problema da senha, ou '' se estiver tudo certo.
export function passwordProblem(password, confirmation) {
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `A senha precisa ter pelo menos ${PASSWORD_MIN_LENGTH} caracteres.`
  }
  if (new TextEncoder().encode(password).length > PASSWORD_MAX_BYTES) {
    return 'A senha é longa demais. Use até 72 caracteres.'
  }
  if (password !== confirmation) {
    return 'As senhas não conferem.'
  }
  return ''
}
