import Link from "next/link";

import { Icons } from "@/components/icons";
import { ModelSettings } from "@/components/model-settings";

export default function SettingsPage() {
  return (
    <main className="settings-page container-wide">
      <header className="settings-topbar">
        <Link href="/" className="button secondary"><Icons.ArrowLeft /> بازگشت</Link>
        <div className="brand-lockup"><div className="brand-mark"><Icons.Book /></div><div><strong>Exam Coach</strong><span>تنظیمات سراسری</span></div></div>
      </header>
      <ModelSettings />
    </main>
  );
}
