// Manual MongoDB initialization (optional — indexes are also created by the backend on startup)
// Run: mongosh earthscape < database/init.js

db = db.getSiblingDB("earthscape");

// users
db.users.createIndex({ email: 1 }, { unique: true });

// climate_records — shard key candidate: { location.region: 1, timestamp: -1 }
db.climate_records.createIndex({ timestamp: -1 });
db.climate_records.createIndex({ "location.region": 1, timestamp: -1 });
db.climate_records.createIndex({ source_type: 1, timestamp: -1 });
db.climate_records.createIndex({ is_anomaly: 1 });
db.climate_records.createIndex({ is_archived: 1 });

// ingestion_logs
db.ingestion_logs.createIndex({ file_hash: 1 }, { unique: true });

// job_logs
db.job_logs.createIndex({ status: 1 });
db.job_logs.createIndex({ triggered_by: 1, started_at: -1 });

// ml_results
db.ml_results.createIndex({ model_type: 1, trained_at: -1 });

// alert_events
db.alert_events.createIndex({ acknowledged: 1, triggered_at: -1 });
db.alert_events.createIndex({ rule_id: 1 });

// support_tickets
db.support_tickets.createIndex({ submitted_by: 1, created_at: -1 });
db.support_tickets.createIndex({ status: 1 });

// revoked_tokens — TTL auto-delete at expires_at
db.revoked_tokens.createIndex({ jti: 1 }, { unique: true });
db.revoked_tokens.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });

print("EarthScape indexes created.");
