import LoginForm from "@/components/core/auth/login-form";
import LogoutCard from "@/components/core/logout-card";
import { auth } from "@/utils/auth";

export default async function LoginPage() {
  const session = await auth();
  const isLoggedIn = session?.accessToken;

  return isLoggedIn ? <LogoutCard /> : <LoginForm />;
}
