import Header from "@/components/Header";
import AuthForm from "@/components/AuthForm";

export default function LoginPage() {
  return (
    <>
      <Header />
      <main className="auth-page page-shell">
        <AuthForm mode="login" />
      </main>
    </>
  );
}
