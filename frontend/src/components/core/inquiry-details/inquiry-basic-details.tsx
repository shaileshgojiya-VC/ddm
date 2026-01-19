"use client";

import SmartFilterDropdown from "@/components/core/smart-filter-dropdown";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { type FilterConfig } from "@/types/filters";
import { Inquiry } from "@/types/inquiry";
import { formatDate } from "@/utils/date-format";
import {
  Building,
  Package,
  Pencil,
  Tag,
  X,
  type LucideIcon,
} from "lucide-react";
import { useState } from "react";

const VerticalSeparator = () => {
  return (
    <Separator
      orientation="vertical"
      className="data-[orientation=vertical]:h-4 bg-foreground/30"
    />
  );
};

interface InquiryEditableFieldProps {
  icon: LucideIcon;
  value: string;
  isEditing: boolean;
  config: FilterConfig;
  onEdit: () => void;
  onCancel: () => void;
  onChange: (filterType: string, value: string) => void;
  getLabel: (value: string) => string;
}

const InquiryEditableField = ({
  icon: Icon,
  value,
  isEditing,
  config,
  onEdit,
  onCancel,
  onChange,
  getLabel,
}: InquiryEditableFieldProps) => {
  return (
    <div className="flex items-center gap-2">
      <Icon className="size-4 text-muted-foreground" />
      {isEditing ? (
        <div className="flex items-center gap-2">
          <SmartFilterDropdown
            config={config}
            currentValue={value}
            onFilterChange={onChange}
          />
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0 size-8"
            onClick={onCancel}
          >
            <X className="size-4" />
          </Button>
        </div>
      ) : (
        <div className="flex items-center justify-between gap-2">
          <span className="font-medium">{getLabel(value)}</span>
          <Button
            variant="ghost"
            size="icon"
            className="size-8"
            onClick={onEdit}
          >
            <Pencil className="size-4" />
          </Button>
        </div>
      )}
    </div>
  );
};

interface ReadOnlyFieldProps {
  label: string;
  value: string;
  icon?: LucideIcon;
}

const ReadOnlyField = ({ label, value, icon: Icon }: ReadOnlyFieldProps) => {
  return (
    <div className="flex items-center gap-1">
      {Icon && <Icon className="size-4 text-muted-foreground" />}
      <span className="text-muted-foreground">{label}:</span>
      <span>{value}</span>
    </div>
  );
};

interface InquiryBasicDetailsProps {
  readonly inquiryDetails: Inquiry;
}

export default function InquiryBasicDetails({
  inquiryDetails,
}: InquiryBasicDetailsProps) {
  const {
    group_name,
    priority: InquiryPriority,
    prodcut_category,
    created_at,
    last_contact,
    company_name,
  } = inquiryDetails || {};

  const [office, setOffice] = useState(company_name || "-");
  const [group, setGroup] = useState(group_name || "-");
  const [priority, setPriority] = useState(InquiryPriority || "-");
  const [editingOffice, setEditingOffice] = useState(false);
  const [editingGroup, setEditingGroup] = useState(false);

  // Office options
  const officeConfig: FilterConfig = {
    key: "list_office",
    label: "All Offices",
    options: [
      {
        label: "All Offices",
        value: "",
      },
      {
        label: "Dana Dairy EMEA WEGWG TWH5H4 5HRJNFGN TEGRGBE ERHGSH ",
        value: "dana_dairy_emea",
      },
      { label: "Dana Dairy Europe", value: "dana_dairy_europe" },
      { label: "Dana Dairy MENA", value: "dana_dairy_mena" },
      { label: "Dana Dairy Asia", value: "dana_dairy_asia" },
      { label: "Dana Dairy Americas", value: "dana_dairy_americas" },
    ],
  };

  // Group options
  const groupConfig: FilterConfig = {
    key: "list_group",
    label: "All Groups",
    options: [
      {
        label: "All Groups",
        value: "",
      },
      { label: "A: Infant Formula", value: "infant_formula" },
      { label: "B: Consumer Dairy", value: "consumer_dairy" },
      { label: "C: Food Service", value: "food_service" },
      { label: "D: Dairy Ingredients", value: "dairy_ingredients" },
      { label: "E: Infant Formula 25KG", value: "infant_formula_25kg" },
      { label: "F: Baby Food PL", value: "baby_food_pl" },
      { label: "G: Infant Formula DXB/KR", value: "infant_formula_dxb_kr" },
      { label: "H: Baby Cereal 25KG", value: "baby_cereal_25kg" },
      { label: "I: Dairy PL", value: "dairy_pl" },
    ],
  };

  // Priority options
  const priorityOptions = [
    { value: "urgent", label: "Urgent" },
    { value: "high", label: "High" },
    { value: "medium", label: "Medium" },
    { value: "low", label: "Low" },
  ];

  const getOfficeLabel = (value: string) => {
    return (
      officeConfig?.options?.find((opt) => opt?.value === value)?.label ||
      value ||
      "-"
    );
  };

  const getGroupLabel = (value: string) => {
    const label =
      groupConfig?.options?.find((opt) => opt?.value === value)?.label || value;
    // Extract the short form (e.g., "Group B: Consumer Dairy")
    const match = label.match(/^([A-Z]):\s*(.+)$/);
    return match ? `Group ${match[1]}: ${match[2]}` : label || "-";
  };

  const getPriorityLabel = (value: string) => {
    return priorityOptions.find((opt) => opt?.value === value)?.label || "High";
  };

  const handleOfficeChange = (filterType: string, value: string) => {
    setOffice(value);
    setEditingOffice(false);
    // TODO: Handle API update
    // console.log("Office updated:", value);
  };

  const handleGroupChange = (filterType: string, value: string) => {
    setGroup(value);
    setEditingGroup(false);
    // TODO: Handle API update
    // console.log("Group updated:", value);
  };

  const handlePriorityChange = (value: string) => {
    setPriority(value);
    // TODO: Handle API update
    // console.log("Priority updated:", value);
  };

  return (
    <div className="flex flex-wrap items-center gap-3 px-3 py-2 bg-muted/30 rounded-lg text-sm">
      <InquiryEditableField
        icon={Building}
        value={office}
        isEditing={editingOffice}
        config={officeConfig}
        onEdit={() => setEditingOffice(true)}
        onCancel={() => setEditingOffice(false)}
        onChange={handleOfficeChange}
        getLabel={getOfficeLabel}
      />
      <VerticalSeparator />
      <InquiryEditableField
        icon={Tag}
        value={group}
        isEditing={editingGroup}
        config={groupConfig}
        onEdit={() => setEditingGroup(true)}
        onCancel={() => setEditingGroup(false)}
        onChange={handleGroupChange}
        getLabel={getGroupLabel}
      />
      <VerticalSeparator />
      <ReadOnlyField
        label="Category"
        value={prodcut_category || "-"}
        icon={Package}
      />
      <VerticalSeparator />
      <ReadOnlyField
        label="Created"
        value={created_at ? formatDate(created_at) : "-"}
      />
      <VerticalSeparator />
      <ReadOnlyField
        label="Last Contact"
        value={last_contact ? formatDate(last_contact) : "-"}
      />
      <VerticalSeparator />
      <div className="flex items-center gap-1">
        <span className="text-muted-foreground">Priority:</span>
        <Select value={priority} onValueChange={handlePriorityChange} disabled>
          <SelectTrigger
            className="w-full border-none outline-none bg-transparent shadow-none"
            size="sm"
          >
            <SelectValue>{getPriorityLabel(priority)}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {priorityOptions.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
