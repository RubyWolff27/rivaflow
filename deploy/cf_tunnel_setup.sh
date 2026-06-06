#!/bin/bash
# Stage 6: create a SEPARATE staging tunnel (does not touch Groot's existing tunnel),
# route staging-api/staging.rivaflow.app -> the rivaflow containers, create DNS, emit token.
set -uo pipefail
CFT=$(grep -E '^CLOUDFLARE_API_TOKEN=|^CF_API_TOKEN=' ~/.config/PAI/.env | head -1 | cut -d= -f2-)
ACCT=57c072a2a40c3377475f075287fc2398
ZONE=6fd662ea0483cd839de42890ea8b28c4
API=https://api.cloudflare.com/client/v4
hdr=(-H "Authorization: Bearer $CFT" -H "Content-Type: application/json")

echo "== find/create tunnel rivaflow-staging =="
TID=$(curl -s "${hdr[@]}" "$API/accounts/$ACCT/cfd_tunnel?name=rivaflow-staging&is_deleted=false" | python3 -c 'import sys,json;r=json.load(sys.stdin).get("result") or [];print(r[0]["id"] if r else "")')
if [ -z "$TID" ]; then
  TID=$(curl -s "${hdr[@]}" -X POST "$API/accounts/$ACCT/cfd_tunnel" -d '{"name":"rivaflow-staging","config_src":"cloudflare"}' | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["result"]["id"] if d.get("success") else "ERR:"+str(d.get("errors")))')
fi
echo "tunnel id: $TID"
[ "${TID:0:4}" = "ERR:" ] && exit 1

echo "== set ingress (api:8000, web:80) =="
curl -s "${hdr[@]}" -X PUT "$API/accounts/$ACCT/cfd_tunnel/$TID/configurations" \
 -d '{"config":{"ingress":[{"hostname":"staging-api.rivaflow.app","service":"http://api:8000"},{"hostname":"staging.rivaflow.app","service":"http://web:80"},{"service":"http_status:404"}]}}' \
 | python3 -c 'import sys,json;d=json.load(sys.stdin);print("  ingress:",d.get("success") or d.get("errors"))'

echo "== DNS CNAMEs -> tunnel =="
for h in staging staging-api; do
  out=$(curl -s "${hdr[@]}" -X POST "$API/zones/$ZONE/dns_records" -d "{\"type\":\"CNAME\",\"name\":\"$h\",\"content\":\"$TID.cfargotunnel.com\",\"proxied\":true}")
  echo "  $h: $(echo "$out" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("ok" if d.get("success") else [e.get("message") for e in d.get("errors",[])])')"
done

echo "== fetch connector token =="
TOKEN=$(curl -s "${hdr[@]}" "$API/accounts/$ACCT/cfd_tunnel/$TID/token" | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["result"] if d.get("success") else "")')
umask 077; printf '%s' "$TOKEN" > ~/.config/PAI/rivaflow-staging-tunnel.token
echo "  token saved (len ${#TOKEN}) -> ~/.config/PAI/rivaflow-staging-tunnel.token"
echo "TID=$TID"
