export type Role = 'admin' | 'analyst' | 'viewer';

export interface User {
  id: string;
  email: string;
  role: Role;
  is_active: boolean;
}
