// Reactive State Store for NxtMov

class StateStore {
  constructor() {
    this.state = {
      user: JSON.parse(localStorage.getItem("nxtmov_user") || "null"),
      organizations: [],
      activeOrgId: parseInt(localStorage.getItem("nxtmov_active_org_id") || "0", 10),
      activeView: "dashboard",
    };
    this.listeners = [];
  }

  getState() {
    return this.state;
  }

  setState(newState) {
    this.state = { ...this.state, ...newState };
    if (newState.user) {
      localStorage.setItem("nxtmov_user", JSON.stringify(newState.user));
    }
    if (newState.activeOrgId) {
      localStorage.setItem("nxtmov_active_org_id", newState.activeOrgId.toString());
    }
    this.notify();
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify() {
    this.listeners.forEach(listener => listener(this.state));
  }
}

export const store = new StateStore();
