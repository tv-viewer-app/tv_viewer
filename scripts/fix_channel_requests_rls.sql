-- Remove dangerous anon UPDATE policy
DROP POLICY IF EXISTS "Anyone can vote" ON channel_requests;

-- Create a secure vote function instead
CREATE OR REPLACE FUNCTION vote_channel_request(p_request_id uuid, p_device_hash text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    -- Validate inputs
    IF p_request_id IS NULL OR length(p_device_hash) > 64 THEN
        RAISE EXCEPTION 'Invalid input';
    END IF;
    -- Atomic increment (no read-then-write race)
    UPDATE channel_requests SET votes = votes + 1, updated_at = now()
    WHERE id = p_request_id AND status = 'pending';
END;
$$;

GRANT EXECUTE ON FUNCTION vote_channel_request(uuid, text) TO anon;

-- Revoke direct UPDATE from anon
REVOKE UPDATE ON channel_requests FROM anon;
