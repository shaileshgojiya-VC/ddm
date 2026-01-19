import PageHeading from "@/components/core/page-heading";
import CommonTabs, { type TabItem } from "@/components/core/common-tabs";
import ProfileTab from "@/components/core/profile/tabs/profile-tab";
import SecurityTab from "@/components/core/profile/tabs/security-tab";
import IntegrationsTab from "@/components/core/profile/tabs/integrations-tab";

export default function ProfilePage() {
  const tabs: TabItem[] = [
    {
      value: "profile",
      label: "Profile",
      content: <ProfileTab />,
    },
    {
      value: "security",
      label: "Security",
      content: <SecurityTab />,
    },
    {
      value: "integrations",
      label: "Integrations",
      content: <IntegrationsTab />,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeading
        title="Settings"
        description="Manage your profile and account settings"
      />
      <CommonTabs tabs={tabs} defaultValue="profile" className="max-w-4xl" />
    </div>
  );
}
