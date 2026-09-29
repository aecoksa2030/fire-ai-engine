"use client";

import { useEffect, useState } from "react";
import { Loader2, Trash2, UserPlus, KeyRound, ShieldCheck } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { useT } from "@/lib/i18n";
import { ApiError, createUser, deleteUser, listUsers, updateUser, type UserRecord } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SelectNative } from "@/components/ui/select-native";

const ROLES = ["engineer", "auditor", "admin"];

export default function UsersPage() {
  const token = useAuthStore((s) => s.token);
  const currentUsername = useAuthStore((s) => s.user?.username);
  const t = useT();

  const [users, setUsers] = useState<UserRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function refresh() {
    if (!token) return;
    listUsers(token)
      .then(setUsers)
      .catch((err) => setError(err instanceof ApiError ? err.message : String(err)));
  }

  useEffect(refresh, [token]);

  function updateOne(userId: number, patch: Partial<UserRecord>) {
    setUsers((prev) => prev?.map((u) => (u.id === userId ? { ...u, ...patch } : u)) ?? prev);
  }

  function removeOne(userId: number) {
    setUsers((prev) => prev?.filter((u) => u.id !== userId) ?? prev);
  }

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-text-primary">{t.users_title}</h1>
        <p className="text-sm text-text-secondary mt-0.5">{t.users_subtitle}</p>
      </div>

      <CreateUserCard token={token!} onCreated={refresh} />

      <div>
        <h2 className="text-sm font-semibold text-text-primary mb-2">{t.users_list_title}</h2>

        {error && (
          <div className="text-sm text-danger bg-danger/10 border border-danger/30 rounded-[var(--radius-md)] px-4 py-3 mb-3">
            {error}
          </div>
        )}

        {users === null && !error && (
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <Loader2 className="h-4 w-4 animate-spin" /> {t.archive_loading}
          </div>
        )}

        {users !== null && users.length === 0 && (
          <p className="text-sm text-text-secondary">{t.users_list_empty}</p>
        )}

        <div className="space-y-3">
          {users?.map((user) => (
            <UserRow
              key={user.id}
              user={user}
              token={token!}
              isSelf={user.username === currentUsername}
              onUpdated={(patch) => updateOne(user.id, patch)}
              onDeleted={() => removeOne(user.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function CreateUserCard({ token, onCreated }: { token: string; onCreated: () => void }) {
  const t = useT();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("engineer");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  async function handleCreate() {
    if (!username.trim() || !email.trim() || !password) return;
    setCreating(true);
    setError(null);
    setOk(false);
    try {
      await createUser(token, { username: username.trim(), email: email.trim(), password, role });
      setUsername("");
      setEmail("");
      setPassword("");
      setRole("engineer");
      setOk(true);
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <Card>
      <CardContent className="pt-5">
        <h2 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-1.5">
          <UserPlus className="h-4 w-4" /> {t.users_create_title}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="space-y-1.5">
            <Label>{t.users_col_username}</Label>
            <Input value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>{t.users_col_email}</Label>
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>{t.password}</Label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>{t.users_col_role}</Label>
            <SelectNative value={role} onChange={(e) => setRole(e.target.value)}>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </SelectNative>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <Button
            onClick={handleCreate}
            disabled={creating || !username.trim() || !email.trim() || !password}
          >
            {creating ? <Loader2 className="h-4 w-4 animate-spin" /> : t.users_create_btn}
          </Button>
          {ok && <span className="text-xs text-success">{t.users_create_ok}</span>}
        </div>
        {error && <div className="text-xs text-danger mt-2">{error}</div>}
      </CardContent>
    </Card>
  );
}

function UserRow({
  user,
  token,
  isSelf,
  onUpdated,
  onDeleted,
}: {
  user: UserRecord;
  token: string;
  isSelf: boolean;
  onUpdated: (patch: Partial<UserRecord>) => void;
  onDeleted: () => void;
}) {
  const t = useT();
  const [role, setRole] = useState(user.role);
  const [savingRole, setSavingRole] = useState(false);
  const [roleOk, setRoleOk] = useState(false);

  const [newPassword, setNewPassword] = useState("");
  const [savingPw, setSavingPw] = useState(false);
  const [pwOk, setPwOk] = useState(false);

  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [rowError, setRowError] = useState<string | null>(null);

  async function handleRoleChange() {
    setSavingRole(true);
    setRowError(null);
    setRoleOk(false);
    try {
      await updateUser(token, user.id, { role });
      onUpdated({ role });
      setRoleOk(true);
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setSavingRole(false);
    }
  }

  async function handleResetPassword() {
    if (!newPassword) return;
    setSavingPw(true);
    setRowError(null);
    setPwOk(false);
    try {
      await updateUser(token, user.id, { new_password: newPassword });
      setNewPassword("");
      setPwOk(true);
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setSavingPw(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setRowError(null);
    try {
      await deleteUser(token, user.id);
      onDeleted();
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : String(err));
      setDeleting(false);
    }
  }

  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <div className="text-sm font-medium text-text-primary">{user.username}</div>
            <div className="text-xs text-text-secondary">{user.email}</div>
          </div>
          <span className="text-[10px] uppercase tracking-wide text-accent font-semibold bg-accent-soft rounded-[var(--radius-sm)] px-2 py-1">
            {user.role}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
          <div className="flex items-end gap-2">
            <div className="flex-1 space-y-1.5">
              <Label className="text-xs">{t.users_new_role_label}</Label>
              <SelectNative value={role} onChange={(e) => setRole(e.target.value)}>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </SelectNative>
            </div>
            <Button
              size="sm"
              variant="secondary"
              onClick={handleRoleChange}
              disabled={savingRole || role === user.role}
            >
              {savingRole ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <ShieldCheck className="h-3.5 w-3.5" />}
              {t.users_change_role_btn}
            </Button>
          </div>

          <div className="flex items-end gap-2">
            <div className="flex-1 space-y-1.5">
              <Label className="text-xs">{t.users_new_password_label}</Label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder={t.users_reset_pw_hint}
              />
            </div>
            <Button size="sm" variant="secondary" onClick={handleResetPassword} disabled={savingPw || !newPassword}>
              {savingPw ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <KeyRound className="h-3.5 w-3.5" />}
              {t.users_reset_pw_btn}
            </Button>
          </div>
        </div>

        {(roleOk || pwOk) && (
          <div className="text-xs text-success mt-2">
            {roleOk ? t.users_role_updated : t.users_reset_pw_ok}
          </div>
        )}
        {rowError && <div className="text-xs text-danger mt-2">{rowError}</div>}

        {!isSelf && (
          <div className="mt-3 pt-3 border-t border-border-subtle flex items-center gap-2">
            {confirmDelete ? (
              <>
                <span className="text-xs text-danger">{t.users_delete_confirm}</span>
                <Button size="sm" variant="destructive" onClick={handleDelete} disabled={deleting}>
                  {deleting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : t.users_delete_ok}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setConfirmDelete(false)}>
                  {t.archive_cancel}
                </Button>
              </>
            ) : (
              <Button size="sm" variant="ghost" onClick={() => setConfirmDelete(true)}>
                <Trash2 className="h-3.5 w-3.5" /> {t.users_delete_btn}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
