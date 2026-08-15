// Central API Client for NxtMov

export const getApiBase = () => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;

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
 * Normalizes any error object, array, or string into a clean, human-readable string.
 * Prevents generic '[object Object]' error toasts.
 */
export function normalizeErrorMessage(err) {
  if (!err) return "An unexpected error occurred.";
  
  if (typeof err === "string") {
    if (err === "[object Object]") return "An unexpected server error occurred.";
    return err;
  }
  
  if (err instanceof Error) {
    if (err.message && typeof err.message === "string" && err.message !== "[object Object]") {
      return err.message;
    }
  }

  // Handle FastAPI validation error array: [{ loc: [...], msg: "..." }, ...]
  if (Array.isArray(err)) {
    const msgs = err.map(e => {
      if (typeof e === "string") return e;
      if (e && typeof e === "object") {
        const locStr = Array.isArray(e.loc) ? e.loc.filter(l => l !== "body").join(" -> ") : "";
        const msg = e.msg || e.message || (typeof e === "object" ? JSON.stringify(e) : String(e));
        return locStr ? `${locStr}: ${msg}` : msg;
      }
      return String(e);
    }).filter(m => m && m !== "[object Object]");
    if (msgs.length > 0) return msgs.join("; ");
  }

  // Handle FastAPI error objects: { message: "...", detail: "..." }
  if (typeof err === "object") {
    if (err.detail) {
      const detailMsg = normalizeErrorMessage(err.detail);
      if (detailMsg && detailMsg !== "[object Object]") return detailMsg;
    }
    if (err.message && typeof err.message === "string" && err.message !== "[object Object]") {
      return err.message;
    }
    if (err.msg && typeof err.msg === "string" && err.msg !== "[object Object]") {
      return err.msg;
    }
    if (err.error) {
      const errRes = normalizeErrorMessage(err.error);
      if (errRes && errRes !== "[object Object]") return errRes;
    }
    
    try {
      const json = JSON.stringify(err);
      if (json && json !== "{}" && json !== "null") return json;
    } catch {
      // ignore
    }
  }

  const str = String(err);
  return str !== "[object Object]" ? str : "An unexpected error occurred. Please try again.";
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
