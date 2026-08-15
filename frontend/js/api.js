// Central API Client for NxtMov

export const getApiBase = () => {
    try {
        const customBase = localStorage.getItem("nxtmov_api_base") || (typeof window !== "undefined" && window.NXTMOV_API_BASE);
        if (customBase) return customBase.replace(/\/+$/, "");
    } catch {
        // Safe fallback if localStorage is blocked
    }

    const hostname = typeof window !== "undefined" ? window.location.hostname : "";
    const protocol = typeof window !== "undefined" ? window.location.protocol : "http:";

    // Production: GitHub Pages
    if (hostname === "vinaynalavade.github.io") {
        return "https://nxtmov-api.onrender.com/api/v1";
    }

    // Local development
    if (
        hostname === "localhost" ||
        hostname === "127.0.0.1"
    ) {
        return `${protocol}//${hostname}:8000/api/v1`;
    }

    // Fallback
    return "https://nxtmov-api.onrender.com/api/v1";
};

export const API_BASE = getApiBase();

/**
 * Resolves a backend-relative path to a complete, accessible URL in both local and cloud environments.
 */
export function getBackendUrl(relativeOrAbsoluteUrl) {
    if (!relativeOrAbsoluteUrl) return "";
    if (relativeOrAbsoluteUrl.startsWith("http://") || relativeOrAbsoluteUrl.startsWith("https://")) {
        return relativeOrAbsoluteUrl;
    }
    const base = getApiBase();
    const root = base.replace(/\/api\/v1\/?$/, "");
    if (relativeOrAbsoluteUrl.startsWith("/api/v1")) {
        return `${root}${relativeOrAbsoluteUrl}`;
    }
    if (relativeOrAbsoluteUrl.startsWith("/")) {
        return `${root}${relativeOrAbsoluteUrl}`;
    }
    return `${base}/${relativeOrAbsoluteUrl}`;
}

/**
 * Resolves an authenticated file URL with embedded token query parameter for direct browser tab display.
 */
export function getAuthenticatedFileUrl(relativeOrAbsoluteUrl) {
    const fullUrl = getBackendUrl(relativeOrAbsoluteUrl);
    const token = API.getToken();
    if (!token) return fullUrl;
    const separator = fullUrl.includes("?") ? "&" : "?";
    return `${fullUrl}${separator}token=${encodeURIComponent(token)}`;
}

/**
 * Normalizes any error object, array, string, or boolean into a clean, human-readable string.
 * Prevents 'true', 'false', '[object Object]', or raw HTML error toasts.
 */
export function normalizeErrorMessage(err, defaultFallback = "An unexpected error occurred. Please try again.") {
  if (err === null || err === undefined || err === "" || typeof err === "boolean") {
    return defaultFallback;
  }

  if (typeof err === "string") {
    const trimmed = err.trim();
    if (trimmed === "true" || trimmed === "false" || trimmed === "undefined" || trimmed === "null" || trimmed === "[object Object]" || trimmed === "{}") {
      return defaultFallback;
    }
    if (trimmed.startsWith("<!DOCTYPE html") || trimmed.startsWith("<html")) {
      return "Server returned an unexpected response. Please try again.";
    }
    return trimmed;
  }

  if (err instanceof Error) {
    if (err.message) {
      return normalizeErrorMessage(err.message, defaultFallback);
    }
  }

  // Handle FastAPI validation error array: [{ loc: [...], msg: "..." }, ...]
  if (Array.isArray(err)) {
    const msgs = err.map(e => {
      if (typeof e === "string") return normalizeErrorMessage(e, "");
      if (e && typeof e === "object") {
        const locStr = Array.isArray(e.loc) ? e.loc.filter(l => l !== "body").join(" -> ") : "";
        const msg = normalizeErrorMessage(e.msg || e.message || e.detail, "");
        return locStr && msg ? `${locStr}: ${msg}` : msg;
      }
      return "";
    }).filter(m => m && m !== defaultFallback);
    if (msgs.length > 0) return msgs.join("; ");
  }

  // Handle FastAPI error objects: { detail: "...", message: "...", error: "..." }
  if (typeof err === "object") {
    if (err.detail !== undefined) {
      return normalizeErrorMessage(err.detail, defaultFallback);
    }
    if (err.message !== undefined) {
      return normalizeErrorMessage(err.message, defaultFallback);
    }
    if (err.msg !== undefined) {
      return normalizeErrorMessage(err.msg, defaultFallback);
    }
    if (err.error !== undefined) {
      return normalizeErrorMessage(err.error, defaultFallback);
    }

    try {
      const json = JSON.stringify(err);
      if (json && json !== "{}" && json !== "null" && !json.startsWith("[")) {
        return json;
      }
    } catch {
      // ignore
    }
  }

  return defaultFallback;
}

