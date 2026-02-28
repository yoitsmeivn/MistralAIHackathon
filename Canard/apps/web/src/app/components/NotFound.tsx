import { Link } from "react-router";
import { AlertCircle } from "lucide-react";

export function NotFound() {
  return (
    <div className="flex items-center justify-center h-full p-8">
      <div className="text-center">
        <AlertCircle
          className="w-12 h-12 mx-auto mb-4"
          style={{ color: "#252a39", opacity: 0.3 }}
        />
        <h1
          className="text-2xl mb-2"
          style={{ color: "#252a39" }}
        >
          Page Not Found
        </h1>
        <p
          className="text-sm mb-6"
          style={{ color: "#717182" }}
        >
          The page you're looking for doesn't exist.
        </p>
        <Link
          to="/"
          className="inline-block px-5 py-2 rounded-lg text-sm transition-opacity hover:opacity-90"
          style={{
            backgroundColor: "#252a39",
            color: "#ffffff",
          }}
        >
          Go to Dashboard
        </Link>
      </div>
    </div>
  );
}