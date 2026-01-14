# RapidAPI Requirements and Fit (UK Property Pulse API)

This is a condensed checklist based on RapidAPI provider docs in `RapidAPI_Docs/`.

## 1) Security and traffic control

Rapid Runtime (RapidAPI proxy) adds headers to every request:
- `X-RapidAPI-Host`
- `X-RapidAPI-Key`
- `X-RapidAPI-Proxy-Secret` (recommended for provider-side verification)

Provider guidance:
- Validate `X-RapidAPI-Proxy-Secret` server-side to block non-Rapid traffic.
- Optionally allowlist Rapid Runtime IPs at the firewall.

Project status:
- By default the API is open (no auth).
- A server-side gate is now available via `RAPIDAPI_PROXY_SECRET`.
  - When set, all endpoints except `/` and `/health` require
    `X-RapidAPI-Proxy-Secret` to match.
  - On mismatch, API returns `403 rapidapi proxy secret required`.

Actions:
- Get the proxy secret from RapidAPI Security tab.
- Set `RAPIDAPI_PROXY_SECRET` in production `.env`.
- (Optional) allowlist Rapid Runtime IPs at the firewall or Cloudflare.

## 2) OpenAPI and docs

RapidAPI expects an OpenAPI document. Key points:
- `info.title`, `info.description`, `info.version` are used for listing fields.
- `info.termsOfService` is supported and recommended.
- Remote `$ref` is not supported. Local `$ref` only.
- Importing an OAS with security policy applies it at project level.

Project status:
- OpenAPI 3.1 available at `/openapi.json`.
- Title/description updated to "UK Property Pulse API".
- Terms of service not yet set in OpenAPI.

Actions:
- Add `info.termsOfService` (and optionally `contact` and `license`).

## 3) Hub Listing (Studio tabs)

General Tab:
- Logo, category, short/long description, website, terms of use.
Docs Tab:
- Markdown README for the listing "About" page.
Definitions Tab:
- Endpoint groups, upload updated OAS, configure security schemes.
Gateway Tab:
- Runtime settings, proxy secret, request limits, threat protection.
Monetize Tab:
- Plans (BASIC/PRO/ULTRA/MEGA), pricing, rate limits.

Project status:
- Listing content can be added in Rapid Studio after publish.
- No additional auth schemes required.

## 4) Monetization and payouts

RapidAPI marketplace:
- Default BASIC plan exists; free with request quota.
- Marketplace fee is 25%.
- Payouts are via PayPal only.

## 5) GDPR / privacy / IP

Rapid is a data processor under GDPR. DPA available via Rapid.
IP violations are handled via Rapid's IP enforcement process.

Project status:
- API returns aggregated statistics only (no address-level data).
- Low privacy risk compared to raw data APIs.

## 6) Current readiness summary

Ready:
- HTTPS, public base URL, health endpoint.
- OpenAPI 3.1 document.
- Aggregated-only responses (no PII).

To do:
1) Set `RAPIDAPI_PROXY_SECRET` in production.
2) Add terms of service URL (and optionally contact/license) in OpenAPI.
3) Add Hub listing content (logo, short/long description, README).
