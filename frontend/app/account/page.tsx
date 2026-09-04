import Header from "@/components/Header";
import AccountPanel from "@/components/AccountPanel";

export default function AccountPage() {
  return (
    <>
      <Header />
      <main className="account-page page-shell">
        <AccountPanel />
      </main>
    </>
  );
}
