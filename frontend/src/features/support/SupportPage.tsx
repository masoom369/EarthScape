import { useState, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Plus, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import PageHeader from "@/components/ui/PageHeader";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { Table, Thead, Th, Tbody, Tr, Td } from "@/components/ui/Table";
import Pagination from "@/components/ui/Pagination";
import EmptyState from "@/components/ui/EmptyState";
import { formatDateTime } from "@/lib/utils";
import type { SupportTicket, PaginatedTickets, TicketStatus } from "@/types/support";
import Select from "@/components/ui/Select";

const createSchema = z.object({
  subject: z.string().min(1).max(200),
  description: z.string().min(1),
  screenshot_url: z.string().url().optional().or(z.literal("")),
});
type CreateForm = z.infer<typeof createSchema>;

const STATUS_VARIANT: Record<TicketStatus, "warning" | "info" | "success"> = {
  open: "warning",
  "in-progress": "info",
  resolved: "success",
};

export default function SupportPage() {
  const { isAdmin } = useAuth();
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [selected, setSelected] = useState<SupportTicket | null>(null);
  const [adminStatus, setAdminStatus] = useState<TicketStatus>("in-progress");
  const [adminResponse, setAdminResponse] = useState("");
  const [responding, setResponding] = useState(false);

  const load = useCallback(async (p = 1) => {
    const { data } = await api.get<PaginatedTickets>(`/support/tickets?page=${p}&limit=20`);
    setTickets(data.items);
    setTotal(data.total);
  }, []);

  useState(() => { load(1); });

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
  });

  async function onCreate(data: CreateForm) {
    try {
      const payload = { ...data, screenshot_url: data.screenshot_url || null };
      await api.post("/support/tickets", payload);
      toast.success("Ticket submitted");
      setShowModal(false);
      reset();
      load(1);
    } catch {
      toast.error("Failed to submit ticket");
    }
  }

  async function respond(ticket: SupportTicket) {
    setResponding(true);
    try {
      await api.patch(`/support/tickets/${ticket.id}`, {
        status: adminStatus,
        response: adminResponse || undefined,
      });
      toast.success("Ticket updated");
      setSelected(null);
      setAdminResponse("");
      load(page);
    } catch {
      toast.error("Failed to update ticket");
    } finally {
      setResponding(false);
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title="Support"
        description="Submit and track support requests"
        action={
          <Button icon={<Plus size={14} />} onClick={() => setShowModal(true)}>
            New Ticket
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Tickets</CardTitle>
        </CardHeader>
        {tickets.length === 0 ? (
          <EmptyState icon={<MessageSquare size={22} />} title="No tickets yet" description="Submit a ticket if you need assistance" />
        ) : (
          <>
            <Table>
              <Thead>
                <tr>
                  <Th>Subject</Th>
                  <Th>Status</Th>
                  <Th>Submitted</Th>
                  {isAdmin && <Th>Actions</Th>}
                </tr>
              </Thead>
              <Tbody>
                {tickets.map((t) => (
                  <Tr key={t.id}>
                    <Td>
                      <div>
                        <p className="text-xs font-medium" style={{ color: "var(--text-primary)" }}>{t.subject}</p>
                        {t.response && (
                          <p className="text-xs mt-0.5" style={{ color: "var(--text-tertiary)" }}>
                            Response: {t.response.slice(0, 60)}…
                          </p>
                        )}
                      </div>
                    </Td>
                    <Td><Badge variant={STATUS_VARIANT[t.status]}>{t.status}</Badge></Td>
                    <Td><span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{formatDateTime(t.created_at)}</span></Td>
                    {isAdmin && (
                      <Td>
                        <Button variant="ghost" size="sm" onClick={() => { setSelected(t); setAdminStatus(t.status); setAdminResponse(t.response ?? ""); }}>
                          Respond
                        </Button>
                      </Td>
                    )}
                  </Tr>
                ))}
              </Tbody>
            </Table>
            <Pagination page={page} total={total} limit={20} onChange={(p) => { setPage(p); load(p); }} />
          </>
        )}
      </Card>

      {/* Create modal */}
      <Modal open={showModal} onClose={() => setShowModal(false)} title="New Support Ticket">
        <form onSubmit={handleSubmit(onCreate)} className="space-y-4">
          <Input label="Subject" error={errors.subject?.message} {...register("subject")} />
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Description</label>
            <textarea
              rows={4}
              className="w-full px-3 py-2 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[var(--brand-500)]"
              style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }}
              {...register("description")}
            />
            {errors.description && <p className="text-xs" style={{ color: "var(--danger)" }}>{errors.description.message}</p>}
          </div>
          <Input label="Screenshot URL (optional)" type="url" error={errors.screenshot_url?.message} {...register("screenshot_url")} />
          <div className="flex gap-3 justify-end pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button type="submit" loading={isSubmitting}>Submit</Button>
          </div>
        </form>
      </Modal>

      {/* Admin respond modal */}
      <Modal open={!!selected} onClose={() => setSelected(null)} title="Respond to Ticket">
        {selected && (
          <div className="space-y-4">
            <div className="rounded-lg p-3 text-sm" style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)" }}>
              <p className="font-medium mb-1" style={{ color: "var(--text-primary)" }}>{selected.subject}</p>
              <p>{selected.description}</p>
            </div>
            <Select label="Status" value={adminStatus} onChange={(e) => setAdminStatus(e.target.value as TicketStatus)}>
              <option value="open">Open</option>
              <option value="in-progress">In Progress</option>
              <option value="resolved">Resolved</option>
            </Select>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>Response</label>
              <textarea
                rows={3}
                value={adminResponse}
                onChange={(e) => setAdminResponse(e.target.value)}
                className="w-full px-3 py-2 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[var(--brand-500)]"
                style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", color: "var(--text-primary)" }}
              />
            </div>
            <div className="flex gap-3 justify-end">
              <Button variant="secondary" onClick={() => setSelected(null)}>Cancel</Button>
              <Button loading={responding} onClick={() => respond(selected)}>Save Response</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}