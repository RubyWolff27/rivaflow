-- Restore admin access for RubyWolff@gmail.com
UPDATE users SET is_admin = TRUE WHERE LOWER(email) = LOWER('RubyWolff@gmail.com');
