// Central API Client for NxtMov

export const getApiBase = () => {
  const port = window.location.port;
  if (port && port !== "8000") {
    const host = window.location.hostname || "127.0.0.1";
    return `http://${host}:8000/api/v1`;
  }
  return "/api/v1";
};

export const API_BASE = getApiBase();

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

    try {
      const response = await fetch(url, config);
      if (response.status === 401) {
        this.clearToken();
        if (window.location.hash !== "#/login") {
          window.location.hash = "#/login";
        }
        throw new Error("Your session has expired. Please log in again.");
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
          errorMsg = "Your session has expired. Please log in again.";
        } else if (response.status === 403) {
          errorMsg = "You do not have permission to perform this action.";
        } else if (response.status === 413) {
          errorMsg = "Resume file is too large.";
        } else if (response.status === 415) {
          errorMsg = "Unsupported resume format. Upload PDF, DOCX, or TXT.";
        } else if (response.status === 500 && (!data || !data.detail)) {
          errorMsg = "Resume analysis failed on the server. Check the backend logs.";
        }
        throw new Error(errorMsg || `HTTP ${response.status}: Request failed.`);
      }
      return data;
    } catch (error) {
      console.error(`API Error [${options.method || 'GET'} ${endpoint}]:`, error);
      if (error instanceof TypeError && (error.message.includes("fetch") || error.message.includes("NetworkError") || error.message.includes("Failed to fetch"))) {
        throw new Error("Unable to connect to NxtMov server. Please ensure the backend is running at http://127.0.0.1:8000.");
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
