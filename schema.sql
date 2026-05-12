-- Schema per Live Advisor Dashboard
-- Eseguire UNA SOLA VOLTA nella console SQL di Supabase
-- (Project → SQL Editor → New query → incolla → Run)

CREATE TABLE IF NOT EXISTS advisors (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  meet_link TEXT NOT NULL,
  is_live BOOLEAN NOT NULL DEFAULT FALSE,
  session_started_at TIMESTAMPTZ NULL,
  last_heartbeat_at TIMESTAMPTZ NULL,
  display_order INT NOT NULL DEFAULT 0,
  last_event_source TEXT NULL,  -- 'manual' | 'extension'
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Idempotente: aggiunge le colonne anche se la tabella esisteva già
ALTER TABLE advisors ADD COLUMN IF NOT EXISTS last_event_source TEXT;
ALTER TABLE advisors ADD COLUMN IF NOT EXISTS last_heartbeat_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS consultation_sessions (
  id SERIAL PRIMARY KEY,
  advisor_id INT NOT NULL REFERENCES advisors(id) ON DELETE CASCADE,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ NULL,
  duration_seconds INT NULL,
  source TEXT NULL  -- 'manual' | 'extension'
);

ALTER TABLE consultation_sessions ADD COLUMN IF NOT EXISTS source TEXT;

CREATE INDEX IF NOT EXISTS idx_sessions_advisor_started
  ON consultation_sessions(advisor_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_sessions_started_at
  ON consultation_sessions(started_at DESC);

-- Seed iniziale: i 10 advisor del team Leone Master School
-- ON CONFLICT (name) DO NOTHING permette ri-esecuzioni sicure
INSERT INTO advisors (name, meet_link, display_order) VALUES
  ('Marvin Alessandrin',  'https://meet.google.com/yrd-rzhe-dkr', 1),
  ('Domenico Primo',      'https://meet.google.com/ifs-vwsd-skb', 2),
  ('Nora D''Ascanio',     'https://meet.google.com/igs-zcdr-kah', 3),
  ('Cristian Testa',      'https://meet.google.com/kse-eoqz-qxu', 4),
  ('Hassan Mozumber',     'https://meet.google.com/bov-xhnb-opk', 5),
  ('Roberta Scicchitano', 'https://meet.google.com/ony-skpm-bms', 6),
  ('Asma Bouchrit',       'https://meet.google.com/xmg-bmxk-xwj', 7),
  ('Mattia Primo',        'https://meet.google.com/jth-hhtk-jmn', 8),
  ('Vincenzo Meglioli',   'https://meet.google.com/urq-ufbo-sai', 9),
  ('Manuel Cuccu',        'https://meet.google.com/njy-nwue-amd', 10)
ON CONFLICT (name) DO NOTHING;
