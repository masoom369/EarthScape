import Markdown from 'react-markdown';
import { theme } from '../../styles/theme';

const HELP_CONTENT = `
# EarthScape User Guide

## Login & Session Management
Sign in with your email and password at the login page. Your session is stored in a secure httpOnly cookie.
Click **Logout** in the sidebar to end your session.

## Data Upload & Ingestion Monitoring
Navigate to **Ingestion** (Analyst/Admin). Drag and drop a CSV, JSON, or GeoJSON file.
Select the appropriate source type. Monitor upload status in the ingestion log table.

## Triggering MapReduce & ML Jobs
Go to **Jobs**. For MapReduce, select job type and provide the HDFS input path.
For ML training, choose model type (anomaly detection, trend prediction, or correlation) and click Train.
Job status updates automatically.

## Alert Rules & Acknowledging Events
Admins can create alert rules on the **Alerts** page. Rules evaluate incoming sensor data automatically.
Unacknowledged alerts appear on the Dashboard notifications panel. Click **Acknowledge** to dismiss.

## Support Tickets
Visit **Support** to submit a ticket with subject, description, and optional screenshot URL.
Track status and admin responses in the ticket list.
`;

export function HelpPage() {
  return (
    <div style={{
      background: theme.colors.surface, padding: theme.spacing.xl,
      borderRadius: theme.radius.lg, maxWidth: 800,
    }}>
      <Markdown>{HELP_CONTENT}</Markdown>
    </div>
  );
}
