import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, CheckCircle, XCircle, Clock } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import PageHeader from "@/components/ui/PageHeader";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import Pagination from "@/components/ui/Pagination";
import EmptyState from "@/components/ui/EmptyState";
import Select from "@/components/ui/Select";
import { formatDateTime } from "@/lib/utils";
import type { IngestionLog, PaginatedIngestionLogs } from "@/types/ingestion";

const STATUS_VARIANT: Record<string, "success" | "danger" | "warning"> = {
  success: "success",
  failed: "danger",
  pending: "warning",
};

const STATUS_ICON: Record<string, React.ReactNode> = {
  success: <CheckCircle size={13} />,
  failed: <XCircle size={13} />,
  pending: <Clock size={13} />,
};

export default function IngestionPage() {
  const [logs, setLogs] = useState<IngestionLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [uploading, setUploading] = useState(false);
  const [sourceType, setSourceType] = useState("weather_station");
  const [logsLoaded, setLogsLoaded] = useState(false);

  const loadLogs = useCallback(async (p = 1) => {
    try {
      const { data } = await api.get<PaginatedIngestionLogs>(`/ingest/logs?page=${p}&limit=20`);
      setLogs(data.items);
      setTotal(data.total);
      setLogsLoaded(true);
    } catch {
      toast.error("Failed to load ingestion logs");
    }
  }, []);

  useState(() => { loadLogs(1); });

  const onDrop = useCallback(
    async (files: File[]) => {
      const file = files[0];
      if (!file) return;
      setUploading(true);
      const form = new FormData();
      form.append("file", file);
      form.append("source_type", sourceType);
      try {
        await api.post("/ingest/upload", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        toast.success(`Ingested: ${file.name}`);
        loadLogs(1);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Upload failed";
        toast.error(msg);
      } finally {
        setUploading(false);
      }
    },
    [sourceType, loadLogs]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/json": [".json", ".geojson"],
    },
    multiple: false,
    disabled: uploading,
  });

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader title="Data Ingestion" description="Upload climate datasets to HDFS" />

      {/* Upload zone */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Dataset</CardTitle>
          <Select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="w-40"
          >
            <option value="weather_station">Weather Station</option>
            <option value="satellite">Satellite</option>
            <option value="sensor">Sensor</option>
          </Select>
        </CardHeader>

        <div
          {...getRootProps()}
          className="border-2 border-dashed rounded-xl flex flex-col items-center justify-center py-12 px-6 cursor-pointer transition-all duration-200"
          style={{
            borderColor: isDragActive ? "var(--brand-500)" : "var(--border-default)",
            background: isDragActive ? "var(--brand-50)" : "var(--bg-elevated)",
          }}
        >
          <input {...getInputProps()} />
          <Upload
            size={32}
            className="mb-3"
            style={{ color: isDragActive ? "var(--brand-500)" : "var(--text-tertiary)" }}
          />
          <p className="font-semibold text-sm" style={{ color: "var(--text-primary)", fontFamily: "var(--font-display)" }}>
            {uploading ? "Uploading…" : isDragActive ? "Drop to upload" : "Drag & drop or click to browse"}
          </p>
          <p className="text-xs mt-1" style={{ color: "var(--text-tertiary)" }}>
            CSV, JSON, GeoJSON · Max 50 MB
          </p>
        </div>
      </Card>

      {/* Logs table */}
      <Card>
        <CardHeader>
          <CardTitle>Ingestion Log</CardTitle>
          <Button variant="secondary" size="sm" onClick={() => loadLogs(page)}>
            Refresh
          </Button>
        </CardHeader>

        {logsLoaded && logs.length === 0 ? (
          <EmptyState icon={<FileText size={22} />} title="No ingestion logs" description="Upload a file to get started" />
        ) : (
          <>
            <Table>
              <Thead>
                <tr>
                  <Th>File</Th>
                  <Th>Format</Th>
                  <Th>Records</Th>
                  <Th>Status</Th>
                  <Th>Date</Th>
                </tr>
              </Thead>
              <Tbody>
                {logs.map((log) => (
                  <Tr key={log.id}>
                    <Td>
                      <span className="font-medium text-xs" style={{ fontFamily: "var(--font-mono)" }}>
                        {log.filename}
                      </span>
                    </Td>
                    <Td>
                      <Badge variant="neutral">{log.format.toUpperCase()}</Badge>
                    </Td>
                    <Td>
                      <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                        {log.record_count.toLocaleString()}
                      </span>
                    </Td>
                    <Td>
                      <Badge variant={STATUS_VARIANT[log.status] ?? "neutral"}>
                        <span className="flex items-center gap-1">
                          {STATUS_ICON[log.status]}
                          {log.status}
                        </span>
                      </Badge>
                    </Td>
                    <Td>
                      <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
                        {formatDateTime(log.created_at)}
                      </span>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
            <Pagination
              page={page}
              total={total}
              limit={20}
              onChange={(p) => { setPage(p); loadLogs(p); }}
            />
          </>
        )}
      </Card>
    </div>
  );
}