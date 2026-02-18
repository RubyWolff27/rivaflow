-- Restore admin access for RubyWolff@gmail.com
UPDATE users SET is_admin = 1 WHERE LOWER(email) = LOWER('RubyWolff@gmail.com');