export class API {
  static getToken() {
    return localStorage.getItem("nxtmov_token") || "";
  }

  static setToken(token) {
    localStorage.setItem("nxtmov_token", token);
  }

  static clearToken() {
    localStorage.removeItem("nxtmov_token");
    localStorage.removeItem("nxtmov_user");
    localStorage.removeItem("nxtmov_active_org");
  }

  static getHeaders(isJson = true) {
    const headers = {};
    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    if (isJson) {
      headers["Content-Type"] = "application/json";
    }
    return headers;
  }

  static async request(endpoint, options = {}) {
    const baseUrl = getApiBase();
    const url = `${baseUrl}${endpoint}`;
    const headers = { ...this.getHeaders(options.isJson !== false), ...options.headers };
    
    const config = {
      method: options.method || "GET",
      headers,
    };

    if (options.body) {
      if (options.isJson !== false) {
        config.body = JSON.stringify(options.body);
      } else {
        config.body = options.body;
      }
    }

    const isLoginEndpoint = endpoint === "/auth/login";
    const isRegisterEndpoint = endpoint === "/auth/register";
    const isPublicAuthEndpoint = endpoint.startsWith("/auth/config") || isLoginEndpoint || isRegisterEndpoint;

    try {
      const response = await fetch(url, config);

      // Handle 401 for authenticated session expiration on PROTECTED endpoints only
      if (response.status === 401 && !isPublicAuthEndpoint) {
        const hadToken = Boolean(this.getToken());
        this.clearToken();
        if (window.location.hash !== "#/login") {
          window.location.hash = "#/login";
        }
        if (hadToken) {
          throw new Error("Your session has expired. Please log in again.");
        }
      }
      
      if (response.status === 204) {
        return null;
      }

      let data;
      try {
        data = await response.json();
      } catch (jsonErr) {
        data = { detail: `Server error (${response.status} ${response.statusText})` };
      }

      if (!response.ok) {
        let errorMsg = normalizeErrorMessage(data?.detail || data);

        if (response.status === 401) {
          if (isLoginEndpoint) {
            const rawDetail = (typeof data?.detail === "string" ? data.detail : errorMsg).toLowerCase();
            if (rawDetail.includes("password")) {
              errorMsg = "Incorrect password. Please try again.";
            } else if (rawDetail.includes("no account") || rawDetail.includes("not found") || rawDetail.includes("user")) {
              errorMsg = "No account found with this email address.";
            } else {
              errorMsg = "Incorrect password. Please try again.";
            }
          } else {
            errorMsg = "Your session has expired. Please log in again.";
          }
        } else if (response.status === 429) {
          if (isLoginEndpoint) {
            errorMsg = "Too many login attempts. Please wait a moment and try again.";
          } else if (isRegisterEndpoint) {
            errorMsg = "Too many signup attempts. Please wait a moment and try again.";
          } else {
            errorMsg = "Too many requests. Please wait a moment and try again.";
          }
        } else if (response.status === 400 && isRegisterEndpoint) {
          const rawDetail = (typeof data?.detail === "string" ? data.detail : errorMsg).toLowerCase();
          if (rawDetail.includes("exists") || rawDetail.includes("already")) {
            errorMsg = "An account with this email already exists.";
          } else if (rawDetail.includes("email")) {
            errorMsg = "Please enter a valid email address.";
          } else if (rawDetail.includes("password")) {
            errorMsg = "Password does not meet the required security requirements.";
          }
        } else if (response.status >= 500) {
          if (isLoginEndpoint) {
            errorMsg = "Something went wrong while signing you in. Please try again.";
          } else if (isRegisterEndpoint) {
            errorMsg = "Something went wrong while creating your account. Please try again.";
          } else {
            errorMsg = "Something went wrong on the server. Please try again.";
          }
        }

        throw new Error(errorMsg || `HTTP ${response.status}: Request failed.`);
      }
      return data;
    } catch (error) {
      if (error instanceof TypeError && (error.message.includes("fetch") || error.message.includes("NetworkError") || error.message.includes("Failed to fetch"))) {
        throw new Error("Unable to connect to NxtMov server. Please try again.");
      }
      throw error;
    }
  }

  static get(endpoint) {
    return this.request(endpoint, { method: "GET" });
  }

  static post(endpoint, body, isJson = true) {
    return this.request(endpoint, { method: "POST", body, isJson });
  }

  static put(endpoint, body) {
    return this.request(endpoint, { method: "PUT", body });
  }

  static patch(endpoint, body) {
    return this.request(endpoint, { method: "PATCH", body });
  }

  static delete(endpoint) {
    return this.request(endpoint, { method: "DELETE" });
  }
}

export const api = API;
export default API;
