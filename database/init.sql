CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'published',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS event_consumptions (
    id UUID PRIMARY KEY,
    event_id UUID NOT NULL,
    consumer VARCHAR(100) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    processed_at TIMESTAMP,

    CONSTRAINT fk_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_events_event_type
ON events(event_type);


CREATE INDEX IF NOT EXISTS idx_events_created_at
ON events(created_at);


CREATE INDEX IF NOT EXISTS idx_event_consumptions_event_id
ON event_consumptions(event_id);


CREATE INDEX IF NOT EXISTS idx_event_consumptions_consumer
ON event_consumptions(consumer);


CREATE INDEX IF NOT EXISTS idx_event_consumptions_status
ON event_consumptions(status);