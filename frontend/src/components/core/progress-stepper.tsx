"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import { StageTimeline } from "@/types/inquiry";

export interface StepperProps {
  readonly steps: StageTimeline[];
  readonly activeStep: number;
  readonly onStepChange?: (step: number) => void;
}

export function Stepper({ steps, activeStep, onStepChange }: StepperProps) {
  return (
    <div className="flex items-center relative w-full py-2 overflow-hidden overflow-x-auto">
      {steps?.map((step, index) => {
        const stepNumber = index + 1;
        // Use step status if available, otherwise fall back to position-based logic
        const isCompleted =
          step?.stage_status === "completed" || stepNumber < activeStep;
        const isActive =
          step.stage_status === "active" || stepNumber === activeStep;
        const isUpcoming =
          step?.stage_status === "pending" ||
          step?.stage_status === "upcoming" ||
          stepNumber > activeStep;

        return (
          <button
            key={`${step?.stage_name}-${index}`}
            className="flex flex-col items-center relative flex-1 group cursor-pointer"
            onClick={() => onStepChange?.(stepNumber)}
            disabled
          >
            <div className={cn("absolute top-3 left-0 right-0 h-0.5 bg-muted")}>
              <div
                className={cn(
                  "h-full bg-primary",
                  isCompleted && "w-full",
                  isActive && "w-1/2",
                  isUpcoming && "w-0"
                )}
              />
            </div>
            {/* Step Circle */}
            <div
              className={cn(
                "relative size-6 rounded-full flex items-center justify-center transition-all duration-300 font-medium text-sm z-10",
                "cursor-pointer",
                isCompleted &&
                  "bg-primary text-primary-foreground group-hover:scale-110 shadow-md",
                isActive &&
                  "bg-primary text-primary-foreground shadow-lg ring-2 ring-primary/30 ring-offset-2 ring-offset-background scale-110",
                isUpcoming &&
                  "bg-background text-muted-foreground group-hover:ring-2 group-hover:ring-primary border border-border"
              )}
            >
              {isCompleted ? (
                <Check className="size-4" />
              ) : (
                <span className="text-xs">{stepNumber}</span>
              )}
            </div>

            {/* Step Label */}

            <div
              className={cn(
                "text-xs font-medium transition-colors duration-300 line-clamp-2 mt-2 text-center w-full px-2 truncate",
                isActive
                  ? "text-foreground font-semibold"
                  : "text-muted-foreground"
              )}
            >
              {step?.stage_name}
            </div>
          </button>
        );
      })}
    </div>
  );
}
