-- Channel requests table
CREATE TABLE IF NOT EXISTS channel_requests (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    name text NOT NULL,
    url text,
    country text,
    category text,
    votes integer DEFAULT 1,
    status text DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    submitted_by text,  -- device_id hash for dedup
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- RLS: anyone can read, insert, and vote
ALTER TABLE channel_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read requests" ON channel_requests FOR SELECT USING (true);
CREATE POLICY "Anyone can insert requests" ON channel_requests FOR INSERT WITH CHECK (true);
CREATE POLICY "Anyone can vote" ON channel_requests FOR UPDATE USING (true) WITH CHECK (true);

-- Index for sorting by votes
CREATE INDEX idx_channel_requests_votes ON channel_requests(votes DESC);

-- Grant access to anon
GRANT SELECT, INSERT, UPDATE ON channel_requests TO anon;
