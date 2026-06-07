import { useState, useCallback } from "react";
import { Download, Database } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import PageHeader from "@/components/ui/PageHeader";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import Pagination from "@/components/ui/Pagination";
import { FilterBar } from "@/components/ui/FilterBar";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import EmptyState from "@/components/ui/EmptyState";
import { formatDateTime, formatNumber } from "@/lib/utils";
import type { ClimateRecord, PaginatedClimateRecords } from "@/types/climate";
import { useAuth } from "@/hooks/useAuth";

export default function ClimateExplorerPage() {
  const { can } = useAuth();
  const [records, setRecords] = useState<ClimateRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  const [filters, setFilters] = useState({
    region: "",
    source_type: "",
    from_date: "",
    to_date: "",
    is_anomaly: "",
  });

  const buildQuery = (p = 1) => {
    const params = new URLSearchParams({ page: String(p), limit: "50" });
    if (filters.region) params.set("region", filters.region);
    if (filters.source_type) params.set("source_type", filters.source_type);
    if (filters.from_date) params.set("from_date", filters.from_date);
    if (filters.to_date) params.set("to_date", filters.to_date);
    if (filters.is_anomaly) params.set("is_anomaly", filters.is_anomaly);
    return params.toString();
  };

  const loadRecords = useCallback(async (p = 1) => {
    setLoading(true);
    try {
      const { data } = await api.get<PaginatedClimateRecords>(`/climate?${buildQuery(p)}`);
      setRecords(data.items);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load records");
    } finally {
      setLoading(false);
    }
  }, [filters]); // eslint-disable-line react-hooks/exhaustive-deps

  useState(() => { loadRecords(1); });

  async function exportCSV() {
    setExporting(true);
    try {
      const params = new URLSearchParams();
      if (filters.region) params.set("region", filters.region);
      if (filters.source_type) params.set("source_type", filters.source_type);
      if (filters.from_date) params.set("from_date", filters.from_date);
      if (filters.to_date) params.set("to_date", filters.to_date);
      if (filters.is_anomaly) params.set("is_anomaly", filters.is_anomaly);

      const res = await api.get(`/climate/export?${params.toString()}`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data as Blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "climate_export.csv";
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Export downloaded");
    } catch {
      toast.error("Export failed or cap exceeded");
    } finally {
      setExporting(false);
    }
  }

  function update(k: string, v: string) {
    setFilters((f) => ({ ...f, [k]: v }));
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title="Climate Explorer"
        description="Browse and export climate records"
        action={
          can("admin", "analyst") ? (
            <Button
              variant="secondary"
              size="sm"
              icon={<Download size={14} />}
              loading={exporting}
              onClick={exportCSV}
            >
              Export CSV
            </Button>
          ) : undefined
        }
      />

      <FilterBar>
        <Input
          label="Region"
          placeholder="Karachi"
          value={filters.region}
          onChange={(e) => update("region", e.target.value)}
          className="w-36"
        />
        <Select label="Source" value={filters.source_type} onChange={(e) => update("source_type", e.target.value)} className="w-40">
          <option value="">All</option>
          <option value="weather_station">Weather Station</option>
          <option value="satellite">Satellite</option>
          <option value="sensor">Sensor</option>
        </Select>
        <Input
          label="From"
          type="date"
          value={filters.from_date}
          onChange={(e) => update("from_date", e.target.value)}
          className="w-36"
        />
        <Input
          label="To"
          type="date"
          value={filters.to_date}
          onChange={(e) => update("to_date", e.target.value)}
          className="w-36"
        />
        <Select label="Anomalies" value={filters.is_anomaly} onChange={(e) => update("is_anomaly", e.target.value)} className="w-32">
          <option value="">All</option>
          <option value="true">Anomalies only</option>
          <option value="false">Normal only</option>
        </Select>
        <Button onClick={() => { setPage(1); loadRecords(1); }} loading={loading} size="sm" className="mt-5">
          Apply
        </Button>
      </FilterBar>

      <Card>
        <CardHeader>
          <CardTitle>Records</CardTitle>
          <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>
            {total.toLocaleString()} total
          </span>
        </CardHeader>

        {!loading && records.length === 0 ? (
          <EmptyState icon={<Database size={22} />} title="No records found" description="Adjust filters or ingest data" />
        ) : (
          <>
            <Table>
              <Thead>
                <tr>
                  <Th>Region</Th>
                  <Th>Source</Th>
                  <Th>Temp °C</Th>
                  <Th>Precip mm</Th>
                  <Th>Humidity %</Th>
                  <Th>CO₂ ppm</Th>
                  <Th>Anomaly</Th>
                  <Th>Timestamp</Th>
                </tr>
              </Thead>
              <Tbody>
                {records.map((r) => (
                  <Tr key={r.id}>
                    <Td><span className="font-medium text-xs">{r.location.region}</span></Td>
                    <Td><Badge variant="neutral">{r.source_type}</Badge></Td>
                    <Td><span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>{formatNumber(r.temperature_c, 1)}</span></Td>
                    <Td><span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>{formatNumber(r.precipitation_mm)}</span></Td>
                    <Td><span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>{formatNumber(r.humidity_pct, 1)}</span></Td>
                    <Td><span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>{formatNumber(r.co2_ppm, 1)}</span></Td>
                    <Td>
                      {r.is_anomaly
                        ? <Badge variant="danger">Yes</Badge>
                        : <Badge variant="neutral">No</Badge>}
                    </Td>
                    <Td><span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{formatDateTime(r.timestamp)}</span></Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
            <Pagination page={page} total={total} limit={50} onChange={(p) => { setPage(p); loadRecords(p); }} />
          </>
        )}
      </Card>
    </div>
  );
}