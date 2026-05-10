# Network Fix (Jan 2026)

Problem observed
- Docker DNS (127.0.0.11) on user-defined networks was failing: container names and external hosts (api.deepseek.com) did not resolve; balancer exited on “host not found” and LLM calls timed out.

Current working setup
- Custom bridge network with static IPs: `grammar-fixed-net` (172.25.0.0/24, NAT enabled).
- Static addresses:
  - grammar-llm-01 → 172.25.0.11
  - grammar-llm-02 → 172.25.0.12
  - grammar-llm-balancer → 172.25.0.20 (port 8081 exposed)
  - grammar-llm-dev → 172.25.0.30 (port 9019 exposed)
- `extra_hosts` for all services: `api.deepseek.com:3.173.21.63` (bypasses broken DNS).
- `lb.conf` uses the fixed IPs for upstreams.
- Verified paths:
  - Host: `http://127.0.0.1:8081/health` → 200, `/v2/check` returns valid response.
  - Host dev: `http://127.0.0.1:9019/v2/check`.
  - From containers on `grammar-fixed-net`: balancer `http://172.25.0.20/v2/check`; dev `http://172.25.0.30:8000/v2/check`.

How to recreate
1) Ensure no legacy containers occupy ports/names, then:
```
docker compose down
docker compose --profile dev down
docker network rm grammar-fixed-net  # if exists
```
2) `docker compose up -d` in `deploy/load-balancer/` (creates `grammar-fixed-net` and starts 01/02/balancer).
3) (Optional) `docker compose --profile dev up -d grammar-llm-dev`.

Notes
- Static IPs + `extra_hosts` are used as a DNS bypass; if Docker DNS starts working again, upstreams/hosts can be switched back to names.
- If `api.deepseek.com` IP changes, update the `extra_hosts` entries (compose) accordingly.
