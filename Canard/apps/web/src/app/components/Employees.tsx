import { useState, useEffect, useRef } from "react";
import { Link } from "react-router";
import { Plus, Search, Edit, Trash2, Upload } from "lucide-react";
import { motion } from "motion/react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "./ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import type { Employee } from "../types";
import { getEmployees, createEmployee, importEmployeesCSV } from "../services/api";

const riskBadgeStyle = (risk: string) => {
  switch (risk) {
    case "high":
      return { backgroundColor: "#fef2f2", color: "#ef4444" };
    case "medium":
      return { backgroundColor: "#fffbeb", color: "#f59e0b" };
    case "low":
      return { backgroundColor: "#f0fdf4", color: "#22c55e" };
    default:
      return { backgroundColor: "#f4f4f4", color: "#9ca3af" };
  }
};

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

const getInitials = (name: string) =>
  name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

export function Employees() {
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterDepartment, setFilterDepartment] = useState<string>("all");
  const [filterRisk, setFilterRisk] = useState<string>("all");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [creating, setCreating] = useState(false);
  const [importResult, setImportResult] = useState<{
    created: number;
    updated: number;
    errors: string[];
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    phone: "",
    department: "",
    jobTitle: "",
  });

  const loadEmployees = () => {
    setLoading(true);
    getEmployees()
      .then((data) => {
        setEmployees(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadEmployees();
  }, []);

  const handleCreateEmployee = async () => {
    setCreating(true);
    try {
      await createEmployee({
        full_name: formData.fullName,
        email: formData.email,
        phone: formData.phone,
        department: formData.department || undefined,
        job_title: formData.jobTitle || undefined,
      });
      setShowModal(false);
      setFormData({
        fullName: "",
        email: "",
        phone: "",
        department: "",
        jobTitle: "",
      });
      loadEmployees();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to create employee");
    } finally {
      setCreating(false);
    }
  };

  const handleCSVImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    // Reset input so re-selecting the same file triggers change
    e.target.value = "";

    setImporting(true);
    setImportResult(null);
    try {
      const result = await importEmployeesCSV(file);
      setImportResult(result);
      loadEmployees();
    } catch (err) {
      setImportResult({
        created: 0,
        updated: 0,
        errors: [err instanceof Error ? err.message : "Import failed"],
      });
    } finally {
      setImporting(false);
    }
  };

  const filteredEmployees = employees.filter((employee) => {
    const matchesSearch =
      employee.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      employee.department.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDepartment =
      filterDepartment === "all" || employee.department === filterDepartment;
    const matchesRisk =
      filterRisk === "all" || employee.riskLevel === filterRisk;
    return matchesSearch && matchesDepartment && matchesRisk;
  });

  const departments = Array.from(
    new Set(employees.map((e) => e.department))
  );

  return (
    <motion.div
      className="p-8 max-w-7xl"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {/* Hidden file input for CSV */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={handleCSVImport}
      />

      {/* Header */}
      <motion.div
        className="mb-8 flex items-center justify-between"
        variants={item}
      >
        <div>
          <h1 className="text-2xl font-medium mb-1 text-foreground">
            Employees
          </h1>
          <p className="text-sm text-muted-foreground">
            Manage employees for vishing security testing
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={importing}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="w-4 h-4" />
            {importing ? "Importing..." : "Import CSV"}
          </Button>
          <Button onClick={() => setShowModal(true)}>
            <Plus className="w-4 h-4" />
            Add Employee
          </Button>
        </div>
      </motion.div>

      {/* Import result banner */}
      {importResult && (
        <motion.div
          className="mb-5 rounded-lg border p-4 text-sm"
          style={{
            backgroundColor: importResult.errors.length > 0 && importResult.created === 0 && importResult.updated === 0
              ? "#fef2f2"
              : "#f0fdf4",
            borderColor: importResult.errors.length > 0 && importResult.created === 0 && importResult.updated === 0
              ? "#fecaca"
              : "#bbf7d0",
          }}
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex items-center justify-between">
            <div>
              {importResult.created > 0 && (
                <span className="text-green-700 mr-3">
                  {importResult.created} created
                </span>
              )}
              {importResult.updated > 0 && (
                <span className="text-blue-700 mr-3">
                  {importResult.updated} updated
                </span>
              )}
              {importResult.errors.length > 0 && (
                <span className="text-red-600">
                  {importResult.errors.length} error(s)
                </span>
              )}
            </div>
            <button
              className="text-muted-foreground hover:text-foreground text-xs"
              onClick={() => setImportResult(null)}
            >
              Dismiss
            </button>
          </div>
          {importResult.errors.length > 0 && (
            <ul className="mt-2 text-xs text-red-600 space-y-0.5">
              {importResult.errors.slice(0, 5).map((err, i) => (
                <li key={i}>{err}</li>
              ))}
              {importResult.errors.length > 5 && (
                <li>...and {importResult.errors.length - 5} more</li>
              )}
            </ul>
          )}
        </motion.div>
      )}

      {/* Filters */}
      <motion.div className="mb-5 flex gap-3 flex-wrap" variants={item}>
        <div className="flex-1 min-w-48 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search employees..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={filterDepartment} onValueChange={setFilterDepartment}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Departments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            {departments.map((dept) => (
              <SelectItem key={dept} value={dept}>
                {dept}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterRisk} onValueChange={setFilterRisk}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="All Risk" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Risk Levels</SelectItem>
            <SelectItem value="high">High Risk</SelectItem>
            <SelectItem value="medium">Medium Risk</SelectItem>
            <SelectItem value="low">Low Risk</SelectItem>
            <SelectItem value="unknown">Unknown</SelectItem>
          </SelectContent>
        </Select>
      </motion.div>

      {/* Table */}
      <motion.div variants={item}>
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="pl-6">Employee</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Tests</TableHead>
                <TableHead>Last Test</TableHead>
                <TableHead className="w-16" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEmployees.map((employee) => (
                <TableRow key={employee.id}>
                  <TableCell className="pl-6">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-xs shrink-0 font-medium"
                        style={{
                          backgroundColor: "#fdfbe1",
                          color: "#252a39",
                        }}
                      >
                        {getInitials(employee.fullName)}
                      </div>
                      <div>
                        <Link
                          to={`/employees/${employee.id}`}
                          className="text-sm font-medium text-foreground hover:underline"
                        >
                          {employee.fullName}
                        </Link>
                        <p className="text-xs text-muted-foreground">
                          {employee.jobTitle}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {employee.department}
                  </TableCell>
                  <TableCell>
                    <p className="text-xs text-muted-foreground">
                      {employee.email}
                    </p>
                    <p className="text-xs text-muted-foreground/60">
                      {employee.phone}
                    </p>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className="capitalize border-0"
                      style={riskBadgeStyle(employee.riskLevel)}
                    >
                      {employee.riskLevel}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <p className="text-sm text-foreground">
                      {employee.totalTests} total
                    </p>
                    <p className="text-xs text-red-500">
                      {employee.failedTests} failed
                    </p>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {employee.lastTestDate}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <button className="text-muted-foreground/30 hover:text-muted-foreground transition-colors">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="text-muted-foreground/30 hover:text-red-400 transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      </motion.div>

      {/* Add Employee Dialog */}
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Add Employee</DialogTitle>
            <DialogDescription>
              Add a new employee for security testing
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {[
              {
                label: "Full Name",
                field: "fullName",
                type: "text",
                placeholder: "e.g., John Smith",
              },
              {
                label: "Email",
                field: "email",
                type: "email",
                placeholder: "john.smith@company.com",
              },
              {
                label: "Phone",
                field: "phone",
                type: "tel",
                placeholder: "+1 (555) 123-4567",
              },
              {
                label: "Job Title",
                field: "jobTitle",
                type: "text",
                placeholder: "e.g., Software Engineer",
              },
            ].map(({ label, field, type, placeholder }) => (
              <div key={field}>
                <label className="block text-xs text-muted-foreground mb-1.5">
                  {label}
                </label>
                <Input
                  type={type}
                  value={formData[field as keyof typeof formData]}
                  onChange={(e) =>
                    setFormData({ ...formData, [field]: e.target.value })
                  }
                  placeholder={placeholder}
                />
              </div>
            ))}

            <div>
              <label className="block text-xs text-muted-foreground mb-1.5">
                Department
              </label>
              <Select
                value={formData.department}
                onValueChange={(val) =>
                  setFormData({ ...formData, department: val })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent>
                  {[
                    "Finance",
                    "HR",
                    "Sales",
                    "Engineering",
                    "Marketing",
                    "Operations",
                    "Legal",
                  ].map((d) => (
                    <SelectItem key={d} value={d}>
                      {d}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateEmployee}
              disabled={
                creating || !formData.fullName || !formData.email || !formData.department
              }
            >
              {creating ? "Adding..." : "Add Employee"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
