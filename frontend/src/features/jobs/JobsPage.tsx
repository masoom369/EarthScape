import { useState, useCallback, useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Cpu, Brain, CheckCircle, XCircle, Clock, Loader2 } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { usePoll } from "@/hooks/usePoll";
import PageHeader from "@/components/ui/PageHeader";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import Pagination from "@/components/ui/Pagination";
import { formatDateTime } from "@/lib/utils";
import type { JobLog, PaginatedJobLogs } from "@/types/job";
import type { IngestionLog, PaginatedIngestionLogs } from "@/types/ingestion";

const POLL_MS = Number(import.meta.env.VITE_POLL_JOBS_MS ?? 5000);

const mrSchema = z.object({
  job_name: z.string().min(1, "Required"),
  hdfs_input_path: z.string().min(1, "Select an ingested file"),
  job_type: z.enum(["temperature_agg", "precipitation_totals", "anomaly_scores"]),
});
type MRForm = z.infer<typeof mrSchema>;

// CRITICAL #3 fix: job_type → required input format. Drives the file dropdown
// filter below so users physically cannot select a mismatched file.
const JOB_TYPE_FORMAT: Record<MRForm["job_type"], "csv" | "json"> = {
  temperature_agg: "csv",
  precipitation_totals: "csv",
  anomaly_scores: "json",
};

function fileFormat(filename: string): "csv" | "json" | null {
  const ext = filename.split(".").pop()?.toLowerCase();
  if (ext === "csv") return "csv";
  if (ext === "json" || ext === "geojson") return "json";
  return null;
}

const STATUS_VARIANT: Record<string, "success" | "danger" | "warning" | "info"> = {
  completed: "success",
  failed: "danger",
  queued: "warning",
  running: "info",
};

