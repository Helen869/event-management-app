import { useEffect, useState } from "react";

export type Route =
  | { page: "list" }
  | { page: "new" }
  | { page: "details"; id: string }
  | { page: "edit"; id: string }
  | { page: "notFound" };

function parseRoute(hash: string): Route {
  const [root, id, action, ...rest] = hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  if (root === undefined) return { page: "list" };
  if (root !== "events" || id === undefined || rest.length > 0) return { page: "notFound" };
  if (id === "new" && action === undefined) return { page: "new" };
  if (action === undefined) return { page: "details", id };
  if (action === "edit") return { page: "edit", id };
  return { page: "notFound" };
}

export function useRoute(): Route {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return parseRoute(hash);
}

export function navigate(path: string): void {
  window.location.hash = path;
}
