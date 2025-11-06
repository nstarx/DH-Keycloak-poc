export interface AuthClient {
  init(): Promise<boolean>; // returns authenticated?
  login(): Promise<void>;
  logout(): Promise<void>;
  getAccessToken(): Promise<string | null>;
  getUser(): Promise<{ preferred_username?: string; email?: string } | null>;
}
