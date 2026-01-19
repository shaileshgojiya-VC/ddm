import PageHeading from "@/components/core/page-heading";
import CommonTabs, { type TabItem } from "@/components/core/common-tabs";
import BitrixCRMTab from "@/components/core/settings/bitrix-crm-tab";
import OneDriveTab from "@/components/core/settings/onedrive-tab";
import InquiryConnectorTab from "@/components/core/settings/inquiry-connector-tab";
import SupplierConnectorTab from "@/components/core/settings/supplier-connector-tab";

export default async function SettingsPage() {
  const tabs: TabItem[] = [
    {
      value: "bitrix-crm",
      label: "Bitrix CRM",
      content: <BitrixCRMTab />,
    },
    {
      value: "onedrive",
      label: "OneDrive",
      content: <OneDriveTab />,
    },
    {
      value: "inquiry-connector",
      label: "Inquiry Connector",
      content: <InquiryConnectorTab />,
    },
    {
      value: "supplier-connector",
      label: "Supplier Connector",
      content: <SupplierConnectorTab />,
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeading
        title="System Settings"
        description="Configure integrations and system connections"
      />
      <CommonTabs tabs={tabs} defaultValue="bitrix-crm" />
    </div>
  );
}
