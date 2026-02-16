-- Invalidate all existing plaintext tokens (users must re-login)
-- pgcrypto is not available on Render managed PG, so just delete instead of hashing
DELETE FROM refresh_tokens;
