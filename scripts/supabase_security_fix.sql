-- Supabase Security Fixes
-- Run in Supabase SQL Editor (Dashboard > SQL Editor)
-- Addresses linter warnings about SECURITY DEFINER functions

-- ============================================================================
-- 1. Drop and recreate functions with SECURITY INVOKER
-- ============================================================================

DROP FUNCTION IF EXISTS public.promote_channel_source(text, text, text);
DROP FUNCTION IF EXISTS public.report_channel_broken(text, text);
DROP FUNCTION IF EXISTS public.report_channel_working(text, text, integer);

-- promote_channel_source
CREATE FUNCTION public.promote_channel_source(
    p_channel_name text,
    p_working_url text,
    p_working_hash text
)
RETURNS void
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
BEGIN
    IF length(p_channel_name) > 200 OR length(p_working_url) > 500 OR length(p_working_hash) > 64 THEN
        RAISE EXCEPTION 'Input too long';
    END IF;
    UPDATE channels
    SET url = p_working_url, url_hash = p_working_hash, updated_at = now()
    WHERE name = p_channel_name;
END;
$$;

-- report_channel_broken
CREATE FUNCTION public.report_channel_broken(
    p_url_hash text,
    p_device_id text
)
RETURNS void
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
BEGIN
    IF length(p_url_hash) > 64 OR length(p_device_id) > 64 THEN
        RAISE EXCEPTION 'Input too long';
    END IF;
    INSERT INTO channel_status (url_hash, status, last_checked, report_count)
    VALUES (p_url_hash, 'broken', now(), 1)
    ON CONFLICT (url_hash)
    DO UPDATE SET status = 'broken', last_checked = now(),
        report_count = channel_status.report_count + 1;
END;
$$;

-- report_channel_working
CREATE FUNCTION public.report_channel_working(
    p_url_hash text,
    p_device_id text,
    p_response_time_ms integer DEFAULT 0
)
RETURNS void
LANGUAGE plpgsql
SECURITY INVOKER
AS $$
BEGIN
    IF length(p_url_hash) > 64 OR length(p_device_id) > 64 THEN
        RAISE EXCEPTION 'Input too long';
    END IF;
    INSERT INTO channel_status (url_hash, status, last_checked, report_count)
    VALUES (p_url_hash, 'working', now(), 0)
    ON CONFLICT (url_hash)
    DO UPDATE SET status = 'working', last_checked = now(), report_count = 0;
END;
$$;

-- Grant execute to anon (needed for client calls)
GRANT EXECUTE ON FUNCTION public.promote_channel_source(text, text, text) TO anon;
GRANT EXECUTE ON FUNCTION public.report_channel_broken(text, text) TO anon;
GRANT EXECUTE ON FUNCTION public.report_channel_working(text, text, integer) TO anon;

-- ============================================================================
-- 2. Materialized view: Revoke direct anon access, use safe view wrapper
-- ============================================================================
REVOKE SELECT ON public.mv_top_channels FROM anon;
REVOKE SELECT ON public.mv_top_channels FROM authenticated;

CREATE OR REPLACE VIEW public.v_top_channels
WITH (security_invoker = true)
AS SELECT * FROM public.mv_top_channels;

GRANT SELECT ON public.v_top_channels TO anon;
GRANT SELECT ON public.v_top_channels TO authenticated;
