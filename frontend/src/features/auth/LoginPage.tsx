import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Globe, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/authStore";
import { useThemeStore } from "@/stores/themeStore";
import api from "@/lib/api";
import type { UserProfile } from "@/types/auth";

const schema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(8, "Min 8 characters"),
});
type FormData = z.infer<typeof schema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const setUser = useAuthStore((s) => s.setUser);
  const user = useAuthStore((s) => s.user);
  const theme = useThemeStore((s) => s.theme);
  const toggle = useThemeStore((s) => s.toggle);

  useEffect(() => {
    if (user) navigate("/dashboard", { replace: true });
  }, [user, navigate]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  async function onSubmit(data: FormData) {
    try {
      const res = await api.post<UserProfile>("/auth/login", data);
      setUser(res.data);
      navigate("/dashboard", { replace: true });
      toast.success("Welcome back!");
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Login failed";
      toast.error(msg);
    }
  }

  return (
    <div
      className="min-h-dvh flex items-center justify-center p-4"
      style={{ background: "var(--bg-base)" }}
    >
      {/* Background texture */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(circle at 20% 50%, var(--brand-900) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, var(--brand-900) 0%, transparent 40%)`,
          opacity: 0.4,
        }}
      />

      <div className="relative w-full max-w-md animate-fade-up">
        {/* Header */}
        <div className="text-center mb-8">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: "var(--brand-600)" }}
          >
            <Globe size={28} color="white" />
          </div>
          <h1
            className="text-3xl font-bold tracking-tight"
            style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
          >
            EarthScape
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-tertiary)" }}>
            Climate Analytics Platform
          </p>
        </div>

        {/* Card */}
        <div
          className="rounded-2xl p-7"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-default)",
            boxShadow: "var(--shadow-xl)",
          }}
        >
          <h2
            className="text-lg font-bold mb-5"
            style={{ fontFamily: "var(--font-display)", color: "var(--text-primary)" }}
          >
            Sign in to your account
          </h2>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Email address
              </label>
              <input
                type="email"
                autoComplete="email"
                className="w-full px-3 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--brand-500)]"
                style={{
                  background: "var(--bg-elevated)",
                  border: `1px solid ${errors.email ? "var(--danger)" : "var(--border-default)"}`,
                  color: "var(--text-primary)",
                }}
                {...register("email")}
              />
              {errors.email && (
                <p className="text-xs" style={{ color: "var(--danger)" }}>
                  {errors.email.message}
                </p>
              )}
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                Password
              </label>
              <input
                type="password"
                autoComplete="current-password"
                className="w-full px-3 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--brand-500)]"
                style={{
                  background: "var(--bg-elevated)",
                  border: `1px solid ${errors.password ? "var(--danger)" : "var(--border-default)"}`,
                  color: "var(--text-primary)",
                }}
                {...register("password")}
              />
              {errors.password && (
                <p className="text-xs" style={{ color: "var(--danger)" }}>
                  {errors.password.message}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg font-semibold text-sm transition-all mt-2"
              style={{ background: "var(--brand-600)", color: "white" }}
            >
              {isSubmitting ? "Signing in…" : "Sign in"}
              {!isSubmitting && <ArrowRight size={16} />}
            </button>
          </form>

          <p className="text-center text-xs mt-5" style={{ color: "var(--text-tertiary)" }}>
            Default: admin@earthscape.local / Admin123!
          </p>
        </div>

        {/* Theme toggle */}
        <div className="text-center mt-4">
          <button
            onClick={toggle}
            className="text-xs px-3 py-1.5 rounded-full transition-colors"
            style={{ color: "var(--text-tertiary)", background: "var(--bg-surface)" }}
          >
            Switch to {theme === "dark" ? "light" : "dark"} mode
          </button>
        </div>
      </div>
    </div>
  );
}