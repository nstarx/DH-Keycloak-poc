import { UserManager, WebStorageStateStore } from "oidc-client-ts";
import type { AuthClient } from "./AuthClient";
import cfg from "../../config.json";

export class OidcAuth implements AuthClient {
  private um: UserManager;

  constructor() {
    this.um = new UserManager({
      authority: cfg.authority,
      client_id: cfg.clientId,
      redirect_uri: cfg.redirectUri,
      post_logout_redirect_uri: cfg.postLogoutRedirectUri,
      response_type: "code",
      scope: cfg.scope,
      loadUserInfo: true,
      userStore: new WebStorageStateStore({ store: window.sessionStorage })
    });
  }

  async init(): Promise<boolean> {
    if (window.location.pathname.includes("/callback")) {
      await this.um.signinCallback();
      window.history.replaceState({}, "", "/");
    }
    const user = await this.um.getUser();
    return !!user && !user.expired;
  }

  async login() { await this.um.signinRedirect(); }
  async logout() { await this.um.signoutRedirect(); }

  async getAccessToken() {
    let user = await this.um.getUser();
    if (!user || user.expired) {
      user = await this.um.signinSilent().catch(() => null);
    }
    return user?.access_token ?? null;
  }

  async getUser() {
    const u = await this.um.getUser();
    if (!u) return null;
    return {
      preferred_username: (u.profile as any)?.preferred_username || u.profile?.email,
      email: u.profile?.email
    };
  }
}
