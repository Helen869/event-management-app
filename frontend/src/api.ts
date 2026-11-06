// Typed client for the backend; the only module that calls fetch. Shapes mirror the OpenAPI schemas.

export interface EventResponse {
  id: string;
  title: string;
  description: string;
  starts_at: string;
  max_capacity: number;
  registered_count: number;
  remaining_seats: number;
  is_past: boolean;
  is_full: boolean;
}

export interface EventInput {
  title: string;
  description: string;
  starts_at: string;
  max_capacity: number;
}

export interface RegistrationResponse {
  email: string;
  registered_at: string;
}

export interface FieldError {
  field: string;
  message: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: FieldError[];

  constructor(status: number, code: string, message: string, details: FieldError[] = []) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function toApiError(error: unknown): ApiError {
  return error instanceof ApiError
    ? error
    : new ApiError(0, "UNEXPECTED", "Something went wrong. Please try again.");
}

async function request<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    console.error("Network failure", method, path, error);
    throw new ApiError(0, "NETWORK_ERROR", "Cannot reach the server. Check that the backend is running.");
  }
  if (response.status === 204) return undefined as T;

  const data: unknown = await response.json().catch(() => null);
  if (response.ok) return data as T;
  if (data && typeof data === "object" && "code" in data && "message" in data) {
    const error = data as { code: string; message: string; details?: FieldError[] };
    throw new ApiError(response.status, error.code, error.message, error.details);
  }
  console.error("Unexpected response", method, path, response.status);
  throw new ApiError(response.status, "UNEXPECTED", `The server returned an unexpected error (${response.status}).`);
}

const registrations = (eventId: string) => `/events/${eventId}/registrations`;

export const api = {
  listEvents: () => request<EventResponse[]>("/events"),
  getEvent: (id: string) => request<EventResponse>(`/events/${id}`),
  createEvent: (input: EventInput) => request<EventResponse>("/events", "POST", input),
  updateEvent: (id: string, input: EventInput) => request<EventResponse>(`/events/${id}`, "PUT", input),
  listRegistrations: (eventId: string) => request<RegistrationResponse[]>(registrations(eventId)),
  register: (eventId: string, email: string) =>
    request<RegistrationResponse>(registrations(eventId), "POST", { email }),
  unregister: (eventId: string, email: string) =>
    request<void>(`${registrations(eventId)}/${encodeURIComponent(email)}`, "DELETE"),
};
