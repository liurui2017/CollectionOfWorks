"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, ApiError, setToken } from "@/src/api/client";

const schema = z.object({
  username: z.string().min(1, "请输入用户名"),
  password: z.string().min(1, "请输入密码"),
});

type LoginInput = z.infer<typeof schema>;

/** 后台登录页。 */
export default function AdminLoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams.get("redirect") ?? "/admin/works";
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { register, handleSubmit, formState } = useForm<LoginInput>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: LoginInput) => {
    setErr(null);
    setLoading(true);
    try {
      const res = await api.post<{ access_token: string }>("/api/v1/auth/login", data, { noAuth: true });
      if (res.access_token) {
        setToken(res.access_token);
        router.push(redirect);
        router.refresh();
      }
    } catch (e) {
      if (e instanceof ApiError) {
        setErr(e.message);
      } else {
        setErr("登录失败，请稍后重试");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2.5 font-semibold text-text">
            <span className="inline-block h-[9px] w-[9px] rounded-full bg-accent shadow-[0_0_12px_var(--accent)]" />
            管理后台
          </Link>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="rounded-[var(--radius)] border border-border bg-surface p-8 space-y-5"
        >
          <h1 className="text-xl font-semibold text-text text-center">登录</h1>

          <div className="space-y-1.5">
            <label className="text-xs text-text-dim">用户名</label>
            <input
              type="text"
              autoComplete="username"
              className="w-full rounded-lg bg-bg border border-border px-3.5 py-2.5 text-sm text-text outline-none focus:border-accent transition-colors"
              {...register("username")}
            />
            {formState.errors.username && (
              <p className="text-xs text-danger">{formState.errors.username.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-text-dim">密码</label>
            <input
              type="password"
              autoComplete="current-password"
              className="w-full rounded-lg bg-bg border border-border px-3.5 py-2.5 text-sm text-text outline-none focus:border-accent transition-colors"
              {...register("password")}
            />
            {formState.errors.password && (
              <p className="text-xs text-danger">{formState.errors.password.message}</p>
            )}
          </div>

          {err && (
            <div className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
              {err}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-accent text-bg font-semibold py-2.5 text-sm hover:bg-accent-dim transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "登录中..." : "登录"}
          </button>

          <p className="text-center text-xs text-text-mute">
            默认账号 admin · change-me-on-first-login（改环境变量可自定义）
          </p>
        </form>
      </div>
    </div>
  );
}
