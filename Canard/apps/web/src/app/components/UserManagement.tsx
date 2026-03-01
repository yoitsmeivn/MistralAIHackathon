import { useEffect, useState } from "react";
import { UserPlus, ShieldCheck, ArrowRightLeft } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { useAuth } from "../contexts/AuthContext";
import {
  getOrgUsers,
  createOrgUser,
  transferAdmin,
  type OrgUser,
} from "../services/api";

export function UserManagement() {
  const { appUser } = useAuth();
  const [users, setUsers] = useState<OrgUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Add-user dialog state
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newName, setNewName] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [addError, setAddError] = useState("");
  const [addSubmitting, setAddSubmitting] = useState(false);

  // Transfer confirm state
  const [transferTarget, setTransferTarget] = useState<OrgUser | null>(null);
  const [transferSubmitting, setTransferSubmitting] = useState(false);

  const isAdmin = appUser?.role === "admin";

  async function loadUsers() {
    try {
      const data = await getOrgUsers();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  async function handleAddUser(e: React.FormEvent) {
    e.preventDefault();
    setAddError("");
    setAddSubmitting(true);
    try {
      await createOrgUser({
        email: newEmail,
        password: newPassword,
        full_name: newName,
      });
      setShowAddDialog(false);
      setNewEmail("");
      setNewName("");
      setNewPassword("");
      await loadUsers();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setAddSubmitting(false);
    }
  }

  async function handleTransfer() {
    if (!transferTarget) return;
    setTransferSubmitting(true);
    try {
      await transferAdmin(transferTarget.id);
      setTransferTarget(null);
      await loadUsers();
      // Reload page so AuthContext picks up the new role
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transfer failed");
    } finally {
      setTransferSubmitting(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        You do not have permission to view this page.
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Team Members</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage users in your organization
          </p>
        </div>
        <Button
          onClick={() => setShowAddDialog(true)}
          className="bg-[#252a39] text-white hover:bg-[#252a39]/90"
        >
          <UserPlus className="size-4 mr-2" />
          Add Manager
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* User table */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#252a39]" />
        </div>
      ) : (
        <div className="rounded-xl border bg-white shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/30">
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Name</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Email</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Role</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Status</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b last:border-b-0 hover:bg-muted/10">
                  <td className="px-4 py-3 font-medium">{u.full_name}</td>
                  <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                        u.role === "admin"
                          ? "bg-[#fdfbe1] text-[#252a39]"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {u.role === "admin" && <ShieldCheck className="size-3" />}
                      {u.role}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block size-2 rounded-full mr-1.5 ${
                        u.is_active ? "bg-green-500" : "bg-gray-300"
                      }`}
                    />
                    {u.is_active ? "Active" : "Inactive"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {u.role === "manager" && u.is_active && u.id !== appUser?.id && (
                      <button
                        onClick={() => setTransferTarget(u)}
                        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                      >
                        <ArrowRightLeft className="size-3" />
                        Make Admin
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    No users found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Add user dialog */}
      {showAddDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl border p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-semibold mb-4">Add Manager</h2>

            {addError && (
              <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {addError}
              </div>
            )}

            <form onSubmit={handleAddUser} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="add-name">Full Name *</Label>
                <Input
                  id="add-name"
                  placeholder="Jane Doe"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add-email">Email *</Label>
                <Input
                  id="add-email"
                  type="email"
                  placeholder="jane@acme.com"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add-password">Password *</Label>
                <Input
                  id="add-password"
                  type="password"
                  placeholder="Minimum 6 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={6}
                />
              </div>
              <div className="flex gap-3 justify-end pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowAddDialog(false);
                    setAddError("");
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={addSubmitting}
                  className="bg-[#252a39] text-white hover:bg-[#252a39]/90"
                >
                  {addSubmitting ? "Creating..." : "Create Manager"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Transfer admin confirmation dialog */}
      {transferTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl border p-6 w-full max-w-md mx-4">
            <h2 className="text-lg font-semibold mb-2">Transfer Admin Role</h2>
            <p className="text-sm text-muted-foreground mb-4">
              This will make <strong>{transferTarget.full_name}</strong> the admin and
              demote you to manager. This action cannot be undone by you.
            </p>
            <div className="flex gap-3 justify-end">
              <Button
                variant="outline"
                onClick={() => setTransferTarget(null)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleTransfer}
                disabled={transferSubmitting}
                className="bg-red-600 text-white hover:bg-red-700"
              >
                {transferSubmitting ? "Transferring..." : "Transfer Admin"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
