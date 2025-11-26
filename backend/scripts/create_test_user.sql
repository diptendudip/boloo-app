-- Create test user for OTP testing (OTP: 123456)
-- This user ID matches the dummy user in mobile app's AuthContext

INSERT INTO users (
    id,
    phone,
    name,
    role,
    training_reports_count,
    training_completed,
    training_mode_enabled,
    created_at
) VALUES (
    '11111111-1111-1111-1111-111111111111',
    '+919999999999',  -- Test phone number
    'Test User',
    'citizen',
    0,  -- No training reports yet
    false,  -- Training not completed
    true,  -- Training mode enabled (for AI Coach testing)
    NOW()
)
ON CONFLICT (id) DO UPDATE SET
    training_reports_count = EXCLUDED.training_reports_count,
    training_completed = EXCLUDED.training_completed,
    training_mode_enabled = EXCLUDED.training_mode_enabled;

-- Verify the user was created
SELECT id, phone, name, role, training_mode_enabled, training_reports_count
FROM users
WHERE id = '11111111-1111-1111-1111-111111111111';
