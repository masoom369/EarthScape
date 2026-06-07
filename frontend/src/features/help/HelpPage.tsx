import ReactMarkdown from "react-markdown";
import PageHeader from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";

const HELP_MD = `
## Getting Started

### Login and Session Management
Sign in at the login page using your email and password. Your session is stored in a secure httpOnly cookie and expires after 60 minutes of inactivity. Click **Logout** in the top-right corner to end your session immediately.

Default credentials for first run: \`admin@earthscape.local\` / \`Admin123!\`

---

## Data Ingestion

### Uploading a Dataset
1. Navigate to **Ingest Data** in the sidebar (Analyst or Admin only).
2. Select the **Source Type** — Weather Station, Satellite, or Sensor.
3. Drag and drop a file into the upload zone, or click to browse.
4. Supported formats: **CSV**, **JSON**, **GeoJSON** — max 50 MB per file.
5. The ingestion log table below updates automatically after upload.

**Duplicate detection:** Files with the same content (SHA-256 hash) are rejected automatically.

### Monitoring Ingestion Status
Each upload creates a log entry with status **pending → success / failed**. Expand any log row to see the HDFS path and record count.

---

## Jobs

### Triggering a MapReduce Job
1. Go to **Jobs** in the sidebar.
2. Fill in the job name, HDFS input path (e.g. \`/earthscape/raw/weather_station/...\`), and select job type.
3. Available job types:
   - **Temperature Aggregation** — min / max / mean per region
   - **Precipitation Totals** — monthly totals per region
   - **Anomaly Scores** — Z-score based per-record anomaly rating
4. Click **Submit MapReduce Job**. The status column updates every 5 seconds.

### Triggering ML Model Training
1. Select a model type from the dropdown:
   - **Anomaly Detection** (Isolation Forest, last 90 days)
   - **Trend Prediction** (Linear Regression, last 365 days, 30-day forecast)
   - **Correlation Analysis** (Pearson matrix, last 365 days)
2. Click **Start Training**. Results appear on the Dashboard charts automatically.

---

## Alerts

### Configuring Alert Rules (Admin only)
1. Go to **Alerts** and click **New Rule**.
2. Choose a metric, comparison operator, threshold value, and severity.
3. The rule evaluates against every incoming sensor record in real time.
4. Rules can be enabled, disabled, or deleted from the rules table.

### Acknowledging Alert Events
Any authenticated user can acknowledge an alert event. Click **Ack** on any pending event to remove it from the notifications panel.

---

## Support

### Submitting a Ticket
1. Go to **Support** and click **New Ticket**.
2. Fill in the subject, a detailed description, and optionally a screenshot URL.
3. Track the status (Open → In Progress → Resolved) in the ticket list.

### Admin Response
Admins can respond to any ticket via the **Respond** button, update the status, and add a written response visible to the submitting user.

---

## Tips

- The **Dashboard** auto-refreshes in real time — no manual reload needed.
- Use the **Climate Explorer** filter bar to narrow large datasets before exporting.
- CSV exports are capped at **10,000 records** per request. Apply filters to stay under the cap.
- The live feed panel in the dashboard shows the 10 most recent sensor readings.
`;

export default function HelpPage() {
  return (
    <div className="space-y-6 animate-fade-up max-w-3xl">
      <PageHeader title="Help" description="User guide for the EarthScape platform" />
      <Card>
        <article
          className="prose prose-sm max-w-none"
          style={
            {
              "--tw-prose-body": "var(--text-primary)",
              "--tw-prose-headings": "var(--text-primary)",
              "--tw-prose-lead": "var(--text-secondary)",
              "--tw-prose-links": "var(--brand-500)",
              "--tw-prose-bold": "var(--text-primary)",
              "--tw-prose-code": "var(--brand-400)",
              "--tw-prose-hr": "var(--border-subtle)",
              "--tw-prose-quotes": "var(--text-secondary)",
              "--tw-prose-quote-borders": "var(--brand-500)",
              "--tw-prose-captions": "var(--text-tertiary)",
              "--tw-prose-counters": "var(--text-tertiary)",
              "--tw-prose-bullets": "var(--brand-500)",
              "--tw-prose-th-borders": "var(--border-default)",
              "--tw-prose-td-borders": "var(--border-subtle)",
            } as React.CSSProperties
          }
        >
          <ReactMarkdown>{HELP_MD}</ReactMarkdown>
        </article>
      </Card>
    </div>
  );
}