-- Fix: restore SECURITY DEFINER for channel report functions
-- They need to bypass RLS to update channel_status
DROP FUNCTION IF EXISTS public.report_channel_working(text, text, integer);
DROP FUNCTION IF EXISTS public.report_channel_broken(text, text);

CREATE FUNCTION public.report_channel_working(
    p_url_hash text, p_device_id text, p_response_time_ms integer DEFAULT 0
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    IF length(p_url_hash) > 64 OR length(p_device_id) > 64 THEN
        RAISE EXCEPTION 'Input too long';
    END IF;
    INSERT INTO channel_status (url_hash, status, last_checked, report_count)
    VALUES (p_url_hash, 'working', now(), 0)
    ON CONFLICT (url_hash) DO UPDATE
    SET status = 'working', last_checked = now(), report_count = 0;
END;
$$;

CREATE FUNCTION public.report_channel_broken(
    p_url_hash text, p_device_id text
) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    IF length(p_url_hash) > 64 OR length(p_device_id) > 64 THEN
        RAISE EXCEPTION 'Input too long';
    END IF;
    INSERT INTO channel_status (url_hash, status, last_checked, report_count)
    VALUES (p_url_hash, 'broken', now(), 1)
    ON CONFLICT (url_hash) DO UPDATE
    SET status = 'broken', last_checked = now(),
        report_count = channel_status.report_count + 1;
END;
$$;

GRANT EXECUTE ON FUNCTION public.report_channel_working(text, text, integer) TO anon;
GRANT EXECUTE ON FUNCTION public.report_channel_broken(text, text) TO anon;
