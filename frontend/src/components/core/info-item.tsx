import { Badge } from "@/components/ui/badge";
import { EditableField } from "@/components/core/editable-field";
import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

type InfoItemProps = {
  readonly label: string;
  readonly name?: string;
  readonly editable?: boolean;
  readonly icon?: LucideIcon;
  readonly className?: string;
  readonly value?: string | string[] | number | React.ReactNode;
};

export function InfoItem({
  label,
  name,
  editable,
  icon: Icon,
  className,
  value,
}: InfoItemProps) {
  const isArray = Array.isArray(value);
  return (
    <div className={cn("flex items-start gap-3", className)}>
      {Icon && (
        <Icon className="size-4 text-muted-foreground shrink-0 mt-0.5" />
      )}
      <div className="space-y-1 min-w-0 flex-1">
        <label className="text-xs text-muted-foreground">{label}</label>

        <div className="flex-1">
          {editable ? (
            <EditableField name={name || "-"} />
          ) : (
            <>
              {isArray ? (
                <div className="flex flex-wrap gap-2">
                  {value?.map((item) => (
                    <Badge key={item} variant="secondary">
                      {item || "-"}
                    </Badge>
                  ))}
                </div>
              ) : (
                <div className="text-sm font-medium text-foreground wrap-break-word">
                  {value || "-"}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
