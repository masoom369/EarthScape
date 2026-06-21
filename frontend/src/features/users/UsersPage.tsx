import { useState, useCallback, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Plus, UserX, UserCheck } from "lucide-react";
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
import { formatDate } from "@/lib/utils";
import type { UserResponse, PaginatedUsers } from "@/types/user";

const createSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  role: z.enum(["admin", "analyst", "viewer"]),
});
type CreateForm = z.infer<typeof createSchema>;

const ROLE_VARIANT: Record<string, "danger" | "info" | "neutral"> = {
  admin: "danger",
  analyst: "info",
  viewer: "neutral",
};

export default function UsersPage() {
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  // Per-row pending state so toggling one user's status doesn't disable every
  // button in the table — mirrors AlertsPage's toggleRule UX, scoped by id.
  const [pendingId, setPendingId] = useState<string | null>(null);

  const loadUsers = useCallback(async (p = 1, signal?: AbortSignal) => {
    try {
      const { data } = await api.get<PaginatedUsers>(`/users?page=${p}&limit=20`, { signal });
      setUsers(data.items);
      setTotal(data.total);
    } catch (err) {
      if ((err as { name?: string }).name !== "CanceledError") {
        toast.error("Failed to load users");
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void (async () => {
      await loadUsers(1, controller.signal);
    })();
    return () => controller.abort();
  }, [loadUsers]);

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: { role: "viewer" },
  });

  async function onCreate(data: CreateForm) {
    try {
      await api.post("/users", data);
      toast.success("User created");
      setShowModal(false);
      reset();
      void loadUsers(1);
    } catch {
      toast.error("Failed to create user");
    }
  }

  // CRITICAL FIX: deactivate previously called DELETE /users/{id} (which the
  // backend maps to a soft-deactivate, not a real delete — see UserService.
  // deactivate_user). Reactivation never existed because there was no PATCH
  // call wired up. Both directions now go through PATCH /users/{id} with
  // is_active, matching how AlertsPage.toggleRule already does it.
  async function toggleActive(user: UserResponse) {
    setPendingId(user.id);
    try {
      await api.patch(`/users/${user.id}`, { is_active: !user.is_active });
      toast.success(user.is_active ? "User deactivated" : "User reactivated");
      void loadUsers(page);
    } catch {
      toast.error(user.is_active ? "Failed to deactivate" : "Failed to reactivate");
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div className="space-y-6 animate-fade-up">
      <PageHeader
        title="Users"
        description="Manage platform access and roles"
        action={
          <Button icon={<Plus size={14} />} onClick={() => setShowModal(true)}>
            Add User
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>All Users</CardTitle>
          <span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{total} total</span>
        </CardHeader>
        <Table>
          <Thead>
            <tr>
              <Th>Email</Th>
              <Th>Role</Th>
              <Th>Status</Th>
              <Th>Created</Th>
              <Th>Actions</Th>
            </tr>
          </Thead>
          <Tbody>
            {users.map((u) => (
              <Tr key={u.id}>
                <Td>
                  <span className="text-xs font-medium" style={{ fontFamily: "var(--font-mono)" }}>
                    {u.email}
                  </span>
                </Td>
                <Td><Badge variant={ROLE_VARIANT[u.role] ?? "neutral"}>{u.role}</Badge></Td>
                <Td>
                  <Badge variant={u.is_active ? "success" : "danger"}>
                    {u.is_active ? "Active" : "Inactive"}
                  </Badge>
                </Td>
                <Td><span className="text-xs" style={{ color: "var(--text-tertiary)" }}>{formatDate(u.created_at)}</span></Td>
                <Td>
                  <Button
                    variant={u.is_active ? "danger" : "success-soft"}
                    size="sm"
                    icon={u.is_active ? <UserX size={13} /> : <UserCheck size={13} />}
                    loading={pendingId === u.id}
                    onClick={() => toggleActive(u)}
                  >
                    {u.is_active ? "Deactivate" : "Activate"}
                  </Button>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
        <Pagination page={page} total={total} limit={20} onChange={(p) => { setPage(p); void loadUsers(p); }} />
      </Card>

      <Modal open={showModal} onClose={() => setShowModal(false)} title="Create User">
        <form onSubmit={handleSubmit(onCreate)} className="space-y-4">
          <Input label="Email" type="email" error={errors.email?.message} {...register("email")} />
          <Input label="Password" type="password" error={errors.password?.message} {...register("password")} />
          <Select label="Role" {...register("role")}>
            <option value="viewer">Viewer</option>
            <option value="analyst">Analyst</option>
            <option value="admin">Admin</option>
          </Select>
          <div className="flex gap-3 justify-end pt-2">
            <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button>
            <Button type="submit" loading={isSubmitting}>Create User</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}