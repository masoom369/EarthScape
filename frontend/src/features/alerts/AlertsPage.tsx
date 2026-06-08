import { useState, useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Plus, Trash2, Bell, CheckCheck } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import PageHeader from "@/components/ui/PageHeader";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Input from "@/components/ui/Input";
import Select from "@/components/ui/Select";
import Modal from "@/components/ui/Modal";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import Pagination from "@/components/ui/Pagination";
import EmptyState from "@/components/ui/EmptyState";
import { formatDateTime } from "@/lib/utils";
import { useAlertStore } from "@/stores/alertStore";
import type { AlertRule, PaginatedAlertEvents } from "@/types/alert";

const ruleSchema = z.object({
  name: z.string().min(1, "Name is required"),
  metric: z.enum(["temperature_c", "precipitation_mm", "co2_ppm", "humidity_pct"]),
  operator: z.enum([">", "<", "=", ">=", "<="]),
  threshold: z.number(),
  severity: z.enum(["low", "medium", "high"]),
});
type RuleForm = z.infer<typeof ruleSchema>;

const SEV_VARIANT: Record<string, "danger" | "warning" | "info"> = {
  high: "danger", medium: "warning", low: "info",
};

export default function AlertsPage() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [events, setEvents] = useState<PaginatedAlertEvents | null>(null);
  const [eventPage, setEventPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const acknowledge = useAlertStore((s) => s.acknowledge);

  const loadRules = useCallback(async (signal?: AbortSignal) => {
    try {
      const { data } = await api.get<AlertRule[]>("/alerts/rules", { signal });
      setRules(data);
    } catch (err) {
      if ((err as { name?: string }).name !== "CanceledError") {
        toast.error("Failed to load rules");
      }
    }
  }, []);

  const loadEvents = useCallback(async (p = 1, signal?: AbortSignal) => {
    try {
      const { data } = await api.get<PaginatedAlertEvents>(
        `/alerts/events?page=${p}&limit=20`,
        { signal }
      );
      setEvents(data);
    } catch (err) {
      if ((err as { name?: string }).name !== "CanceledError") {
        toast.error("Failed to load events");
      }
    }
  }, []);

  // Inline async IIFE avoids react-hooks/set-state-in-effect — same pattern as JobsPage
  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      await loadRules(controller.signal);
      await loadEvents(1, controller.signal);
    })();
    return () => controller.abort();
  }, [loadRules, loadEvents]);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<RuleForm>({
    resolver: zodResolver(ruleSchema),
    defaultValues: { metric: "temperature_c", operator: ">", severity: "medium" },
  });

  async function onCreateRule(data: RuleForm) {
    try {
      await api.post("/alerts/rules", data);
      toast.success("Rule created");
      setShowModal(false);
      reset();
      void loadRules();
    } catch {
      toast.error("Failed to create rule");
    }
  }

  async function deleteRule(id: string) {
    try {
      await api.delete(`/alerts/rules/${id}`);
      toast.success("Rule deleted");
      void loadRules();
    } catch {
      toast.error("Failed to delete rule");
    }
  }

  async function toggleRule(rule: AlertRule) {
    try {
      await api.patch(`/alerts/rules/${rule.id}`, { is_active: !rule.is_active });
      void loadRules();
    } catch {
      toast.error("Failed to update rule");
    }
  }

  async function ackEvent(id: string) {
    try {
      await api.patch(`/alerts/events/${id}/acknowledge`);
      acknowledge(id);
      void loadEvents(eventPage);
    } catch {
      toast.error("Failed to acknowledge");
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title="Alerts"
        description="Manage alert rules and review triggered events"
        action={
          <Button icon={<Plus size={14} />} onClick={() => setShowModal(true)}>
            New Rule
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Alert Rules</CardTitle>
        </CardHeader>
        {rules.length === 0 ? (
          <EmptyState icon={<Bell size={22} />} title="No alert rules" description="Create a rule to start monitoring" />
        ) : (
          <Table>
            <Thead>
              <tr>
                <Th>Name</Th>
                <Th>Condition</Th>
                <Th>Severity</Th>
                <Th>Status</Th>
                <Th>Actions</Th>
              </tr>
            </Thead>
            <Tbody>
              {rules.map((rule) => (
                <Tr key={rule.id}>
                  <Td><span className="font-medium text-xs">{rule.name}</span></Td>
                  <Td>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                      {rule.metric} {rule.operator} {rule.threshold}
                    </span>
                  </Td>
                  <Td><Badge variant={SEV_VARIANT[rule.severity] ?? "neutral"}>{rule.severity}</Badge></Td>
                  <Td>
                    <Badge variant={rule.is_active ? "success" : "neutral"}>
                      {rule.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </Td>
                  <Td>
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm" onClick={() => toggleRule(rule)}>
                        {rule.is_active ? "Disable" : "Enable"}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Trash2 size={13} />}
                        onClick={() => deleteRule(rule.id)}
                      />
                    </div>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Alert Events</CardTitle>
          <Button variant="secondary" size="sm" onClick={() => void loadEvents(1)}>Refresh</Button>
        </CardHeader>
        {events?.items.length === 0 ? (
          <EmptyState icon={<Bell size={22} />} title="No events" description="Alert events appear here when rules trigger" />
        ) : (
          <>
            <Table>
              <Thead>
                <tr>
                  <Th>Severity</Th>
                  <Th>Value</Th>
                  <Th>Triggered</Th>
                  <Th>Status</Th>
                  <Th>Action</Th>
                </tr>
              </Thead>
              <Tbody>
                {events?.items.map((e) => (
                  <Tr key={e.id}>
                    <Td><Badge variant={SEV_VARIANT[e.severity] ?? "neutral"}>{e.severity}</Badge></Td>
                    <Td>
                      <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                        {e.triggered_value}
                      </span>
                    </Td>
                    <Td><span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{formatDateTime(e.triggered_at)}</span></Td>
                    <Td>
                      <Badge variant={e.acknowledged ? "success" : "warning"}>
                        {e.acknowledged ? "Acknowledged" : "Pending"}
                      </Badge>
                    </Td>
                    <Td>
                      {!e.acknowledged && (
                        <Button variant="ghost" size="sm" icon={<CheckCheck size={13} />} onClick={() => ackEvent(e.id)}>
                          Ack
                        </Button>
                      )}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
            <Pagination
              page={eventPage}
              total={events?.total ?? 0}
              limit={20}
              onChange={(p) => { setEventPage(p); void loadEvents(p); }}
            />
          </>
        )}
      </Card>

      <Modal open={showModal} onClose={() => setShowModal(false)} title="Create Alert Rule">
        <form onSubmit={handleSubmit(onCreateRule)} className="space-y-4">
          <Input label="Rule Name" error={errors.name?.message} {...register("name")} />
          <div className="grid grid-cols-2 gap-3">
            <Select label="Metric" {...register("metric")}>
              <option value="temperature_c">Temperature °C</option>
              <option value="precipitation_mm">Precipitation mm</option>
              <option value="co2_ppm">CO₂ ppm</option>
              <option value="humidity_pct">Humidity %</option>
            </Select>
            <Select label="Operator" {...register("operator")}>
              {([">", "<", "=", ">=", "<="] as const).map((op) => (
                <option key={op} value={op}>{op}</option>
              ))}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Threshold"
              type="number"
              step="any"
              error={errors.threshold?.message}
              {...register("threshold", { valueAsNumber: true })}
            />
            <Select label="Severity" {...register("severity")}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </Select>
          </div>
          <div className="flex gap-3 justify-end pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button type="submit" loading={isSubmitting}>Create Rule</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}