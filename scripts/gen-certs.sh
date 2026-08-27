#!/usr/bin/env bash
#
# Generates a self-signed CA and server certificates for the mosquitto and
# rabbitmq brokers, used to enable TLS between the services.
#
# Output (git-ignored):
#   certs/ca.crt                 -> CA cert distributed to the clients
#   certs/ca.key                 -> CA private key (keep secret)
#   certs/mosquitto/server.{crt,key}
#   certs/rabbitmq/server.{crt,key}
#
# Run once before `docker compose up`:
#   bash scripts/gen-certs.sh
#
# In production, replace these with certificates issued by a real CA, mounted
# at the same paths.
set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")/.." && pwd)/certs"
mkdir -p "$CERT_DIR/mosquitto" "$CERT_DIR/rabbitmq"
cd "$CERT_DIR"

# All paths passed to openssl below are relative to certs/ and config files are
# used instead of -subj, to avoid Git Bash (MSYS) path mangling on Windows.

if [ ! -f ca.crt ]; then
  cat > ca.cnf <<'EOF'
[req]
distinguished_name = dn
prompt = no
[dn]
CN = prospect-dev-ca
EOF
  openssl genrsa -out ca.key 4096
  openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -config ca.cnf -out ca.crt
  rm -f ca.cnf
  echo "CA created."
else
  echo "CA already exists, reusing ca.crt."
fi

gen_cert() {
  local name="$1"
  cat > "$name.cnf" <<EOF
[req]
distinguished_name = dn
req_extensions = ext
prompt = no
[dn]
CN = $name
[ext]
subjectAltName = DNS:$name,DNS:localhost
basicConstraints = CA:FALSE
keyUsage = digitalSignature,keyEncipherment
extendedKeyUsage = serverAuth
EOF
  openssl genrsa -out "$name/server.key" 2048
  openssl req -new -key "$name/server.key" -config "$name.cnf" -out "$name/server.csr"
  openssl x509 -req -in "$name/server.csr" -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out "$name/server.crt" -days 825 -sha256 -extfile "$name.cnf" -extensions ext
  rm -f "$name/server.csr" "$name.cnf"
  echo "Certificate for '$name' created (SAN: DNS:$name)."
}

gen_cert mosquitto
gen_cert rabbitmq

echo "Done. Certificates are in $CERT_DIR"
