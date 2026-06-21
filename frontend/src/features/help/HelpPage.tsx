import {
  Rocket, Upload, Cpu, Bell, MessageSquare, Lightbulb,
  ChevronRight,
} from "lucide-react";
import PageHeader from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";

interface HelpItem {
  label: string;
  text: React.ReactNode;
}

interface HelpSection {
  id: string;
  icon: React.ReactNode;
  title: string;
  items: HelpItem[];
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <code
      className="px-1.5 py-0.5 rounded text-xs"
      style={{
        background: "var(--bg-base)",
        border: "1px solid var(--border-default)",
        color: "var(--brand-500)",
        fontFamily: "var(--font-mono)",
      }}
    >
      {children}
    </code>
  );
}

function B({ children }: { children: React.ReactNode }) {
  return (
    <strong style={{ color: "var(--text-primary)", fontWeight: 600 }}>{children}</strong>
  );
}

// Subsection grouping (Uploading vs Monitoring, MapReduce vs ML, etc.) is now
// flattened into a single ordered item list per section. The uppercase
// tracked-letter sub-headers and their border-bottom dividers are gone —
// per request, no internal section chrome, just a flowing list of points.
const SECTIONS: HelpSection[] = [
  {
    id: "getting-started",
    icon: <Rocket size={18} />,
    title: "Getting Started",
    items: [
      {
        label: "Signing in",
        text: (
          <>
            Sign in at the login page using your email and password. Your session is
            stored in a secure httpOnly cookie and expires after 60 minutes of
            inactivity. Click <B>Logout</B> in the top-right corner to end your session
            immediately.
          </>
        ),
      },
      {
        label: "Default credentials",
        text: (
          <>
            First run only: <Kbd>admin@earthscape.com</Kbd> / <Kbd>Admin123!</Kbd>
          </>
        ),
      },
    ],
  },
  {
    id: "ingestion",
    icon: <Upload size={18} />,
    title: "Data Ingestion",
    items: [
      { label: "Step 1", text: <>Navigate to <B>Ingest Data</B> in the sidebar (Analyst or Admin only).</> },
      { label: "Step 2", text: <>Select the <B>Source Type</B> — Weather Station, Satellite, or Sensor.</> },
      { label: "Step 3", text: "Drag and drop a file into the upload zone, or click to browse." },
      { label: "Formats", text: <>Supported: <B>CSV</B>, <B>JSON</B>, <B>GeoJSON</B> — max 50 MB per file.</> },
      { label: "Duplicate detection", text: "Files with the same content (SHA-256 hash) are rejected automatically." },
      {
        label: "Status flow",
        text: (
          <>
            Each upload creates a log entry: <Kbd>pending</Kbd> → <Kbd>success</Kbd> /{" "}
            <Kbd>failed</Kbd>. Expand any log row to see the HDFS path and record count.
          </>
        ),
      },
    ],
  },
  {
    id: "jobs",
    icon: <Cpu size={18} />,
    title: "Jobs",
    items: [
      { label: "Step 1", text: <>Go to <B>Jobs</B> in the sidebar.</> },
      {
        label: "Step 2",
        text: (
          <>
            Select a job type first, then choose an input file — only files matching
            that job type&apos;s required format (CSV or JSON) are shown.
          </>
        ),
      },
      {
        label: "Job types",
        text: (
          <div className="space-y-1.5 mt-1">
            <div><B>Temperature Aggregation</B> (CSV) — min / max / mean per region</div>
            <div><B>Precipitation Totals</B> (CSV) — monthly totals per region</div>
            <div><B>Anomaly Scores</B> (JSON) — Z-score based per-record anomaly rating</div>
          </div>
        ),
      },
      { label: "Step 3", text: <>Click <B>Submit MapReduce Job</B>. Status updates every 5 seconds.</> },
      {
        label: "ML model types",
        text: (
          <div className="space-y-1.5 mt-1">
            <div><B>Anomaly Detection</B> — Isolation Forest, last 90 days</div>
            <div><B>Trend Prediction</B> — Linear Regression, last 365 days, 30-day forecast</div>
            <div><B>Correlation Analysis</B> — Pearson matrix, last 365 days</div>
          </div>
        ),
      },
      { label: "Run training", text: <>Click <B>Start Training</B>. Results appear on the Dashboard charts automatically.</> },
    ],
  },
  {
    id: "alerts",
    icon: <Bell size={18} />,
    title: "Alerts",
    items: [
      { label: "Create a rule", text: <>Go to <B>Alerts</B> and click <B>New Rule</B> (Admin only).</> },
      { label: "Configure", text: "Choose a metric, comparison operator, threshold value, and severity." },
      { label: "Behavior", text: "The rule evaluates against every incoming sensor record in real time." },
      { label: "Manage", text: "Rules can be enabled, disabled, or deleted from the rules table." },
      {
        label: "Acknowledging",
        text: (
          <>
            Any authenticated user can acknowledge an alert event. Click <B>Ack</B> on
            any pending event to remove it from the notifications panel.
          </>
        ),
      },
    ],
  },
  {
    id: "support",
    icon: <MessageSquare size={18} />,
    title: "Support",
    items: [
      { label: "Create a ticket", text: <>Go to <B>Support</B> and click <B>New Ticket</B>.</> },
      { label: "Fill in", text: "Subject, a detailed description, and optionally a screenshot URL." },
      { label: "Track", text: <>Track status (Open → In Progress → Resolved) in the ticket list.</> },
      {
        label: "Admin response",
        text: (
          <>
            Admins can respond to any ticket via the <B>Respond</B> button, update the
            status, and add a written response visible to the submitting user.
          </>
        ),
      },
    ],
  },
];

const TIPS: string[] = [
  "The Dashboard auto-refreshes in real time — no manual reload needed.",
  "Use the Climate Explorer filter bar to narrow large datasets before exporting.",
  "CSV exports are capped at 10,000 records per request. Apply filters to stay under the cap.",
  "The live feed panel in the dashboard shows the 10 most recent sensor readings.",
];

export default function HelpPage() {
  return (
    <div className="space-y-6 animate-fade-up max-w-4xl mx-auto">
      <PageHeader title="Help" description="User guide for the EarthScape platform" />

      <div className="space-y-5">
        {SECTIONS.map((section) => (
          <Card key={section.id} id={section.id} className="scroll-mt-6 p-6 md:p-8">
            <div className="flex items-center gap-3 mb-6">
              <span
                className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: "var(--brand-100)", color: "var(--brand-600)" }}
              >
                {section.icon}
              </span>
              <h2
                className="text-xl font-bold"
                style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
              >
                {section.title}
              </h2>
            </div>

            <ul className="space-y-3.5">
              {section.items.map((item) => (
                <li key={item.label} className="flex gap-3 text-sm">
                  <ChevronRight
                    size={16}
                    className="shrink-0 mt-0.5"
                    style={{ color: "var(--brand-500)" }}
                  />
                  <span style={{ color: "var(--text-secondary)", lineHeight: 1.7 }}>
                    {item.text}
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        ))}

        <Card id="tips" className="scroll-mt-6 p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <span
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: "var(--accent-400)", color: "white" }}
            >
              <Lightbulb size={18} />
            </span>
            <h2
              className="text-xl font-bold"
              style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
            >
              Tips
            </h2>
          </div>
          <ul className="space-y-3.5">
            {TIPS.map((tip) => (
              <li key={tip} className="flex gap-3 text-sm">
                <ChevronRight size={16} className="shrink-0 mt-0.5" style={{ color: "var(--brand-500)" }} />
                <span style={{ color: "var(--text-secondary)", lineHeight: 1.7 }}>{tip}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}