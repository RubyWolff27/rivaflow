-- Hash existing refresh tokens in-place using pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;
UPDATE refresh_tokens SET token = encode(digest(token, 'sha256'), 'hex');
