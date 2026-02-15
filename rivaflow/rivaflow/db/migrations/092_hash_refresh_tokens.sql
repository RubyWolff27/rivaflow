-- Invalidate all existing plaintext refresh tokens (users must re-login)
DELETE FROM refresh_tokens;