const STATUS_ICON: Record<string, React.ReactNode> = {
  completed: <CheckCircle size={12} />,
  failed: <XCircle size={12} />,
  queued: <Clock size={12} />,
  running: <Loader2 size={12} className="animate-spin" />,
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [mlSubmitting, setMlSubmitting] = useState(false);
  const [mlModel, setMlModel] = useState("anomaly_detection");
  const [ingestedFiles, setIngestedFiles] = useState<IngestionLog[]>([]);

  const loadJobs = useCallback(async (p = 1) => {
    try {
      const { data } = await api.get<PaginatedJobLogs>(`/jobs?page=${p}&limit=20`);
      setJobs(data.items);
      setTotal(data.total);
    } catch { /* silent poll error */ }
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        const { data } = await api.get<PaginatedIngestionLogs>("/ingest/logs?page=1&limit=100");
        setIngestedFiles(data.items.filter((l) => l.status === "success" && l.hdfs_path));
      } catch { /* non-critical */ }
    })();
  }, []);

  usePoll(() => loadJobs(page), POLL_MS);

  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm<MRForm>({
    resolver: zodResolver(mrSchema),
    defaultValues: { job_type: "temperature_agg" },
  });

  const selectedJobType = watch("job_type");
  const requiredFormat = JOB_TYPE_FORMAT[selectedJobType];

  // CRITICAL #3 fix: only list files matching the selected job type's format.
  const compatibleFiles = useMemo(
    () => ingestedFiles.filter((f) => fileFormat(f.filename) === requiredFormat),
    [ingestedFiles, requiredFormat]
  );

  async function onMR(data: MRForm) {
    try {
      await api.post("/jobs/mapreduce", data);
      toast.success("MapReduce job queued");
      reset({ job_type: data.job_type });
      loadJobs(1);
    } catch {
      toast.error("Failed to submit job");
    }
  }

  async function onML() {
    setMlSubmitting(true);
    try {
      await api.post("/jobs/ml/train", { model_type: mlModel });
      toast.success(`ML training started: ${mlModel}`);
      loadJobs(1);
    } catch {
      toast.error("Failed to start ML training");
    } finally {
      setMlSubmitting(false);
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader title="Jobs" description="Trigger MapReduce processing and ML model training" />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>MapReduce Job</CardTitle>
            <Cpu size={18} style={{ color: "var(--text-tertiary)" }} />
          </CardHeader>
          <form onSubmit={handleSubmit(onMR)} className="space-y-3">
            <Input
              label="Job Name"
              error={errors.job_name?.message}
              {...register("job_name")}
            />
            <Select label="Job Type" {...register("job_type")}>
              <option value="temperature_agg">Temperature Aggregation (CSV)</option>
              <option value="precipitation_totals">Precipitation Totals (CSV)</option>
              <option value="anomaly_scores">Anomaly Scores (JSON)</option>
            </Select>
            <div className="space-y-1">
              <Select
                label={`Input File (HDFS) — ${requiredFormat.toUpperCase()} only`}
                error={errors.hdfs_input_path?.message}
                {...register("hdfs_input_path")}
              >
                <option value="">— Select an ingested file —</option>
                {compatibleFiles.length === 0 && (
                  <option disabled>No {requiredFormat.toUpperCase()} files ingested yet</option>
                )}
                {compatibleFiles.map((log) => (
                  <option key={log.id} value={log.hdfs_path!}>
                    {log.filename} · {log.record_count} records · {formatDateTime(log.created_at)}
                  </option>
                ))}
              </Select>
              <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                Only files matching the selected job type&apos;s format are listed.
              </p>
            </div>
            <Button type="submit" loading={isSubmitting} className="w-full mt-1">
              Submit MapReduce Job
            </Button>
          </form>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>ML Training</CardTitle>
            <Brain size={18} style={{ color: "var(--text-tertiary)" }} />
          </CardHeader>
          <div className="space-y-3">
            <Select label="Model Type" value={mlModel} onChange={(e) => setMlModel(e.target.value)}>
              <option value="anomaly_detection">Anomaly Detection (Isolation Forest)</option>
              <option value="trend_prediction">Trend Prediction (Linear Regression)</option>
              <option value="correlation">Correlation Analysis (Pearson)</option>
            </Select>
            <p className="text-xs" style={{ color: "var(--text-tertiary)" }}>
              Training reads from MongoDB climate_records and writes predictions back. Results visible on dashboard.
            </p>
            <Button onClick={onML} loading={mlSubmitting} className="w-full mt-1">
              Start Training
            </Button>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job History</CardTitle>
          <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            Polls every {POLL_MS / 1000}s
          </span>
        </CardHeader>
        <Table>
          <Thead>
            <tr>
              <Th>Name</Th>
              <Th>Type</Th>
              <Th>Status</Th>
              <Th>Duration</Th>
              <Th>Started</Th>
            </tr>
          </Thead>
          <Tbody>
            {jobs.map((job) => (
              <Tr key={job.id}>
                <Td>
                  <span className="text-xs font-medium" style={{ fontFamily: "var(--font-mono)" }}>
                    {job.job_name}
                  </span>
                </Td>
                <Td>
                  <Badge variant="neutral">{job.job_type}</Badge>
                </Td>
                <Td>
                  <Badge variant={STATUS_VARIANT[job.status] ?? "neutral"}>
                    <span className="flex items-center gap-1">
                      {STATUS_ICON[job.status]}
                      {job.status}
                    </span>
                  </Badge>
                  {job.status === "failed" && job.error && (
                    <p className="text-xs mt-1 max-w-xs" style={{ color: "var(--danger)" }}>
                      {job.error}
                    </p>
                  )}
                </Td>
                <Td>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                    {job.duration_seconds != null ? `${job.duration_seconds}s` : "—"}
                  </span>
                </Td>
                <Td>
                  <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                    {formatDateTime(job.started_at)}
                  </span>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
        <Pagination page={page} total={total} limit={20} onChange={(p) => { setPage(p); loadJobs(p); }} />
      </Card>
    </div>
  );
}