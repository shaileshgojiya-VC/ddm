import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface StageBadgeProps {
  readonly stage: string;
  readonly className?: string;
}
export default function StageBadge({ stage, className }: StageBadgeProps) {
  const styles = {
    "New Inquiry New Unclear":
      "bg-blue-700/10 text-blue-700 hover:bg-blue-700/10",
    "New Inquiry New Clear":
      "bg-blue-700/10 text-blue-700 hover:bg-blue-700/10",
    "Form Filled Out": "bg-blue-700/10 text-blue-700 hover:bg-blue-700/10",
    Meeting: "bg-purple-700/10 text-purple-700 hover:bg-purple-700/10",
    "Meeting Report": "bg-purple-700/10 text-purple-700 hover:bg-purple-700/10",
    "Assessment by DANA Lost": "bg-red-700/10 text-red-700 hover:bg-red-700/10",
    "Price Offer Reject": "bg-red-700/10 text-red-700 hover:bg-red-700/10",
    "Assessment by DANA- Won":
      "bg-emerald-700/10 text-emerald-700 hover:bg-emerald-700/10",
    "Price Offer Accept":
      "bg-emerald-700/10 text-emerald-700 hover:bg-emerald-700/10",
    "On Hold": "bg-gray-700/10 text-gray-700 hover:bg-gray-700/10",
    "Product of Interest": "bg-cyan-700/10 text-cyan-700 hover:bg-cyan-700/10",
    Sample: "bg-cyan-700/10 text-cyan-700 hover:bg-cyan-700/10",
    "Identify exact product":
      "bg-cyan-700/10 text-cyan-700 hover:bg-cyan-700/10",
    "Sourcing & Pricing":
      "bg-amber-700/10 text-amber-700 hover:bg-amber-700/10",
    "Proposal & Quotation":
      "bg-indigo-700/10 text-indigo-700 hover:bg-indigo-700/10",
    "Customer Review & Feedback":
      "bg-indigo-700/10 text-indigo-700 hover:bg-indigo-700/10",
    Negotiation: "bg-orange-700/10 text-orange-700 hover:bg-orange-700/10",
    "Join with buyer team":
      "bg-violet-700/10 text-violet-700 hover:bg-violet-700/10",
    "Obtain list of documents":
      "bg-violet-700/10 text-violet-700 hover:bg-violet-700/10",
    "Art work preparation":
      "bg-violet-700/10 text-violet-700 hover:bg-violet-700/10",
    "Docs Preparation":
      "bg-violet-700/10 text-violet-700 hover:bg-violet-700/10",
    "Docs Submitted": "bg-violet-700/10 text-violet-700 hover:bg-violet-700/10",
    "Dispatch approved documents":
      "bg-violet-700/10 text-violet-700 hover:bg-violet-700/10",
    "Register approval": "bg-teal-700/10 text-teal-700 hover:bg-teal-700/10",
    "Go To Registration": "bg-teal-700/10 text-teal-700 hover:bg-teal-700/10",
    "Agreement-Go-To-Registration":
      "bg-green-700/10 text-green-700 hover:bg-green-700/10",
    "Agreement-Order-Placement":
      "bg-green-700/10 text-green-700 hover:bg-green-700/10",
    "Move to Deal":
      "bg-emerald-600/10 text-emerald-600 hover:bg-emerald-600/10",
    "Order Placement":
      "bg-emerald-600/10 text-emerald-600 hover:bg-emerald-600/10",
    Proforma: "bg-emerald-600/10 text-emerald-600 hover:bg-emerald-600/10",
    "Execution plan": "bg-pink-700/10 text-pink-700 hover:bg-pink-700/10",
    "Go To Operation": "bg-pink-700/10 text-pink-700 hover:bg-pink-700/10",
  };

  return (
    <Badge
      className={cn(
        "font-normal capitalize",
        styles[stage as keyof typeof styles] ||
          "bg-blue-700/10 text-blue-700 hover:bg-blue-700/10",
        className
      )}
    >
      {stage || "-"}
    </Badge>
  );
}
