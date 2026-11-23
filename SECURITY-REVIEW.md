# Security review

Date: 2026-11-23

## Findings

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|
| 1 | 🟡 MEDIUM | supabase_security.sql | 29-33 (before remediation) | Any authenticated user could insert reports directly as `verificado_ia`, bypassing the moderation/AI workflow | 9/10 |

## Remediation

- Authenticated inserts are now restricted to `estado = 'pendiente'`.
- Public report and storage reads now expose only reports in `estado = 'aprobado'`.
- Report points are constrained to the values configured for `siembra`, `residuos`, and `mantenimiento`.
- Report updates and deletions now require an authenticated entry in `public.admins`.
- Evidence uploads are restricted to the authenticated user's storage folder.
- Evidence reads are allowed only for approved reports.
- `analisar_foto` now returns manual-review fallback when Vision AI is unavailable.
- Automatic approval now requires Claude Vision AI with `cumple = true` and confidence of at least 75%.
- Evidence validation rejects undersized images and low-entropy blank/capture-like images.
- Landsat cloud masking now covers dilated cloud, cirrus, cloud, and cloud shadow bits.

## Operational requirements

Run the updated [supabase_security.sql](/Users/juanbarrios/Downloads/sombrabaq/supabase_security.sql) in the Supabase SQL editor.
Confirm that the `admins` table and `evidencias` storage bucket exist and that the existing bucket is private.
