"use client";

import { Stepper } from "@/components/core/progress-stepper";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Inquiry } from "@/types/inquiry";
import { AlertCircle } from "lucide-react";
import { useMemo, useState } from "react";
import NoDataFound from "@/components/core/no-data-found";

interface InquiryProgressProps {
  readonly inquiryDetails: Inquiry;
}

export default function InquiryProgress({
  inquiryDetails,
}: InquiryProgressProps) {
  const { stage_timeline, phase } = inquiryDetails || {};

  // Find the active stage
  const activeStageIndex = useMemo(() => {
    const activeIndex = stage_timeline?.findIndex(
      (stage) => stage.stage_status === "active"
    );
    return activeIndex !== undefined && activeIndex !== -1
      ? activeIndex + 1
      : 1;
  }, [stage_timeline]);

  const [activeStep, setActiveStep] = useState(activeStageIndex);

  // Get current stage details
  const currentStage = useMemo(() => {
    return stage_timeline?.find((stage) => stage.stage_number === activeStep);
  }, [stage_timeline, activeStep]);

  const [status, setStatus] = useState(currentStage?.stage_status || "");

  const totalSteps = stage_timeline?.length ?? 0;

  const statusOptions = [
    { value: "completed", label: "Completed" },
    { value: "active", label: "Active" },
    { value: "pending", label: "Pending" },
    { value: "on_hold", label: "On Hold" },
    { value: "delayed", label: "Delayed" },
  ];

  const needsAction =
    status === "pending" || status === "delayed" || status === "on_hold";

  const handleStepChange = (step: number) => {
    setActiveStep(step);
    const selectedStage = stage_timeline?.find(
      (stage) => stage.stage_number === step
    );
    if (selectedStage) {
      setStatus(selectedStage.stage_status);
    }
  };

  return (
    <Card className="bg-muted/30 w-full">
      <CardContent className="">
        <div className="space-y-2">
          {/* Header */}
          <div className="flex items-center gap-4 w-full">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
              PROGRESS
            </h3>
            <div className="flex-1 h-px bg-border" />
            {status && (
              <div className="flex items-center gap-3">
                <Select value={status} onValueChange={setStatus} disabled>
                  <SelectTrigger
                    className="w-fit bg-white rounded-2xl text-xs"
                    size="sm"
                  >
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {statusOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {needsAction && (
                  <Badge
                    variant="destructive"
                    className="gap-1.5 bg-red-50 text-red-600 hover:bg-red-50 border-red-200"
                  >
                    <AlertCircle className="size-3" />
                    Action Required
                  </Badge>
                )}
              </div>
            )}
          </div>
          {stage_timeline && stage_timeline?.length > 0 ? (
            <>
              {/* Phase and Step Info */}
              <div className="flex items-center gap-2 text-xs">
                <Badge
                  variant="secondary"
                  className="bg-primary/10 text-primary hover:bg-primary/10 font-semibold rounded "
                >
                  {phase || "-"}
                </Badge>
                <span className="text-muted-foreground">
                  Step {activeStep} of {totalSteps}
                </span>
              </div>

              <Stepper
                steps={stage_timeline}
                activeStep={activeStep}
                onStepChange={handleStepChange}
              />

              {/* Current Stage */}
              <div className="text-xs">
                <span className="text-muted-foreground">Current: </span>
                <span className="font-medium text-primary">
                  {currentStage?.stage_name || "N/A"}
                </span>
              </div>
            </>
          ) : (
            <NoDataFound
              title="No progress found"
              description="No progress found for this inquiry"
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}
