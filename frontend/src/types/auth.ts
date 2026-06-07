export interface UserProfile {
  id: string;
  email: string;
  role: "admin" | "analyst" | "viewer";
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}