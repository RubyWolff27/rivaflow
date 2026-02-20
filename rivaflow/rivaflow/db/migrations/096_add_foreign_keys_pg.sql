-- Add missing FK: groups.gym_id → gyms(id)
ALTER TABLE groups ADD CONSTRAINT fk_groups_gym_id FOREIGN KEY (gym_id) REFERENCES gyms(id) ON DELETE SET NULL;
