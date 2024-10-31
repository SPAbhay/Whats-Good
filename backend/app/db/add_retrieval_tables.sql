-- Table for tracking retrieval feedback
CREATE TABLE IF NOT EXISTS retrieval_feedback (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR NOT NULL,
    brand_id INTEGER NOT NULL,
    strategy VARCHAR NOT NULL,
    is_relevant BOOLEAN NOT NULL,
    feedback_type VARCHAR NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for strategy weights by industry
CREATE TABLE IF NOT EXISTS strategy_weights (
    id SERIAL PRIMARY KEY,
    industry VARCHAR NOT NULL,
    hyde_weight FLOAT DEFAULT 0.6,
    self_query_weight FLOAT DEFAULT 0.4,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_feedback_brand_id ON retrieval_feedback(brand_id);
CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON retrieval_feedback(timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS idx_weights_industry ON strategy_weights(industry);